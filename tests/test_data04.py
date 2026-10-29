"""Guarded retention semantics for the DATA-04 development candidate."""
import ast
from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'versions/navigation_v4'), str(ROOT / 'versions/data_history_v1')]
from blind_drone.experiments.protocol_v2 import load_v2_config
from blind_drone.navigation.observed import MissionV2
from blind_drone.sensors.acquisition import RANGE_NAMES, SampledObservation
from blind_drone.contracts.runtime import VehicleState
from blind_drone_data04.navigation import OccupiedOnlyAcquisitionGrid, OccupiedOnlyNavigator


def observation(time=0., x=.125):
    pose = VehicleState(time, (x, .025, 1.5), (0., 0., 0.), (0., 0., 0.), (0., 0., 0.))
    readings = {name: {'distance_m': 8., 'valid': True, 'at_limit': True} for name in RANGE_NAMES}
    sample = {'sample_time_s': time, 'frame': 'body_FLU', 'acquisition_state': pose, 'readings': readings}
    return SampledObservation.construct(pose, sample)


class RetentionTests(unittest.TestCase):
    def test_old_free_cells_expire_but_occupied_hits_and_inflation_persist(self):
        config = load_v2_config()
        grid = OccupiedOnlyAcquisitionGrid(config['navigation_v2'], config['vehicle']['body_size_m'], .33)
        grid.origin = (.125, .025)
        grid.free = {(0, 0), (1, 0)}
        grid.occupied = {(2, 2)}
        grid.blocked = {(x, y) for x in range(3) for y in range(3)}
        before_blocked = set(grid.blocked)
        grid.last_sample = 0.
        grid.update(observation(.032, 10.125))
        self.assertNotIn((0, 0), grid.free)
        self.assertNotIn((1, 0), grid.free)
        self.assertIn((2, 2), grid.occupied)
        self.assertTrue(before_blocked <= grid.blocked)

    def test_expired_hit_and_its_inflation_are_removed_at_ttl(self):
        config = load_v2_config()
        grid = OccupiedOnlyAcquisitionGrid(config['navigation_v2'], config['vehicle']['body_size_m'], .33)
        grid.origin = (.125, .025)
        cell = (2, 2)
        grid.occupied = {cell}
        grid.occupied_hit_times = {cell: 0.0}
        grid.blocked = {(cell[0] + dx, cell[1] + dy) for dx, dy in grid.offsets}
        grid.last_sample = 0.0
        grid.update(observation(10.0, .125))
        self.assertNotIn(cell, grid.occupied)
        self.assertFalse(grid.blocked.intersection({(cell[0] + dx, cell[1] + dy) for dx, dy in grid.offsets}))

    def test_reused_packet_does_not_expire_free_evidence(self):
        config = load_v2_config()
        grid = OccupiedOnlyAcquisitionGrid(config['navigation_v2'], config['vehicle']['body_size_m'], .33)
        first = observation()
        grid.update(first)
        previous = set(grid.free)
        reused = replace(first, state=replace(first.state, time_s=.016))
        grid.update(reused)
        self.assertEqual(grid.free, previous)

    def test_budget_counts_separate_occupied_free_and_inflation_entries(self):
        config = load_v2_config()
        config['navigation_v2']['max_cells'] = 10
        grid = OccupiedOnlyAcquisitionGrid(config['navigation_v2'], config['vehicle']['body_size_m'], .33)
        grid.origin = (.125, .025)
        grid.occupied = {(0, 0)}
        grid.blocked = {(0, 0)}
        grid.free = {(1, 0)}
        grid.params['max_cells'] = 3
        grid.retain((2, 0), False)
        self.assertTrue(grid.exhausted)
        self.assertEqual(grid.occupied, {(0, 0)})
        self.assertEqual(grid.free, {(1, 0)})

    def test_navigator_stops_when_route_is_not_supported_by_current_free_evidence(self):
        nav = OccupiedOnlyNavigator(MissionV2((5., 0., 1.5), 'mapped'), load_v2_config())
        self.assertIsInstance(nav.grid, OccupiedOnlyAcquisitionGrid)
        nav.started = -3.
        nav.grid.update = lambda observation: None
        nav.grid.plan = lambda start, goal: []
        nav.grid.free.clear()
        command = nav.step(observation())
        self.assertEqual((command.forward_m_s, command.left_m_s), (0., 0.))
        self.assertEqual(nav.status, 'scan_no_observed_route')

    def test_candidate_has_no_privileged_policy_imports(self):
        tree = ast.parse((ROOT / 'versions/data_history_v1/blind_drone_data04/navigation.py').read_text())
        imports = [node.module or '' for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        self.assertFalse(any(name.startswith(('blind_drone.world', 'blind_drone.evaluation')) for name in imports))


if __name__ == '__main__':
    unittest.main()
