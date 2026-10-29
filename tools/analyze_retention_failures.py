"""Describe exposed retention failures from existing logs; never run a policy/simulator.

Manifest digests below identify the three previously reviewed historical runs.
Only selected case/result/decision/physics files are rehashed here. This bounded
analysis does not repeat the original complete raw replay or infer causality.
"""
import argparse
from collections import Counter
import hashlib
import json
from math import dist, hypot, pi
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


STUDIES = {
    "v4": ("9503c2c2b483d677d7f0ff25f76d7dcca360bc08",
           "e7840b636a2c67365a01e185c27214899bcf1328d43db3ee0e147ab82819bb83"),
    "data03": ("94f8e0b461c01aa18f269e75eb6662ce2d2283df",
               "bc188514e0d1a862fac548e8340fd8f6e85cc9897b0d08b063fd502f04f83fea"),
    "data04": ("8b4e3bed8a9e86946ca1c7c2a47dcffdf646aca2",
               "35186405fb35e0eb0584d5bf63c369da086c57a69bef198fc104c5da04323a5c"),
}
METHODS = {"v4_full_history": ("v4", "candidate"),
           "data03_original": ("data03", "candidate"),
           "data03_in_data04": ("data04", "reference"),
           "data04_ttl10": ("data04", "candidate")}


def checked_bytes(path, expected):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("Raw hash mismatch: " + str(path))
    return data


def case_outcomes(episodes, arm):
    """Collapse two repeats by case, excluding negative controls."""
    rows = {}
    for episode in episodes:
        if episode["arm"] != arm or not episode["feasible"]:
            continue
        key = episode["case_id"], episode["repeat"]
        if episode["repeat"] not in (0, 1) or key in rows:
            raise ValueError("Unexpected or duplicate repeat")
        rows[key] = episode["outcome"]
    result = {}
    for case_id in sorted({key[0] for key in rows}):
        if any((case_id, repeat) not in rows for repeat in (0, 1)):
            raise ValueError("Missing repeat for " + case_id)
        result[case_id] = [rows[(case_id, repeat)] for repeat in (0, 1)]
    return result


def decision_profile(decisions):
    if not decisions or any(b["time_s"] <= a["time_s"] for a, b in zip(decisions, decisions[1:])):
        raise ValueError("Missing or unordered decisions")
    def moving(row):
        command = row["command"]
        return hypot(command["forward_m_s"], command["left_m_s"]) > 1e-9
    tail = [row for row in decisions if row["time_s"] >= decisions[-1]["time_s"] - 10.]
    return {"decisions": len(decisions),
            "status_counts": dict(sorted(Counter(row["status"] for row in decisions).items())),
            "nonzero_horizontal_commands": sum(moving(row) for row in decisions),
            "last_10s_decisions": len(tail),
            "last_10s_status_counts": dict(sorted(Counter(row["status"] for row in tail).items())),
            "last_10s_nonzero_horizontal_commands": sum(moving(row) for row in tail)}


def goal_dwell_profile(physics, goal, quality):
    """Describe goal proximity versus uninterrupted slow dwell, without rescoring."""
    first_inside = first_slow = since = None
    longest = 0.
    for row in physics:
        inside = dist(row["position_m"], goal) <= quality["goal_radius_m"]
        slow = inside and hypot(*row["velocity_m_s"]) <= quality["stop_speed_m_s"]
        if inside and first_inside is None:
            first_inside = row["time_s"]
        if slow:
            if first_slow is None:
                first_slow = row["time_s"]
            if since is None:
                since = row["time_s"]
            longest = max(longest, row["time_s"] - since)
        else:
            since = None
    return {"first_inside_goal_s": first_inside, "first_slow_inside_goal_s": first_slow,
            "longest_slow_goal_interval_s": longest}


