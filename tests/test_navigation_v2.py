"""Observation-only mapping/planning/command tests; not simulator flight evidence."""
import ast
from dataclasses import replace
import math
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from blind_drone.contracts.navigation import NavigationObservation,RangeReading
from blind_drone.contracts.runtime import MotionCommand,VehicleState
from blind_drone.experiments.protocol import verify_lock
from blind_drone.experiments.protocol_v2 import build_manifest,load_v2_config,select_suite_v2
from blind_drone.navigation.observed import MissionV2,ObservedNavigator
from blind_drone.observation.range_grid import RangeGrid,rotate_rpy


class NavigationV2Tests(unittest.TestCase):
    def setUp(self):
        self.config=load_v2_config()
        state=VehicleState(1,(0,0,1.5),(0,0,0),(0,0,0),(0,0,0))
        names=[f"range_{a:03d}" for a in range(0,360,45)]+["range_up","range_down"]
        self.obs=NavigationObservation(state,1,"body_FLU",tuple(RangeReading(n,8,True,True) for n in names))

    def grid(self,**changes):
        p={**self.config["navigation_v2"],**changes}
        return RangeGrid(p,self.config["vehicle"]["body_size_m"],.33)

    def test_full_rpy_transform_preserves_length_and_frame(self):
        v=rotate_rpy((1,0,0),(0,0,math.pi/2))
        self.assertAlmostEqual(v[0],0);self.assertAlmostEqual(v[1],1)
        v=rotate_rpy((1,0,0),(0,math.pi/2,0))
        self.assertAlmostEqual(v[2],-1)
        v=rotate_rpy((.3,.4,.5),(.2,.3,.4))
        self.assertAlmostEqual(sum(x*x for x in v),.5)

    def test_hit_endpoint_uses_sensor_origin_and_measured_yaw(self):
        obs=replace(self.obs,state=replace(self.obs.state,attitude_rad=(0,0,math.pi/2)),
                    ranges=tuple(replace(r,distance_m=1,at_limit=False) if r.name=="range_000" else r for r in self.obs.ranges))
        grid=self.grid();grid.update(obs)
        self.assertIn(grid.cell((0,1.33)),grid.occupied)
        self.assertEqual(grid.updates,1);grid.update(obs);self.assertEqual(grid.updates,1)

    def test_at_limit_creates_no_false_wall(self):
        grid=self.grid();grid.update(self.obs)
        self.assertFalse(grid.occupied);self.assertTrue(grid.free)
        self.assertNotIn(grid.cell((9,0)),grid.free)

    def test_budget_stops_new_storage_and_reset_has_no_old_map(self):
        grid=self.grid(max_cells=10);grid.update(self.obs)
        self.assertTrue(grid.exhausted)
        self.assertLessEqual(len(grid.free)+len(grid.occupied),10)
        self.assertFalse(self.grid().occupied)

    def test_unknown_cells_cannot_be_executed_as_observed_free(self):
        grid=self.grid();grid.origin=(0,0)
        grid.free.add(grid.cell((0,0)))
        self.assertFalse(grid.segment_ok((0,0),(1,0),True))
        self.assertTrue(grid.segment_ok((0,0),(1,0),False))

    def test_guard_removes_closing_velocity_but_allows_retreat(self):
        grid=self.grid();grid.origin=(0,0)
        grid.retain(grid.cell((.7,0)),True)
        vx,vy,changed=grid.guard((0,0),.4,0)
        self.assertTrue(changed);self.assertLess(vx,.1)
        vx,vy,changed=grid.guard((0,0),-.4,0)
        self.assertFalse(changed);self.assertEqual(vx,-.4)

    def test_online_planner_can_route_back_out_of_u_in_known_grid(self):
        grid=self.grid();grid.origin=(0,0)
        for x in range(-20,21):
            for y in range(-20,21):grid.free.add((x,y))
        # Unit fixture for planner only; runtime fills these cells from rays.
        grid.blocked={(x,8) for x in range(-8,9)}|{(x,-8) for x in range(-8,9)}|{(8,y) for y in range(-8,9)}
        path=grid.plan((0,0),(4,0))
        self.assertTrue(path)
        self.assertTrue(any(p[0]< -2 for p in path))
        for a,b in zip(path,path[1:]):self.assertTrue(grid.segment_ok(a,b))

    def test_invalid_stale_samples_return_zero_before_mapping(self):
        nav=ObservedNavigator(MissionV2((5,0,1.5),"mapped"),self.config)
        self.assertEqual(nav.step(replace(self.obs,sample_time_s=0)),MotionCommand())
        self.assertEqual(nav.grid.updates,0)

    def test_guarded_comparator_retains_reactive_detour_logic(self):
        self.config["navigation_v2"]["initial_scan_s"]=0
        nav=ObservedNavigator(MissionV2((5,0,1.5),"guarded"),self.config)
        obs=replace(self.obs,ranges=tuple(replace(r,distance_m=1,at_limit=False) if r.name=="range_000" else r for r in self.obs.ranges))
        command=nav.step(obs)
        self.assertGreater(command.left_m_s,.1)

    def test_mission_rejects_scene_fields_and_bad_values(self):
        valid={"kind":"mission","goal_m":[5,0,1.5],"policy":"mapped"}
        self.assertEqual(MissionV2.from_packet(valid).policy,"mapped")
        for packet in [{**valid,"obstacles":[]},{**valid,"policy":"oracle"},{**valid,"goal_m":[float("nan"),0,1]},[]]:
            with self.assertRaises(ValueError):MissionV2.from_packet(packet)

    def test_new_navigation_never_imports_privileged_modules(self):
        for name in ("observation/range_grid.py","navigation/observed.py"):
            tree=ast.parse((ROOT/"src/blind_drone"/name).read_text())
            imports=[n.module or "" for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
            imports += [a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
            self.assertFalse(any(any(s in module.split('.') for s in ('world','evaluation','adapters','controller','os','pathlib')) for module in imports))

    def test_v1_protocol_unchanged_and_fresh_v2_splits_disjoint(self):
        self.assertTrue(verify_lock())
        cases=build_manifest()["cases"]
        self.assertEqual(len(cases),36)
        self.assertEqual(len({c["geometry_sha256"] for c in cases}),36)


if __name__=="__main__":unittest.main()
