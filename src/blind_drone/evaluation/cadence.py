"""Tick scoring and conservative paired v3 gates. Privileged evaluation only."""
from math import isclose, isfinite

from blind_drone.evaluation.episode import EpisodeEvaluator
from blind_drone.experiments.protocol_v3 import adverse_upper_bound
from blind_drone.sensors.acquisition import cpu_summary


class CadenceEvaluator(EpisodeEvaluator):
    def __init__(self, goal, quality):
        super().__init__(goal, {**quality, "timeout_s": quality["deadline_s"]})

    def update(self, time_s, position_m, velocity_m_s, contact_count):
        # Quantize only time onto the declared 16 ms clock to avoid a floating
        # subtraction turning dwell=1 s or the deadline into a later tick.
        time_s = round(time_s, 9)
        return super().update(time_s, position_m, velocity_m_s, contact_count)


def classify_attempt(result, console, timed_out=False):
    """Only recognizable loader/display errors are automatically retryable.

    Watchdog/no result without evidence stays unresolved. Controller exceptions
    and OOM reported by the controller remain algorithm failures, never infra.
    """
    if result is not None:
        return "valid" if result.get("status") == "complete" else "unresolved"
    if any(marker in console for marker in ("could not connect to display", "Could not load the Qt platform plugin",
                                            "error while loading shared libraries")):
        return "infrastructure"
    return "unresolved"


def pair_order(case_id, repeat):
    import hashlib
    if repeat not in (0, 1):
        raise ValueError("Exactly two repeats")
    parity = int(hashlib.sha256(case_id.encode()).hexdigest(), 16) % 2
    return ("reference", "candidate") if (parity + repeat) % 2 == 0 else ("candidate", "reference")


