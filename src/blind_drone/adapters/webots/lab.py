"""Privileged test fixtures and observer UI; never a navigation input source."""
from __future__ import annotations

import json
from math import sqrt
import os
from pathlib import Path
import traceback

from blind_drone.world.minimal_lab import ROOT, load_config


def norm(values):
    return sqrt(sum(value * value for value in values))


def main():
    from controller import Supervisor

    supervisor = Supervisor()
    config = load_config()
    smoke = os.environ.get("BLIND_DRONE_MODE", "manual") == "smoke"
    output = Path(os.environ.get("BLIND_DRONE_OUTPUT", str(ROOT / "artifacts/webots-manual"))).resolve()
    output.mkdir(parents=True, exist_ok=True)
    step_ms = int(supervisor.getBasicTimeStep())
    emitter, receiver = (supervisor.getDevice(name) for name in ("operator", "telemetry"))
    receiver.enable(step_ms)
    drone = supervisor.getFromDef("DRONE")
    hidden = supervisor.getFromDef("BLOCK_HIDDEN")
    hidden_initial = next(item["center_m"] for item in config["world"]["obstacles"] if item["id"] == "BLOCK_HIDDEN")
    limits = config["smoke"]
    result = {"status": "running", "mode": "smoke" if smoke else "manual", "webots_version": "R2025a",
              "checks": {}, "assumptions": ["ideal GPS/attitude/gyro", "geometric ranges without noise", "operator-scripted motion, no autonomous navigation"]}
    latest = None
    stage, stage_start = "hover", 0.0
    stage_origin = None
    saved_front = None
    telemetry_count = 0
    next_log = next_label = 0.0
    log = (output / "telemetry.jsonl").open("w", encoding="utf-8", buffering=1)

    def send(packet):
        emitter.send(json.dumps(packet, allow_nan=False).encode())

    def move(forward=0.0, left=0.0, up=0.0, yaw=0.0):
        send({"kind": "motion", "forward_m_s": forward, "left_m_s": left, "up_m_s": up, "yaw_rate_rad_s": yaw})

    def place(position):
        drone.getField("translation").setSFVec3f(position)
        drone.getField("rotation").setSFRotation([0, 0, 1, 0])
        drone.resetPhysics()
        send({"kind": "reset"})

    def reset_world():
        hidden.getField("translation").setSFVec3f(hidden_initial)
        place(config["world"]["start_m"])

    def require(name, condition, details):
        result["checks"][name] = {"passed": bool(condition), **details}
        if not condition:
            raise AssertionError(f"{name}: {details}")

    def finish(success, error=None):
        result["status"] = "passed" if success else "failed"
        result["elapsed_simulation_s"] = supervisor.getTime()
        result["telemetry_packets"] = telemetry_count
        if error:
            result["error"] = str(error)
        (output / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        log.close()
        print("BLIND_DRONE_SMOKE_RESULT " + json.dumps(result, allow_nan=False), flush=True)
        supervisor.simulationQuit(0 if success else 1)

    try:
        print("BLIND_DRONE_LAB_READY: mode=" + result["mode"], flush=True)
        while supervisor.step(step_ms) != -1:
            now = supervisor.getTime()
            while receiver.getQueueLength():
                packet = json.loads(receiver.getString())
                receiver.nextPacket()
                if packet.get("kind") == "reset_request":
                    reset_world()
                elif packet.get("kind") == "telemetry":
                    latest = packet
                    telemetry_count += 1
                    if now >= next_log:
                        log.write(json.dumps(packet, allow_nan=False) + "\n")
                        next_log = now + 0.064
            if latest is None:
                if now > 3:
                    raise RuntimeError("No telemetry from drone controller")
                continue
            if now - latest["time_s"] > 0.25:
                raise RuntimeError("Drone telemetry stopped")
            if now >= next_label:
                supervisor.setLabel(0, "BLIND DRONE LAB | " + (stage if smoke else "MANUAL"), 0.02, 0.02, 0.05, 0xFFFFFF, 0, "Arial")
                supervisor.setLabel(1, "W/S forward  A/D left  T/G height  Q/E yaw  SPACE brake  R reset", 0.02, 0.09, 0.035, 0xDDDDDD, 0, "Arial")
                front = (latest.get("ranges") or {}).get("readings", {}).get("range_000", {}).get("distance_m")
                supervisor.setLabel(2, f"t={now:.1f}s  z={latest['position_m'][2]:.2f}m  front={front}", 0.02, 0.14, 0.035, 0x77FFAA, 0, "Arial")
                next_label = now + 0.25
            if not smoke:
                continue
            elapsed = now - stage_start
            position = latest["position_m"]
            velocity = latest["velocity_m_s"]
            if now > limits["total_timeout_s"]:
                raise RuntimeError("Smoke sequence timeout at " + stage)
            if stage == "hover":
                move()
                if elapsed >= limits["hover_duration_s"]:
                    drift = norm([a-b for a,b in zip(position, config["world"]["start_m"])])
                    require("hover", drift < limits["hover_position_tolerance_m"] and max(abs(a) for a in latest["attitude_rad"][:2]) < 0.12,
                            {"position_error_m": drift, "altitude_m": position[2], "attitude_rad": latest["attitude_rad"]})
                    require("camera_free_devices", not any("camera" in name.lower() for name in latest["devices"]), {"device_names": latest["devices"]})
                    supervisor.exportImage(str(output / "scene.png"), 100)
                    stage, stage_start, stage_origin = "forward", now, list(position)
            elif stage == "forward":
                move(forward=config["vehicle"]["horizontal_speed_m_s"])
                if elapsed >= limits["motion_duration_s"]:
                    require("forward_motion", position[0] - stage_origin[0] > limits["minimum_motion_m"], {"delta_x_m": position[0] - stage_origin[0]})
                    stage, stage_start = "brake", now
            elif stage == "brake":
                move()
                if elapsed >= limits["brake_duration_s"]:
                    require("brake", norm(velocity) < limits["stop_speed_tolerance_m_s"], {"speed_m_s": norm(velocity)})
                    stage, stage_start, stage_origin = "strafe", now, list(position)
            elif stage == "strafe":
                move(left=0.6)
                if elapsed >= 1.5:
                    require("strafe_motion", position[1] - stage_origin[1] > 0.3, {"delta_y_m": position[1] - stage_origin[1]})
                    stage, stage_start = "strafe_brake", now
            elif stage == "strafe_brake":
                move()
                if elapsed >= 2:
                    stage, stage_start, stage_origin = "yaw", now, list(latest["attitude_rad"])
            elif stage == "yaw":
                move(yaw=0.5)
                if elapsed >= 1.5:
                    require("yaw_motion", latest["attitude_rad"][2] - stage_origin[2] > 0.2,
                            {"delta_yaw_rad": latest["attitude_rad"][2] - stage_origin[2]})
                    stage, stage_start, stage_origin = "ascend", now, list(position)
            elif stage == "ascend":
                move(up=0.4)
                if elapsed >= 1.5:
                    require("vertical_motion", position[2] - stage_origin[2] > 0.25, {"delta_z_m": position[2] - stage_origin[2]})
                    place(limits["sensor_fixture_m"])
                    stage, stage_start = "sensor_fixture", now
            elif stage == "sensor_fixture":
                move()
                if elapsed >= 2:
                    readings = latest["ranges"]["readings"]
                    near = next(item for item in config["world"]["obstacles"] if item["id"] == "BLOCK_NEAR")
                    expected_front = near["center_m"][0] - near["size_m"][0]/2 - limits["sensor_fixture_m"][0] - config["sensors"]["horizontal_origin_radius_m"]
                    expected_down = position[2] - config["sensors"]["vertical_origin_offset_m"]
                    saved_front = readings["range_000"]["distance_m"]
                    require("range_geometry", all(item["valid"] for item in readings.values()) and
                            abs(saved_front - expected_front) < limits["sensor_tolerance_m"] and
                            abs(readings["range_down"]["distance_m"] - expected_down) < limits["sensor_tolerance_m"],
                            {"front_m": saved_front, "expected_front_m": expected_front,
                             "down_m": readings["range_down"]["distance_m"], "expected_down_m": expected_down,
                             "up_at_limit": readings["range_up"]["at_limit"]})
                    hidden.getField("translation").setSFVec3f([6.0, 0.0, 1.0])
                    stage, stage_start = "occlusion", now
            elif stage == "occlusion":
                move()
                if elapsed >= 0.5:
                    front = latest["ranges"]["readings"]["range_000"]["distance_m"]
                    require("nearest_surface_occlusion", abs(front - saved_front) < limits["sensor_tolerance_m"],
                            {"front_before_m": saved_front, "front_after_hidden_object_moved_m": front})
                    stage, stage_start = "collision", now
            elif stage == "collision":
                move(forward=0.8)
                contacts = drone.getContactPoints(True)
                if contacts:
                    require("physical_collision", position[0] < 1.7, {"contact_count": len(contacts), "position_m": position})
                    reset_world()
                    stage, stage_start = "reset", now
                elif elapsed > limits["collision_timeout_s"]:
                    raise AssertionError("No physical collision detected before deadline")
            elif stage == "reset":
                move()
                if elapsed >= limits["reset_duration_s"]:
                    error = norm([a-b for a,b in zip(position, config["world"]["start_m"])])
                    require("reset", error < limits["hover_position_tolerance_m"] and norm(velocity) < limits["stop_speed_tolerance_m_s"],
                            {"position_error_m": error, "speed_m_s": norm(velocity), "remaining_contacts": len(drone.getContactPoints(True))})
                    require("reset_clears_collision", len(drone.getContactPoints(True)) == 0, {})
                    finish(True)
                    return
    except Exception as error:
        traceback.print_exc()
        if smoke:
            finish(False, error)
        else:
            log.close()
            raise
    finally:
        if not log.closed:
            log.close()
