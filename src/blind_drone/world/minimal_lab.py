"""Generate an offline, primitive-only Webots world and quadrotor model."""
from __future__ import annotations

import json
from math import acos, cos, pi, sin, sqrt
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "configs/lab_v1.toml"
PROTO = ROOT / "simulation/webots/protos/BlindDrone.proto"
WORLD = ROOT / "simulation/webots/worlds/minimal_lab.wbt"


def load_config(path=CONFIG):
    config = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    if config["runtime_camera_enabled"] or config["runtime_privileged_state_enabled"]:
        raise ValueError("Runtime observation restrictions violated")
    if config["sensor_period_ms"] % config["basic_time_step_ms"]:
        raise ValueError("Sensor period must be a multiple of physics step")
    v = config["vehicle"]
    if v["mass_kg"] <= 0 or min(v["inertia_kg_m2"]) <= 0:
        raise ValueError("Mass and inertia must be positive")
    if 4 * v["thrust_coefficient_n_s2"] * v["motor_max_rad_s"] ** 2 <= v["mass_kg"] * config["world"]["gravity_m_s2"]:
        raise ValueError("Insufficient maximum thrust")
    return config


def vector(values):
    return " ".join(f"{value:.10g}" for value in values)


def appearance(color):
    return f"PBRAppearance {{ baseColor {color} roughness 0.75 metalness 0 }}"


def box(def_name, center, size, color):
    return f'''DEF {def_name} Solid {{
  translation {vector(center)}
  children [ Shape {{ appearance {appearance(color)} geometry Box {{ size {vector(size)} }} }} ]
  name "{def_name}"
  boundingObject Box {{ size {vector(size)} }}
}}'''


def device_specs(config):
    s = config["sensors"]
    result = []
    for degree in s["horizontal_directions_deg"]:
        angle = degree * pi / 180
        radius = s["horizontal_origin_radius_m"]
        result.append((f"range_{int(degree):03d}", [radius * cos(angle), radius * sin(angle), 0], [0, 0, 1, angle]))
    offset = s["vertical_origin_offset_m"]
    result += [("range_up", [0, 0, offset], [0, -1, 0, pi / 2]),
               ("range_down", [0, 0, -offset], [0, 1, 0, pi / 2])]
    return result


def controller_config(config):
    """Explicit whitelist: no world layout, fixtures or reference paths."""
    return {
        "vehicle": config["vehicle"], "control": config["control"],
        "sensors": config["sensors"],
        "world": {"gravity_m_s2": config["world"]["gravity_m_s2"]},
        "sensor_period_ms": config["sensor_period_ms"],
        "goal_m": config["world"]["goal_m"],
        "sensor_names": [name for name, _, _ in device_specs(config)],
    }


def proto_text(config):
    v, s = config["vehicle"], config["sensors"]
    children = [f'Shape {{ appearance {appearance("0.15 0.55 0.8")} geometry Box {{ size {vector(v["body_size_m"])} }} }}',
                f'Pose {{ translation 0.37 0 0 children [ Shape {{ appearance {appearance("1 0.6 0.05")} geometry Sphere {{ radius 0.06 }} }} ] }}',
                'GPS { name "gps" }', 'Gyro { name "gyro" }',
                'InertialUnit { name "imu" }',
                'Receiver { name "operator" channel 1 }',
                'Emitter { name "telemetry" channel 2 }']
    for index, (xs, ys, spin) in enumerate(((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1))):
        x, y = xs * v["arm_offset_m"], ys * v["arm_offset_m"]
        # Webots applies -Q about shaftAxis; choose q1=-spin*k*ratio.
        q1 = -spin * v["thrust_coefficient_n_s2"] * v["torque_to_thrust_m"]
        children += [f'''Propeller {{
      shaftAxis 0 0 1
      centerOfThrust {x} {y} 0
      thrustConstants {v["thrust_coefficient_n_s2"]} 0
      torqueConstants {q1} 0
      device RotationalMotor {{ name "motor_{index}" maxVelocity {v["motor_max_rad_s"]} maxTorque 10 }}
    }}''', f'''Pose {{ translation {x} {y} 0.03 rotation 1 0 0 {pi / 2}
      children [ Shape {{ appearance {appearance("0.12 0.15 0.2")} geometry Cylinder {{ radius 0.14 height 0.01 }} }} ]
    }}''']
    for name, origin, rotation in device_specs(config):
        children.append(f'''DistanceSensor {{
      translation {vector(origin)}
      rotation {vector(rotation)}
      name "{name}"
      type "generic"
      numberOfRays 1
      aperture 0.001
      lookupTable [ 0 0 {s["noise_fraction"]}, {s["range_max_m"]} {s["range_max_m"]} {s["noise_fraction"]} ]
    }}''')
    return f'''#VRML_SIM R2025a utf8
# Generated from configs/lab_v1.toml by tools/build_lab.py. Original primitive geometry.
PROTO BlindDrone [
  field SFVec3f translation 0 0 1.5
  field SFRotation rotation 0 0 1 0
  field SFString customData ""
] {{
  Robot {{
    translation IS translation
    rotation IS rotation
    customData IS customData
    name "blind_drone"
    supervisor FALSE
    controller "drone_controller"
    children [
    {chr(10).join(children)}
    ]
    boundingObject Box {{ size {vector(v["body_size_m"])} }}
    physics Physics {{
      density -1
      mass {v["mass_kg"]}
      centerOfMass [ 0 0 0 ]
      inertiaMatrix [ {vector(v["inertia_kg_m2"])}, 0 0 0 ]
    }}
  }}
}}
'''