def aggregate(episodes, cases, spec):
    """No missing repeats, no success-only denominator, no pseudo-replication."""
    keys = [(e["case_id"], e["arm"], e["repeat"]) for e in episodes]
    expected = {(c["id"], a, r) for c in cases for a in ("reference", "candidate") for r in (0,1)}
    if len(set(keys)) != len(keys) or set(keys) != expected:
        raise ValueError("Incomplete/duplicate paired study; cannot conclude")
    groups = {}
    for c in cases:
        groups[c["id"]] = {}
        for arm in ("reference", "candidate"):
            rows = [e for e in episodes if e["case_id"] == c["id"] and e["arm"] == arm]
            groups[c["id"]][arm] = {
                "success": all(e["outcome"] == "success" for e in rows),
                "elapsed_s": max(e["elapsed_s"] for e in rows),
                "path_m": max(e["path_length_m"] for e in rows),
                "cpu_p95_ms": max(e["cpu"]["p95_ms"] for e in rows)}
            if any(e['outcome'] not in ('success','collision','out_of_bounds','timeout','algorithm_failure') for e in rows):
                raise ValueError('Unknown algorithm outcome')
    feasible = [c for c in cases if c["feasible"]]
    if not feasible:
        raise ValueError("Need feasible cases")
    q, b = spec["quality"], spec["budget"]
    success = {a:sum(groups[c["id"]][a]["success"] for c in feasible) for a in ("reference","candidate")}
    adverse = sum(groups[c["id"]]["reference"]["success"] and not groups[c["id"]]["candidate"]["success"] for c in feasible)
    upper = adverse_upper_bound(adverse, len(feasible), q["one_sided_alpha"])
    def ratio(candidate, reference):
        return candidate/reference if reference > 0 else (1. if candidate == 0 else None)
    def within(value, cap):
        return value is not None and isfinite(value) and value <= cap + 1e-9
    def sums(arm, field, common=False):
        total = 0.
        for c in feasible:
            pair = groups[c["id"]]
            if common and not all(row["success"] for row in pair.values()):continue
            row = pair[arm]
            if common or field == "cpu_p95_ms": total += row[field]
            elif row["success"]: total += min(row[field], q["failure_path_penalty_m"]) if field=="path_m" else row[field]
            else: total += q["failure_path_penalty_m"] if field=="path_m" else q["failure_time_penalty_s"]
        return total
    ratios = {field:ratio(sums("candidate",field),sums("reference",field)) for field in ("path_m","elapsed_s","cpu_p95_ms")}
    common_n = sum(all(row["success"] for row in groups[c["id"]].values()) for c in feasible)
    common_path = ratio(sums("candidate","path_m",True),sums("reference","path_m",True)) if common_n else None
    common_time = ratio(sums("candidate","elapsed_s",True),sums("reference","elapsed_s",True)) if common_n else None
    data_ok = True
    for c in cases:
        for r in (0,1):
            pair = {e["arm"]:e for e in episodes if e["case_id"]==c["id"] and e["repeat"]==r}
            for a,e in pair.items():
                acq=e["acquisition"]
                expected_rate=1000/spec[a+"_period_ms"]
                rate=acq["scored"]["payload_bytes_per_s"]
                data_ok &= acq["schedule_complete"] and acq["all"]["invalid_values"] == 0
                data_ok &= rate is not None and isclose(rate,96*expected_rate,rel_tol=1e-9)
            ref=pair["reference"]["acquisition"]["scored"]["payload_bytes_per_s"]
            cand=pair["candidate"]["acquisition"]["scored"]["payload_bytes_per_s"]
            data_ok &= ref is not None and cand is not None and within(ratio(cand,ref),1-q["minimum_range_rate_reduction"])
    # CPU gate includes negative cases as well as feasible cases.
    cpu_ratio=ratio(sum(groups[c["id"]]["candidate"]["cpu_p95_ms"] for c in cases),
                    sum(groups[c["id"]]["reference"]["cpu_p95_ms"] for c in cases))
    gates = {
        "success": all(n/len(feasible)>=q["minimum_success_rate"] for n in success.values()),
        "no_collision_bounds": all(e["outcome"] not in ("collision","out_of_bounds") and e.get("contact_count",0)==0 for e in episodes),
        "negative_never_success": all(e["outcome"]!="success" for e in episodes if not next(c["feasible"] for c in cases if c["id"]==e["case_id"])),
        "adverse_bound": upper <= q["maximum_adverse_pair_probability"],
        "range_reduction": bool(data_ok),
        "common_success_path": within(common_path,q["maximum_common_success_path_ratio"]),
        "penalized_time": within(ratios["elapsed_s"],q["maximum_penalized_time_ratio"]),
        "penalized_path": within(ratios["path_m"],q["maximum_penalized_path_ratio"]),
        "cpu": within(cpu_ratio,b["maximum_p95_decision_cpu_ratio"]),
        "resources": all(e["resources"]["peak_cells"]<=b["max_cells"] and e["resources"]["peak_expansions"]<=b["max_expansions"]
                         and not e["resources"]["budget_exhausted"] and e["resources"]["rss_peak_mib"]<=b["controller_rss_limit_mib"] for e in episodes)}
    return {"met": all(gates.values()), "gates": gates, "feasible_cases":len(feasible), "negative_cases":len(cases)-len(feasible),
            "case_successes":success,"adverse_cases":adverse,"adverse_upper_bound":upper,
            "penalized_ratios":ratios,"common_success_cases":common_n,"common_success_path_ratio":common_path,
            "common_success_time_ratio":common_time,
            "cpu_p95_ratio":cpu_ratio,"paired_table":{f"{int(ref)}{int(cand)}":sum(
                groups[c["id"]]["reference"]["success"]==ref and groups[c["id"]]["candidate"]["success"]==cand for c in feasible)
                for ref in (False,True) for cand in (False,True)},
            "by_family":{f:{a:sum(groups[c["id"]][a]["success"] for c in cases if c["family"]==f) for a in success}
                         for f in sorted({c["family"] for c in cases})},"collapsed":groups}
