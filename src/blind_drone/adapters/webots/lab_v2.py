"""Privileged, paired diagnostic episodes. Never sends motion commands or paths."""
import hashlib
import json
from math import dist, pi, sqrt
import os
from pathlib import Path
import traceback
import tomllib

from blind_drone.evaluation.episode import EpisodeEvaluator, summarize
from blind_drone.experiments.protocol_v2 import CONFIG as NAV_CONFIG, LOCK, load_v2_config as load_config, select_suite_v2
from blind_drone.world.minimal_lab import ROOT
from blind_drone.world.scenarios import digest


def main():
    from controller import Supervisor

    supervisor = Supervisor()
    lab_config = load_config()
    specification = tomllib.loads(NAV_CONFIG.read_text())
    output = Path(os.environ["BLIND_DRONE_OUTPUT"])
    output.mkdir(parents=True, exist_ok=True)
    config = dict(specification["evaluation"])
    selection = os.environ.get("BLIND_DRONE_POLICY", "all")
    policies = specification["policies"] if selection=="all" else [selection]
    if any(p not in specification["policies"] for p in policies):raise ValueError("Invalid policy")
    requested=os.environ.get("BLIND_DRONE_CASE")
    split=os.environ.get("BLIND_DRONE_SPLIT","development")
    manifest,cases,protocol_hash=select_suite_v2(split,requested)
    manifest_hash=digest(manifest)
    suite="observed_v2"
    rendering=os.environ.get("BLIND_DRONE_RENDERING","true")=="true"
    specification={"split":split,"evaluation":config,"case_ids":[c["id"] for c in cases]}
    (output/"cases.json").write_text(json.dumps(cases,indent=2)+"\n")
    step_ms = int(supervisor.getBasicTimeStep())
    emitter = supervisor.getDevice("operator")
    receiver = supervisor.getDevice("telemetry")
    receiver.enable(step_ms)
    drone = supervisor.getFromDef("DRONE")
    blocks = [supervisor.getFromDef(item["id"]) for item in lab_config["world"]["obstacles"]]
    goal_node = supervisor.getFromDef("GOAL")
    report = {"status": "running", "mode": "navigation", "webots_version": "R2025a",
              "source_commit": os.environ.get("GITHUB_SHA") or os.environ.get("BLIND_DRONE_SOURCE_COMMIT"),
              "working_tree_dirty":os.environ.get("BLIND_DRONE_DIRTY")!="false","ci_run_id": os.environ.get("GITHUB_RUN_ID"),
              "algorithm_version": "observed_grid_v2", "lab_config": lab_config,
              "suite":suite,"protocol_sha256":protocol_hash,"manifest_sha256":manifest_hash,
              "protocol_frozen":LOCK.exists(),
              "rendering_enabled":rendering,
              "complete_split":not requested and selection=="all",
              "split": specification["split"], "specification_sha256": hashlib.sha256(NAV_CONFIG.read_bytes()).hexdigest(),
              "specification": specification, "episodes": [], "checks": {},
              "assumptions": ["ideal localization and ranges", "horizontal detours at goal altitude",
                              "public fixtures; split isolation relies on frozen protocol, not secrecy", "no learned model"]}
    (output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    log = (output / "telemetry.jsonl").open("w", buffering=1)
    next_log = 0.0
    next_label = 0.0
    latest = None
    trajectories = []
    failures = []

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
                drone.getField("rotation").setSFRotation([0, 0, 1, case.get("start_yaw_rad",0.0)])
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
                actual_start = drone.getPosition()
                initial_speed = sqrt(sum(v*v for v in drone.getVelocity()[:3]))
                if dist(actual_start,case["start_m"]) > 0.18 or initial_speed > 0.18:
                    raise RuntimeError("Reset did not settle at the requested start pose")
                initial_yaw = latest["attitude_rad"][2]
                yaw_error = (initial_yaw-case.get("start_yaw_rad",0.0)+pi)%(2*pi)-pi
                if abs(yaw_error) > 0.1:
                    raise RuntimeError("Reset yaw did not settle")
                send({"kind": "mission", "goal_m": case["goal_m"], "policy": policy})
                start = supervisor.getTime()
                evaluator = EpisodeEvaluator(case["goal_m"], config)
                evaluator.update(0.0,actual_start,drone.getVelocity()[:3],0)
                trajectory = {"case_id":case["id"],"policy":policy,"frame":"world_ENU",
                              "source":"privileged_observer_only","points_txyz":[[0.0,*[round(v,4) for v in actual_start]]]}
                next_trace = 0.5
                while True:
                    now = step()
                    position = drone.getPosition()
                    velocity = drone.getVelocity()[:3]
                    contacts = drone.getContactPoints(True)
                    result = evaluator.update(now - start, position, velocity, len(contacts))
                    if now-start >= next_trace or result:
                        trajectory["points_txyz"].append([round(now-start,3),*[round(v,4) for v in position]])
                        next_trace = now-start+0.5
                    if rendering and now>=next_label:
                        supervisor.setLabel(0, f"{case['id']} | {policy} | {now-start:.1f}s", 0.02, 0.02, 0.05, 0xFFFFFF, 0, "Arial")
                        supervisor.setLabel(1, f"{latest['navigation']['state']} | distance={dist(position,case['goal_m']):.2f}m", 0.02, 0.09, 0.035, 0x77FFAA, 0, "Arial")
                        next_label=now+.25
                    if result:
                        if result["outcome"]!="success":
                            failures.append({"case_id":case["id"],"policy":policy,"time_s":now,"outcome":result["outcome"],
                                             "public_observation":{k:latest[k] for k in ("time_s","position_m","attitude_rad","ranges","navigation")},
                                             "ground_truth_position_m":position,"contact_count":len(contacts)})
                            (output/"failures.json").write_text(json.dumps(failures,indent=2)+"\n")
                        episode = {"case_id": case["id"], "policy": policy, "feasible": case["feasible"],
                                   "family":case.get("family",case["id"]),"seed":case.get("seed"),
                                   "geometry_sha256":case.get("geometry_sha256"),"initial_position_m":actual_start,
                                   "initial_yaw_rad":initial_yaw,
                                   "diagnostics":latest["navigation"]["diagnostics"],"final_position_m": position, **result}
                        trajectories.append(trajectory)
                        (output / "trajectories.json").write_text(json.dumps(trajectories,separators=(",",":"))+"\n")
                        report["episodes"].append(episode)
                        (output / "progress.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
                        print("NAVIGATION_EPISODE " + json.dumps(episode), flush=True)
                        if rendering:supervisor.exportImage(str(output / f"{case['id']}-{policy}.jpg"), 85)
                        if rendering and (case["id"] == "single_block" or case.get("family")=="u_trap") and policy == "mapped":
                            supervisor.exportImage(str(output / "scene.jpg"), 85)
                        break
        # Only integration sanity checks are pass/fail gates. Every episode,
        # including any reactive failure, remains in the report and summary.
        episodes = report["episodes"]
        def check(name, condition):
            report["checks"][name] = {"passed": bool(condition)}
        check("all_requested_episodes_recorded", len(episodes) == len(cases) * len(policies))
        check("negative_controls_never_succeed", all(e["outcome"] != "success" for e in episodes if not e["feasible"]))
        empty = [e for e in episodes if e["family"] == "empty"]
        if empty:
            check("empty_goal_and_dwell", all(e["outcome"] == "success" for e in empty))
        blocked = [e for e in episodes if e["family"] == "single_block" and e["policy"] == "direct"]
        if blocked:
            check("direct_collision_is_detected", all(e["outcome"] == "collision" for e in blocked))
        detours = [e for e in episodes if e["case_id"] == "single_block" and e["policy"] == "reactive"]
        if detours and suite=="diagnostic":
            check("reactive_basic_detour", all(e["outcome"] == "success" for e in detours))
        report["summary"] = summarize(episodes)
        report["by_family"] = {family:summarize([e for e in episodes if e["family"]==family]) for family in sorted({e["family"] for e in episodes})}
        report["status"] = "passed" if all(c["passed"] for c in report["checks"].values()) else "failed"
    except Exception as error:
        traceback.print_exc()
        report["status"], report["error"] = "failed", str(error)
    finally:
        log.close()
        (output / "result.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        print("NAVIGATION_RESULT " + json.dumps(report, allow_nan=False), flush=True)
        supervisor.simulationQuit(0 if report["status"] == "passed" else 1)
