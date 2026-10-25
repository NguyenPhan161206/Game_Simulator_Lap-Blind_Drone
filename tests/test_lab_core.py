"""Physical mixing, command boundaries and privileged-data isolation checks."""
import ast
from dataclasses import replace
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from blind_drone.contracts.runtime import MotionCommand, VehicleState
from blind_drone.control.manual import keyboard_command
from blind_drone.control.stabilizer import Stabilizer
from blind_drone.world.minimal_lab import controller_config, device_specs, load_config, outputs


class LabCoreTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config()
        self.state = VehicleState(1.0, (-4.0, 0.0, 1.5), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0))

    def physical_resultant(self, speeds):
        vehicle = self.config["vehicle"]
        forces = [vehicle["thrust_coefficient_n_s2"] * speed**2 for speed in speeds]
        locations = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
        arm, ratio = vehicle["arm_offset_m"], vehicle["torque_to_thrust_m"]
        return (sum(forces), sum(y*arm*f for (x,y,s),f in zip(locations,forces)),
                sum(-x*arm*f for (x,y,s),f in zip(locations,forces)),
                sum(s*ratio*f for (x,y,s),f in zip(locations,forces)))

    def test_hover_balances_gravity_without_rotational_torque(self):
        speeds = Stabilizer(self.config).step(self.state, MotionCommand(), 0.016)
        thrust, tx, ty, tz = self.physical_resultant(speeds)
        self.assertAlmostEqual(thrust, self.config["vehicle"]["mass_kg"] * self.config["world"]["gravity_m_s2"])
        for torque in (tx, ty, tz):
            self.assertAlmostEqual(torque, 0.0)

    def test_roll_pitch_errors_generate_opposing_torque(self):
        for attitude, component in [((0.1,0,0),1), ((0,0.1,0),2)]:
            state = replace(self.state, attitude_rad=attitude)
            result = self.physical_resultant(Stabilizer(self.config).step(state, MotionCommand(), 0.016))
            self.assertLess(result[component], 0)

    def test_positive_yaw_command_generates_positive_world_torque(self):
        result = self.physical_resultant(Stabilizer(self.config).step(self.state, MotionCommand(yaw_rate_rad_s=0.5), 0.016))
        self.assertGreater(result[3], 0)

    def test_world_velocity_is_rotated_into_body_frame(self):
        state = replace(self.state, attitude_rad=(0,0,math.pi/2), velocity_m_s=(0,0.8,0))
        result = self.physical_resultant(Stabilizer(self.config).step(state, MotionCommand(forward_m_s=0.8), 0.016))
        self.assertAlmostEqual(result[1], 0, places=8)
        self.assertAlmostEqual(result[2], 0, places=8)

    def test_invalid_state_fails_before_motor_output(self):
        with self.assertRaises(ValueError):
            Stabilizer(self.config).step(replace(self.state, position_m=(0,0,float("nan"))), MotionCommand(), 0.016)

    def test_operator_cannot_supply_hidden_world_fields(self):
        packet = {"kind":"motion", "forward_m_s":0, "left_m_s":0, "up_m_s":0, "yaw_rate_rad_s":0, "obstacles":[]}
        with self.assertRaises(ValueError):
            MotionCommand.from_operator(packet, self.config["vehicle"])

    def test_operator_rejects_nonfinite_and_clamps_velocity(self):
        packet = {"kind":"motion", "forward_m_s":100, "left_m_s":0, "up_m_s":0, "yaw_rate_rad_s":0}
        self.assertEqual(MotionCommand.from_operator(packet, self.config["vehicle"]).forward_m_s, 0.8)
        packet["forward_m_s"] = float("inf")
        with self.assertRaises(ValueError):
            MotionCommand.from_operator(packet, self.config["vehicle"])

    def test_releasing_keys_brakes_and_space_overrides_motion(self):
        limits = self.config["vehicle"]
        self.assertEqual(keyboard_command(set(), limits), MotionCommand())
        self.assertEqual(keyboard_command({ord("W"),ord(" ")}, limits), MotionCommand())
        self.assertGreater(keyboard_command({ord("W")}, limits).forward_m_s, 0)

    def test_drone_configuration_contains_no_layout_or_fixture(self):
        public = controller_config(self.config)
        self.assertEqual(set(public["world"]), {"gravity_m_s2"})
        self.assertNotIn("smoke", public)
        self.assertNotIn("start_m", public)
        self.assertEqual(set(public), {"vehicle", "control", "sensors", "world", "sensor_period_ms", "goal_m", "sensor_names"})

    def test_ten_nonimage_measurements_and_no_remote_assets(self):
        self.assertEqual(len(device_specs(self.config)), 10)
        for text in outputs(self.config).values():
            self.assertNotIn("Camera {", text)
            self.assertNotIn("RangeFinder {", text)
            self.assertNotIn("https://", text)
            self.assertNotIn("webots://", text)

    def test_drone_adapter_has_no_supervisor_or_scene_calls(self):
        tree = ast.parse((ROOT / "src/blind_drone/adapters/webots/drone.py").read_text())
        banned = {"Supervisor", "getFromDef", "getRoot", "getSelf", "getPosition", "getField", "setSFVec3f", "load_config", "open", "read_text"}
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        names |= {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        names |= {alias.name for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) for alias in node.names}
        self.assertFalse(names & banned, names & banned)


if __name__ == "__main__":
    unittest.main()
