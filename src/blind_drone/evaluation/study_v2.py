"""Integrity and measured engineering criteria for the frozen v2 comparison."""
from math import dist,pi

from blind_drone.evaluation.episode import summarize
from blind_drone.world.scenarios import digest


def development_goal(episodes):
    mapped=[e for e in episodes if e["policy"]=="mapped" and e["feasible"]]
    reactive=[e for e in episodes if e["policy"]=="reactive" and e["feasible"]]
    successes=sum(e["outcome"]=="success" for e in mapped)
    u_successes=sum(e["family"]=="u_trap" and e["outcome"]=="success" for e in mapped)
    collisions=sum(e["outcome"]=="collision" for e in mapped)
    baseline_collisions=sum(e["outcome"]=="collision" for e in reactive)
    return {"met":len(mapped)==10 and len(reactive)==10 and successes>=8 and u_successes>=1 and collisions<=baseline_collisions,
            "mapped_successes":successes,"mapped_u_successes":u_successes,
            "mapped_collisions":collisions,"reactive_collisions":baseline_collisions}


def validate_v2(reports,manifest,protocol_hash,policies,max_cells):
    splits=("development","validation","test")
    if len(reports)!=3 or {r.get("split") for r in reports}!=set(splits):raise ValueError("Missing/duplicate split")
    sources={r.get("source_commit") for r in reports}
    if len(sources)!=1 or None in sources:raise ValueError("Source commit mismatch")
    for report in reports:
        if report.get("status")!="passed" or not report.get("complete_split") or not report.get("protocol_frozen"):
            raise ValueError("Partial, candidate or failed result")
        if not report.get("checks") or not all(c.get("passed") is True for c in report["checks"].values()):raise ValueError("Failed integration checks")
        if report.get("suite")!="observed_v2" or report.get("protocol_sha256")!=protocol_hash or report.get("manifest_sha256")!=digest(manifest):
            raise ValueError("Suite/protocol/manifest mismatch")
        expected={c["id"]:c for c in manifest["cases"] if c["split"]==report["split"]}
        episodes=report["episodes"]
        pairs=[(e["case_id"],e["policy"]) for e in episodes]
        if len(pairs)!=len(set(pairs)) or set(pairs)!={(c,p) for c in expected for p in policies}:
            raise ValueError("Missing, duplicate or foreign episode")
        for episode in episodes:
            case=expected[episode["case_id"]]
            if any(episode.get(k)!=case[k] for k in ("family","seed","feasible","geometry_sha256")):
                raise ValueError("Case metadata mismatch")
            if dist(episode["initial_position_m"],case["start_m"])>.18:raise ValueError("Initial pose mismatch")
            if abs((episode["initial_yaw_rad"]-case["start_yaw_rad"]+pi)%(2*pi)-pi)>.1:raise ValueError("Initial yaw mismatch")
            outcome=episode["outcome"]
            if outcome not in {"success","collision","out_of_bounds","timeout"}:raise ValueError("Invalid outcome")
            if not case["feasible"] and outcome=="success":raise ValueError("False success for impossible goal")
            if case["family"]=="empty" and outcome!="success":raise ValueError("Empty-space sanity failed")
            stats=episode["diagnostics"]
            if stats["peak_cells"]>max_cells or stats["range_values"]!=10*stats["range_samples"]:
                raise ValueError("Invalid memory/sampling counters")
        if report["summary"]!=summarize(episodes):raise ValueError("Summary dropped or changed an outcome")
    performance={}
    for split in splits:
        report=next(r for r in reports if r["split"]==split)
        performance[split]={}
        for policy in policies:
            values=[e["diagnostics"] for e in report["episodes"] if e["policy"]==policy]
            decisions=sum(v["decisions"] for v in values)
            performance[split][policy]={"max_primary_cells":max(v["peak_cells"] for v in values),
                "max_derived_blocked_cells":max(v["derived_blocked_cells"] for v in values),
                "cpu_weighted_mean_ms":sum(v["cpu_mean_ms"]*v["decisions"] for v in values)/max(1,decisions),
                "cpu_max_ms":max(v["cpu_max_ms"] for v in values),"range_values":sum(v["range_values"] for v in values),
                "guard_events":sum(v["guard_events"] for v in values),"plans":sum(v["plans"] for v in values)}
    dev=next(r for r in reports if r["split"]=="development")
    return {"status":"passed","source_commit":next(iter(sources)),"protocol_sha256":protocol_hash,
            "manifest_sha256":digest(manifest),"episodes":sum(len(r["episodes"]) for r in reports),
            "development_engineering_goal":development_goal(dev["episodes"]),
            "summary_by_split":{r["split"]:summarize(r["episodes"]) for r in reports},"resource_metrics":performance,
            "limits":"Ideal static horizontal simulation; bounded observed map is not a privacy guarantee or proof of safety."}
