"""Privileged, paired diagnostic episodes. Never sends motion commands or paths."""
import hashlib
import json
import os
from pathlib import Path
import traceback
import tomllib

from blind_drone.evaluation.episode import EpisodeEvaluator, summarize
from blind_drone.world.minimal_lab import NAV_CONFIG, ROOT, load_config


def main():
    from controller import Supervisor

    supervisor = Supervisor()
    lab_config = load_config()
    specification = tomllib.loads(NAV_CONFIG.read_text())
    output = Path(os.environ["BLIND_DRONE_OUTPUT"])
    output.mkdir(parents=True, exist_ok=True)
    config = specification["evaluation"]
    selection = os.environ.get("BLIND_DRONE_POLICY", "both")
    policies = ["direct", "reactive"] if selection == "both" else [selection]
    cases = specification["cases"]
    requested = os.environ.get("BLIND_DRONE_CASE")
    if requested:
        cases = [case for case in cases if case["id"] == requested]
    if not cases or any(policy not in {"direct", "reactive"} for policy in policies):
        raise ValueError("Unknown case/policy")
    step_ms = int(supervisor.getBasicTimeStep())
    emitter = supervisor.getDevice("operator")
    receiver = supervisor.getDevice("telemetry")
    receiver.enable(step_ms)
    drone = supervisor.getFromDef("DRONE")
    blocks = [supervisor.getFromDef(item["id"]) for item in lab_config["world"]["obstacles"]]
    goal_node = supervisor.getFromDef("GOAL")
    report = {"status": "running", "mode": "navigation", "webots_version": "R2025a",
              "source_commit": os.environ.get("GITHUB_SHA"), "ci_run_id": os.environ.get("GITHUB_RUN_ID"),
              "algorithm_version": "range_tangent_v1", "lab_config": lab_config,
              "split": specification["split"], "specification_sha256": hashlib.sha256(NAV_CONFIG.read_bytes()).hexdigest(),
              "specification": specification, "episodes": [], "checks": {},
              "assumptions": ["ideal localization and ranges", "horizontal detours at goal altitude",
                              "public development fixtures; not held-out evaluation", "no learned model"]}
    (output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    log = (output / "telemetry.jsonl").open("w", buffering=1)
    next_log = 0.0
    latest = None

    def send(packet):
        emitter.send(json.dumps(packet, allow_nan=False).encode())

    def step():
        nonlocal latest, next_log
        if supervisor.step(step_ms) == -1:
            raise RuntimeError("Simulation stopped before diagnostics completed")
        while receiver.getQueueLength():
            packet = json.loads(receiver.getString())
            receiver.nextPacket()
            if packet.get("kind") != "telemetry":
                raise RuntimeError("Unexpected reset/operator request during evaluation")
            latest = packet
        now = supervisor.getTime()
        if latest is not None and now - latest["time_s"] > 0.25:
            raise RuntimeError("Stale drone telemetry")
        if latest is not None and now >= next_log:
            log.write(json.dumps({"case_id": case["id"], "policy": policy, **latest}, allow_nan=False) + "\n")
            next_log = now + 0.064
        return now

    try:
        for case in cases:
            for policy in policies:
                latest = None
                while receiver.getQueueLength():
                    receiver.nextPacket()
                if len(case["obstacles"]) > len(blocks):
                    raise ValueError("Fixture exceeds available primitive blocks")
                for index, node in enumerate(blocks):
                    item = case["obstacles"][index] if index < len(case["obstacles"]) else {"center_m": [30.0 + index, 30.0, 1.5], "size_m": [0.5, 0.5, 3.0]}
                    node.getField("translation").setSFVec3f(item["center_m"])
                    node.getField("boundingObject").getSFNode().getField("size").setSFVec3f(item["size_m"])
                    shape = node.getField("children").getMFNode(0)
                    shape.getField("geometry").getSFNode().getField("size").setSFVec3f(item["size_m"])
                goal_node.getField("translation").setSFVec3f(case["goal_m"])
                drone.getField("translation").setSFVec3f(case["start_m"])
                drone.getField("rotation").setSFRotation([0, 0, 1, 0])
                drone.resetPhysics()
                send({"kind": "reset"})
                warmup_start = supervisor.getTime()
                while supervisor.getTime() - warmup_start < config["warmup_s"]:
                    step()
                    if drone.getContactPoints(True):
                        raise RuntimeError("Collision during reset warmup")
                if latest is None:
                    raise RuntimeError("No telemetry after warmup")
                if any("camera" in name.lower() for name in latest["devices"]):
                    raise RuntimeError("Image device in evaluated drone")
                send({"kind": "mission", "goal_m": case["goal_m"], "policy": policy})
                start = supervisor.getTime()
                evaluator = EpisodeEvaluator(case["goal_m"], config)
                while True:
                    now = step()
                    position = drone.getPosition()
                    velocity = drone.getVelocity()[:3]
                    contacts = drone.getContactPoints(True)
                    result = evaluator.update(now - start, position, velocity, len(contacts))
                    supervisor.setLabel(0, f"{case['id']} | {policy} | {now-start:.1f}s", 0.02, 0.02, 0.05, 0xFFFFFF, 0, "Arial")
                    supervisor.setLabel(1, f"{latest['navigation']['state']} | goal distance={evaluator.min_goal_distance_m:.2f}m", 0.02, 0.09, 0.035, 0x77FFAA, 0, "Arial")
                    if result:
                        episode = {"case_id": case["id"], "policy": policy, "feasible": case["feasible"],
                                   "final_position_m": position, **result}
                        report["episodes"].append(episode)
                        (output / "progress.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
                        print("NAVIGATION_EPISODE " + json.dumps(episode), flush=True)
                        supervisor.exportImage(str(output / f"{case['id']}-{policy}.jpg"), 85)
                        if case["id"] == "single_block" and policy == "reactive":
                            supervisor.exportImage(str(output / "scene.jpg"), 85)
                        break
        # Only integration sanity checks are pass/fail gates. Every episode,
        # including any reactive failure, remains in the report and summary.
        episodes = report["episodes"]
        def check(name, condition):
            report["checks"][name] = {"passed": bool(condition)}
        check("all_requested_episodes_recorded", len(episodes) == len(cases) * len(policies))
        check("negative_controls_never_succeed", all(e["outcome"] != "success" for e in episodes if not e["feasible"]))
        empty = [e for e in episodes if e["case_id"] == "empty"]
        if empty:
            check("empty_goal_and_dwell", all(e["outcome"] == "success" for e in empty))
        blocked = [e for e in episodes if e["case_id"] == "single_block" and e["policy"] == "direct"]
        if blocked:
            check("direct_collision_is_detected", all(e["outcome"] == "collision" for e in blocked))
        detours = [e for e in episodes if e["case_id"] == "single_block" and e["policy"] == "reactive"]
        if detours:
            check("reactive_basic_detour", all(e["outcome"] == "success" for e in detours))
        report["summary"] = summarize(episodes)
        report["status"] = "passed" if all(c["passed"] for c in report["checks"].values()) else "failed"
    except Exception as error:
        traceback.print_exc()
        report["status"], report["error"] = "failed", str(error)
    finally:
        log.close()
        (output / "result.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        print("NAVIGATION_RESULT " + json.dumps(report, allow_nan=False), flush=True)
        supervisor.simulationQuit(0 if report["status"] == "passed" else 1)