def view_rotation(position, target):
    def norm(a):
        length = sqrt(sum(x * x for x in a))
        return [x / length for x in a]
    def cross(a, b):
        return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
    forward = norm([b - a for a, b in zip(position, target)])
    right = norm(cross(forward, [0, 0, 1]))
    up = cross(right, forward)
    m = [[right[i], up[i], -forward[i]] for i in range(3)]
    angle = acos(max(-1, min(1, (sum(m[i][i] for i in range(3)) - 1) / 2)))
    axis = norm([m[2][1]-m[1][2], m[0][2]-m[2][0], m[1][0]-m[0][1]])
    return [*axis, angle]


def world_text(config):
    w = config["world"]
    sx, sy = w["size_m"]
    thickness, height = w["wall_thickness_m"], w["wall_height_m"]
    solids = [box("FLOOR", [0, 0, -w["floor_thickness_m"]/2], [sx, sy, w["floor_thickness_m"]], "0.25 0.3 0.36")]
    for name, center, size in [
        ("WALL_E", [sx/2, 0, height/2], [thickness, sy, height]),
        ("WALL_W", [-sx/2, 0, height/2], [thickness, sy, height]),
        ("WALL_N", [0, sy/2, height/2], [sx, thickness, height]),
        ("WALL_S", [0, -sy/2, height/2], [sx, thickness, height])]:
        solids.append(box(name, center, size, "0.32 0.4 0.46"))
    for obstacle in w["obstacles"]:
        solids.append(box(obstacle["id"], obstacle["center_m"], obstacle["size_m"], "0.85 0.33 0.18"))
    custom = json.dumps(json.dumps(controller_config(config), separators=(",", ":")))
    return f'''#VRML_SIM R2025a utf8
# Generated from configs/lab_v1.toml; no external runtime assets.
EXTERNPROTO "../protos/BlindDrone.proto"
WorldInfo {{
  title "Blind Drone Lab — minimal environment v1"
  basicTimeStep {config["basic_time_step_ms"]}
  coordinateSystem "ENU"
  gravity {w["gravity_m_s2"]}
  randomSeed 11
}}
Viewpoint {{ position 12 -16 14 orientation {vector(view_rotation([12,-16,14], [0,0,1]))} }}
Background {{ skyColor [ 0.08 0.11 0.16 ] }}
DirectionalLight {{ direction -0.4 -0.5 -1 ambientIntensity 0.6 intensity 1 castShadows TRUE }}
{chr(10).join(solids)}
DEF GOAL Pose {{
  translation {vector(w["goal_m"])}
  children [ Shape {{ appearance PBRAppearance {{ baseColor 0.1 0.9 0.35 transparency 0.55 roughness 1 metalness 0 }} geometry Sphere {{ radius {w["goal_radius_m"]} }} }} ]
}}
DEF DRONE BlindDrone {{ translation {vector(w["start_m"])} customData {custom} }}
DEF LAB_SUPERVISOR Robot {{
  supervisor TRUE
  controller "lab_supervisor"
  children [ Emitter {{ name "operator" channel 1 }} Receiver {{ name "telemetry" channel 2 }} ]
}}
'''


def outputs(config):
    return {PROTO: proto_text(config), WORLD: world_text(config)}