def analyze(runs):
    manifests = {}
    outcomes = {}
    for study, run in runs.items():
        source, expected_hash = STUDIES[study]
        manifest = json.loads(checked_bytes(run / "result.json", expected_hash))
        if (manifest["source_commit"] != source or manifest["working_tree_dirty"] or
                manifest["split"] != "development" or manifest["status"] != "complete" or
                not manifest["integrity_passed"] or len(manifest["episodes"]) != 352 or
                len(manifest["attempts"]) != 176):
            raise ValueError("Unexpected historical manifest: " + study)
        manifests[study] = manifest
    for method, (study, arm) in METHODS.items():
        outcomes[method] = case_outcomes(manifests[study]["episodes"], arm)
    membership = set(outcomes["v4_full_history"])
    if len(membership) != 74 or any(set(rows) != membership for rows in outcomes.values()):
        raise ValueError("Feasible task membership differs")
    if len({m["development_sha256"] for m in manifests.values()}) != 1:
        raise ValueError("Development commitments differ")
    spec_path = "versions/navigation_v4/development.toml"
    spec_bytes = checked_bytes(ROOT / spec_path, manifests["v4"]["files"][spec_path])
    quality = tomllib.loads(spec_bytes.decode())["quality"]
    selected = sorted({case for method, rows in outcomes.items() if method != "v4_full_history"
                       for case, repeats in rows.items() if repeats != ["success", "success"]})
    rows = []
    verified = {}
    for method, (study, arm) in METHODS.items():
        manifest = manifests[study]
        attempts = {(a["case_id"], a["repeat"]): a for a in manifest["attempts"]}
        episodes = {(e["case_id"], e["arm"], e["repeat"]): e for e in manifest["episodes"]}
        for case in selected:
            for repeat in (0, 1):
                attempt = attempts[(case, repeat)]
                if attempt["classification"] != "valid" or not attempt["raw_integrity_passed"]:
                    raise ValueError("Invalid attempt")
                folder = runs[study] / Path(attempt["output"]).name
                prefix = arm + str(repeat)
                names = ["case.json", "result.json", "evaluation.jsonl", prefix + "-decisions.jsonl"]
                raw = {name: checked_bytes(folder / name, attempt["files_sha256"][name]) for name in names}
                fixture, pair = json.loads(raw["case.json"]), json.loads(raw["result.json"])
                episode = episodes[(case, arm, repeat)]
                if fixture["id"] != case or pair["status"] != "complete" or episode not in pair["episodes"]:
                    raise ValueError("Raw case/episode mismatch")
                decisions = [json.loads(line) for line in raw[prefix + "-decisions.jsonl"].splitlines()]
                profile = decision_profile(decisions)
                if profile["decisions"] != episode["cpu"]["decisions"]:
                    raise ValueError("Decision count mismatch")
                physics = [json.loads(line) for line in raw["evaluation.jsonl"].splitlines()]
                physics = [point for point in physics if point["arm"] == arm]
                if not physics:
                    raise ValueError("Missing scored physics")
                tail = [p["position_m"] for p in physics if p["time_s"] >= physics[-1]["time_s"] - 10.]
                span = hypot(*(max(p[i] for p in tail) - min(p[i] for p in tail) for i in (0, 1)))
                rows.append({"method": method, "case_id": case, "repeat": repeat,
                             "arm_order": attempt["order"], "arm_slot": attempt["order"].index(arm),
                             "initial_position_m": episode["initial_position_m"],
                             "initial_velocity_m_s": episode["initial_velocity_m_s"],
                             "outcome": episode["outcome"], "elapsed_s": episode["elapsed_s"],
                             "path_length_m": episode["path_length_m"],
                             "final_distance_m": episode["final_distance_m"],
                             "min_goal_distance_m": episode["min_goal_distance_m"],
                             "budget_exhausted": episode["resources"]["budget_exhausted"],
                             "invalid_acquisition_values": episode["acquisition"]["all"]["invalid_values"],
                             "last_10s_horizontal_bbox_diagonal_m": span,
                             **goal_dwell_profile(physics, fixture["goal_m"], quality), **profile})
                for name in names:
                    verified[f"{study}/{folder.name}/{name}"] = attempt["files_sha256"][name]
    original, reference = outcomes["data03_original"], outcomes["data03_in_data04"]
    slot_rows = {}
    for study, arm in [("data03", "candidate"), ("data04", "reference")]:
        slot_rows[study] = {(a["case_id"], a["order"].index(arm)): next(
            e["outcome"] for e in a["result"]["episodes"] if e["arm"] == arm)
            for a in manifests[study]["attempts"] if a["case_id"] in membership}
    initial_deltas = {}
    for study, manifest in manifests.items():
        pairs = [a["result"]["episodes"] for a in manifest["attempts"] if a["case_id"] in membership]
        initial_deltas[study] = {
            "max_position_delta_m": max(dist(a["initial_position_m"], b["initial_position_m"]) for a, b in pairs),
            "max_velocity_delta_m_s": max(dist(a["initial_velocity_m_s"], b["initial_velocity_m_s"]) for a, b in pairs),
            "max_yaw_delta_rad": max(abs((a["initial_yaw_rad"] - b["initial_yaw_rad"] + pi) % (2*pi) - pi)
                                     for a, b in pairs)}
    return {"schema_version": 1, "kind": "bounded_offline_retention_failure_description",
            "scope": "exposed development only; no simulator/policy run or causal inference",
            "goal_quality": quality,
            "sources": {s: {"source_commit": STUDIES[s][0], "manifest_sha256": STUDIES[s][1]}
                        for s in STUDIES},
            "selected_feasible_cases": selected,
            "case_outcomes": {c: {m: r[c] for m, r in outcomes.items()} for c in selected},
            "success_cases": {m: sum(r == ["success", "success"] for r in cases.values())
                              for m, cases in outcomes.items()},
            "same_method_cross_run_case_changes": [c for c in original if
                (original[c] == ["success", "success"]) != (reference[c] == ["success", "success"])],
            "same_method_cross_run_repeat_changes": [{"case_id": c, "repeat": r,
                "original": original[c][r], "in_data04": reference[c][r]}
                for c in original for r in (0, 1) if original[c][r] != reference[c][r]],
            "same_method_cross_run_slot_changes": [{"case_id": c, "slot": slot,
                "original": old, "in_data04": slot_rows["data04"][(c, slot)]}
                for (c, slot), old in slot_rows["data03"].items() if old != slot_rows["data04"][(c, slot)]],
            "within_pair_initial_state_max_deltas": initial_deltas,
            "episodes": rows, "verified_selected_files_sha256": verified}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in STUDIES:
        parser.add_argument("--" + name + "-run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    value = analyze({name: getattr(args, name + "_run") for name in STUDIES})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as output:
        output.write(json.dumps(value, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"selected_cases": len(value["selected_feasible_cases"]),
                      "described_episodes": len(value["episodes"]),
                      "success_cases": value["success_cases"],
                      "same_method_cross_run_case_changes": value["same_method_cross_run_case_changes"]}))


if __name__ == "__main__":
    raise SystemExit(main())
