"""Behavior, scoring and data-boundary checks independent of Webots."""
import ast
from dataclasses import replace
import math
from pathlib import Path
import sys
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from blind_drone.contracts.navigation import NavigationMission, NavigationObservation, RangeReading
from blind_drone.contracts.runtime import MotionCommand, VehicleState
from blind_drone.evaluation.episode import EpisodeEvaluator, summarize
from blind_drone.navigation.baseline import BaselineNavigator
from blind_drone.world.minimal_lab import controller_config, load_config


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.config = controller_config(load_config())
        state = VehicleState(1.0, (0,0,1.5), (0,0,0), (0,0,0), (0,0,0))
        names = [f"range_{a:03d}" for a in range(0,360,45)] + ["range_up", "range_down"]
        self.obs = NavigationObservation(state, 0.984, "body_FLU", tuple(RangeReading(n,8.0,True,True) for n in names))

    def navigator(self, policy="reactive", goal=(5,0,1.5)):
        return BaselineNavigator(NavigationMission(goal,policy), self.config)

    def with_front(self, distance):
        return replace(self.obs, ranges=tuple(replace(r, distance_m=distance, at_limit=False) if r.name == "range_000" else r for r in self.obs.ranges))

    def test_clear_space_goes_toward_goal_with_speed_cap(self):
        command = self.navigator().step(self.obs)
        self.assertGreater(command.forward_m_s,0)
        self.assertEqual(command.left_m_s,0)
        self.assertLessEqual(math.hypot(command.forward_m_s,command.left_m_s),0.55)

    def test_goal_enu_is_rotated_to_flu(self):
        obs = replace(self.obs, state=replace(self.obs.state,attitude_rad=(0,0,math.pi/2)))
        command = self.navigator().step(obs)
        self.assertAlmostEqual(command.forward_m_s,0,places=8)
        self.assertLess(command.left_m_s,0)

    def test_direct_control_ignores_block_while_reactive_turns(self):
        obs = self.with_front(1.0)
        direct = self.navigator("direct").step(obs)
        reactive = self.navigator().step(obs)
        self.assertEqual(direct.left_m_s,0)
        self.assertGreater(reactive.left_m_s,0.4)
        self.assertLess(reactive.forward_m_s,direct.forward_m_s)

    def test_close_surface_produces_no_velocity_into_it(self):
        command = self.navigator().step(self.with_front(0.2))
        self.assertLessEqual(command.forward_m_s,0)

    def test_stale_future_wrong_frame_and_incomplete_samples_brake(self):
        for obs in [replace(self.obs,sample_time_s=0.0), replace(self.obs,sample_time_s=1.1),
                    replace(self.obs,frame="world_ENU"), replace(self.obs,ranges=self.obs.ranges[:-1])]:
            self.assertEqual(self.navigator().step(obs),MotionCommand())

    def test_invalid_nonfinite_and_inconsistent_readings_brake(self):
        for reading in [RangeReading("range_000",None,False,False), RangeReading("range_000",float("nan"),True,False),
                        RangeReading("range_000",1,True,True)]:
            obs = replace(self.obs,ranges=(reading,*self.obs.ranges[1:]))
            self.assertEqual(self.navigator().step(obs),MotionCommand())

    def test_goal_position_requests_zero_motion(self):
        self.assertEqual(self.navigator(goal=(0,0,1.5)).step(self.obs),MotionCommand())

    def test_mission_rejects_hidden_fields_bad_policy_and_coordinates(self):
        valid = {"kind":"mission","goal_m":[5,0,1.5],"policy":"reactive"}
        self.assertEqual(NavigationMission.from_packet(valid).goal_m,(5,0,1.5))
        for packet in [{**valid,"obstacles":[]},{**valid,"policy":"oracle"},
                       {**valid,"goal_m":[True,0,1]},{**valid,"goal_m":[float("nan"),0,1]},[],{}]:
            with self.assertRaises(ValueError):
                NavigationMission.from_packet(packet)

    def test_no_scene_files_or_evaluator_dependencies_in_navigation(self):
        for relative in ("src/blind_drone/navigation/baseline.py", "src/blind_drone/contracts/navigation.py"):
            tree = ast.parse((ROOT/relative).read_text())
            imports = [n.module or "" for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
            imports += [a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
            self.assertFalse(any(any(s in name.split(".") for s in ("world","evaluation","adapters","controller","pathlib","os")) for name in imports))


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.config = tomllib.loads((ROOT/"configs/navigation_v1.toml").read_text())["evaluation"]

    def evaluator(self, **changes):
        return EpisodeEvaluator((0,0,1.5),{**self.config,**changes})

    def test_high_speed_flythrough_does_not_succeed(self):
        ev = self.evaluator()
        self.assertIsNone(ev.update(0,(0,0,1.5),(1,0,0),0))
        self.assertIsNone(ev.update(1,(0,0,1.5),(1,0,0),0))
        self.assertEqual(ev.update(65,(1,0,1.5),(0,0,0),0)["outcome"],"timeout")

    def test_dwell_must_be_continuous_and_latch_terminal_result(self):
        ev = self.evaluator()
        for t,pos in [(0,(0,0,1.5)),(.8,(1,0,1.5)),(1,(0,0,1.5)),(1.99,(0,0,1.5))]:
            self.assertIsNone(ev.update(t,pos,(0,0,0),0))
        result = ev.update(2,(0,0,1.5),(0,0,0),0)
        self.assertEqual(result["outcome"],"success")
        self.assertEqual(ev.update(3,(10,0,0),(0,0,0),1),result)

    def test_collision_and_bounds_override_goal_success(self):
        ev = self.evaluator()
        ev.update(0,(0,0,1.5),(0,0,0),0)
        self.assertEqual(ev.update(1,(0,0,1.5),(0,0,0),2)["outcome"],"collision")
        ev = self.evaluator(position_bounds_max_m=[-0.1,9,5])
        self.assertEqual(ev.update(0,(0,0,1.5),(0,0,0),0)["outcome"],"out_of_bounds")

    def test_success_after_deadline_is_timeout(self):
        ev = self.evaluator(timeout_s=1.0)
        ev.update(.5,(0,0,1.5),(0,0,0),0)
        self.assertEqual(ev.update(1.6,(0,0,1.5),(0,0,0),0)["outcome"],"timeout")

    def test_path_length_counts_failure_and_uses_three_dimensions(self):
        ev = self.evaluator()
        ev.update(0,(0,0,1.5),(0,0,0),0)
        result = ev.update(1,(3,4,1.5),(0,0,0),1)
        self.assertEqual(result["path_length_m"],5)
        with self.assertRaises(ValueError):
            self.evaluator().update(0,(float("nan"),0,0),(0,0,0),0)

    def test_time_must_increase(self):
        ev = self.evaluator()
        ev.update(0,(1,0,1.5),(0,0,0),0)
        with self.assertRaises(ValueError):
            ev.update(0,(1,0,1.5),(0,0,0),0)

    def test_summary_keeps_failures_and_negative_controls_separate(self):
        def episode(feasible,outcome,time):
            return {"policy":"reactive","feasible":feasible,"outcome":outcome,"elapsed_s":time,"path_length_m":time}
        report = summarize([episode(True,"success",10),episode(True,"timeout",65),episode(False,"collision",3)])
        self.assertEqual(report["reactive"]["feasible"]["success_rate"],0.5)
        self.assertEqual(report["reactive"]["feasible"]["success_only_mean_time_s"],10)
        self.assertEqual(report["reactive"]["negative_control"]["episodes"],1)


if __name__ == "__main__":
    unittest.main()
