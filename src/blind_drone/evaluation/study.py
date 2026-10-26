"""Validate paired split coverage/provenance; never cherry-pick navigation outcomes."""
from math import dist, pi

from blind_drone.evaluation.episode import summarize
from blind_drone.world.scenarios import digest


def validate_study(reports,manifest,protocol_hash):
    splits = ("development","validation","test")
    if len(reports)!=len(splits) or {r.get("split") for r in reports}!=set(splits):
        raise ValueError("Exactly one complete report is required for each evaluated split")
    sources = {r.get("source_commit") for r in reports}
    if len(sources)!=1 or None in sources:
        raise ValueError("All reports must identify the same source commit")
    for report in reports:
        if report.get("suite")!="seeded" or report.get("status")!="passed" or not report.get("complete_split"):
            raise ValueError("Partial or failed suite report")
        if not report.get("checks") or not all(c.get("passed") is True for c in report["checks"].values()):
            raise ValueError("Integration checks did not pass")
        if report.get("protocol_sha256")!=protocol_hash or report.get("manifest_sha256")!=digest(manifest):
            raise ValueError("Protocol/manifest mismatch")
        expected = {c["id"]:c for c in manifest["cases"] if c["split"]==report["split"]}
        episodes = report["episodes"]
        pairs = [(e["case_id"],e["policy"]) for e in episodes]
        wanted = {(case_id,policy) for case_id in expected for policy in manifest["specification"]["policies"]}
        if len(pairs)!=len(set(pairs)) or set(pairs)!=wanted:
            raise ValueError("Missing, duplicated or foreign episode in paired split")
        for episode in episodes:
            case = expected[episode["case_id"]]
            if any(episode.get(k)!=case[k] for k in ("family","seed","feasible","geometry_sha256")):
                raise ValueError("Episode metadata differs from frozen case")
            if episode["outcome"] not in {"success","collision","out_of_bounds","timeout"}:
                raise ValueError("Unknown episode outcome")
            if not case["feasible"] and episode["outcome"]=="success":
                raise ValueError("Impossible negative control was scored successful")
            if case["family"]=="empty" and episode["outcome"]!="success":
                raise ValueError("Empty-space task sanity check failed")
            if case["family"]=="single_block" and episode["policy"]=="direct" and episode["outcome"]!="collision":
                raise ValueError("Direct collision sanity check failed")
            if dist(episode["initial_position_m"],case["start_m"])>.18:
                raise ValueError("Wrong initial pose")
            yaw_error = (episode["initial_yaw_rad"]-case["start_yaw_rad"]+pi)%(2*pi)-pi
            if abs(yaw_error)>.1:
                raise ValueError("Wrong initial yaw")
        # Recompute summaries; do not trust a report that quietly drops failures.
        if report["summary"]!=summarize(episodes):
            raise ValueError("Summary differs from complete episode outcomes")
    ordered = sorted(reports,key=lambda r:splits.index(r["split"]))
    return {"status":"passed","stage":"environment_and_evaluation_before_training",
            "source_commit":next(iter(sources)),"protocol_sha256":protocol_hash,"manifest_sha256":digest(manifest),
            "evaluated_episodes":sum(len(r["episodes"]) for r in reports),
            "reserved_training_cases":sum(c["split"]=="train_reserved" for c in manifest["cases"]),
            "summary_by_split":{r["split"]:summarize(r["episodes"]) for r in ordered},
            "by_family_by_split":{r["split"]:{family:summarize([e for e in r["episodes"] if e["family"]==family])
                for family in sorted({e["family"] for e in r["episodes"]})} for r in ordered},
            "quality_claim":"Pipeline coverage/integrity passed; navigation capability must be read from every outcome.",
            "test_reuse_rule":"Once viewed, these test results are exposed; do not tune and report on them as unseen again."}
