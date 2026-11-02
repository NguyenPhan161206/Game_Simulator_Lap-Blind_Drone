"""Behavioral regressions for free-history expiration and fair accounting."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'versions/navigation_v4'),
               str(ROOT/'versions/initialization_aa_v1'), str(ROOT/'versions/retention_cold_v1')]
from blind_drone.contracts.runtime import VehicleState
from blind_drone.experiments.protocol_v2 import load_v2_config
from blind_drone.navigation.cadence import AcquisitionGrid
from blind_drone.navigation.observed import MissionV2
from blind_drone.sensors.acquisition import SampledObservation
from blind_drone_retention.audit import frontier, summarize
from blind_drone_retention.navigation import RetentionGrid, RetentionNavigator
from blind_drone_retention.protocol import execution_arms, generated_outputs, load_spec, schedule, select_cases


class RetentionColdTests(unittest.TestCase):
    def grid(self, ttl=2., budget=16000):
        config = load_v2_config()
        params = deepcopy(config['navigation_v2']); params['max_cells'] = budget
        grid = RetentionGrid(params, config['vehicle']['body_size_m'],
                             config['sensors']['horizontal_origin_radius_m'], ttl)
        grid.origin = (0., 0.)
        return grid

    def observation(self, time, position=(0., 0., 1.5)):
        state = VehicleState(time, position, (0., 0., 0.), (0., 0., 0.), (0., 0., 0.))
        # Grid tests intentionally have no rays; no navigator may move on this schema.
        return SampledObservation(state, time, 'body_FLU', (), state)

    def test_expiration_boundary_refresh_and_duplicate_reads(self):
        grid = self.grid()
        grid.update(self.observation(1.))
        old = (8, 8)
        grid.retain(old, False)
        grid.update(self.observation(3.))
        self.assertIn(old, grid.free)  # inclusive window
        snapshot = grid.snapshot()
        grid.update(replace(self.observation(3.), state=self.observation(8.).state))
        self.assertEqual(snapshot, grid.snapshot())  # current tick cannot refresh sample age
        grid.update(self.observation(3.032))
        self.assertNotIn(old, grid.free)
        self.assertNotIn(old, grid.free_seen)
        self.assertEqual(grid.expired_free, 1)
        grid.retain(old, False)
        grid.update(self.observation(4.))
        grid.retain(old, False)  # a new measured free ray refreshes last-seen
        grid.update(self.observation(5.1))
        self.assertIn(old, grid.free)

    def test_occupied_and_inflation_never_expire_or_become_free(self):
        grid = self.grid()
        grid.update(self.observation(0.))
        cell = (4, 4)
        grid.retain(cell, False)
        grid.retain(cell, True)
        occupied, blocked = grid.occupied.copy(), grid.blocked.copy()
        self.assertNotIn(cell, grid.free_seen)
        grid.update(self.observation(100.))
        grid.retain(cell, False)
        self.assertEqual(grid.occupied, occupied)
        self.assertEqual(grid.blocked, blocked)
        self.assertNotIn(cell, grid.free)

    def test_reference_grid_matches_v4_cells_until_common_budget(self):
        config = load_v2_config()
        reference = self.grid(None)
        legacy = AcquisitionGrid(config['navigation_v2'], config['vehicle']['body_size_m'],
                                 config['sensors']['horizontal_origin_radius_m'])
        legacy.origin = reference.origin
        for stamp in (0., .032, 10.):
            observation = self.observation(stamp)
            reference.update(observation); legacy.update(observation)
            for cell, hit in (((2, 2), False), ((7, 7), True), ((7, 7), False)):
                reference.retain(cell, hit); legacy.retain(cell, hit)
            for name in ('free', 'occupied', 'blocked'):
                self.assertEqual(getattr(reference, name), getattr(legacy, name))
        self.assertEqual(reference.expired_free, 0)

    def test_budget_counts_timestamp_and_inflation_entries_and_is_sticky(self):
        for ttl in (None, 2.):
            grid = self.grid(ttl, 4)
            grid.update(self.observation(0.))  # free centre + timestamp = 2
            grid.retain((1, 1), False)
            self.assertEqual(grid.entries(), 4)
            grid.retain((5, 5), True)  # inflation must be reserved atomically
            self.assertTrue(grid.exhausted)
            self.assertNotIn((5, 5), grid.occupied)
            self.assertEqual(grid.entries(), 4)
            grid.update(self.observation(10.))
            grid.retain((6, 6), False)
            self.assertTrue(grid.exhausted)
            self.assertNotIn((6, 6), grid.free)

    def test_backward_or_nonfinite_sample_rejected(self):
        for stamp in (float('nan'), float('inf'), -.032):
            grid = self.grid(); grid.update(self.observation(0.))
            with self.assertRaises(ValueError):
                grid.update(self.observation(stamp))

    def test_invalid_observation_stops_with_both_retention_modes(self):
        for ttl in (None, 2.):
            nav = RetentionNavigator(MissionV2((5., 0., 1.5), 'mapped'), load_v2_config(), ttl)
            command = nav.step(self.observation(0.))
            self.assertEqual(command.forward_m_s, 0.)
            self.assertEqual(command.left_m_s, 0.)
            self.assertEqual(nav.status, 'invalid_or_stale_observation')

    def test_352_cold_process_matrix_reverses_arm_order_and_rejects_heldout(self):
        _, cases = generated_outputs()
        rows = list(schedule(cases))
        self.assertEqual(len(rows), 352)
        self.assertEqual(sum(c['feasible'] for c in cases), 74)
        self.assertEqual(len({(c['id'], mode, rep, arm) for c, mode, rep, arm in rows}), 352)
        for c in cases:
            arms = [arm for case, _, _, arm in rows if case['id'] == c['id']]
            self.assertEqual(arms[:2], arms[2:][::-1])
        for split in ('validation', 'test'):
            with self.assertRaisesRegex(ValueError, 'development only'):
                select_cases(split)
        for repeat, mode, arm in ((True, 'cold', 'reference'), (0, 'warm', 'reference'), (0, 'cold', None)):
            with self.assertRaises(ValueError):
                execution_arms('case', repeat, mode, arm)
        with self.assertRaisesRegex(ValueError, 'Incomplete/duplicate'):
            summarize([], cases, load_spec())

    def test_frontier_preserves_quality_cost_tradeoff_and_equal_points(self):
        a = {'feasible_case_success': 74, 'mean_free_entries': 1000., 'cpu_mean_ms': 1., 'rss_peak_mean_mib': 30.}
        b = a | {'feasible_case_success': 67, 'mean_free_entries': 500.}
        c = a | {'mean_free_entries': 2000.}
        self.assertEqual(set(frontier({'a': a, 'b': b, 'c': c, 'd': a.copy()})), {'a', 'b', 'd'})

    def test_completed_negative_study_cannot_qualify_by_resource_savings(self):
        rows = []
        cases = [{'id': 'feasible', 'feasible': True}, {'id': 'negative', 'feasible': False}]
        for case, mode, repeat, arm in schedule(cases):
            success = case['feasible'] and arm == 'reference'
            cpu = {'decisions': 10, 'mean_ms': 1., 'p95_ms': 2., 'max_ms': 3., 'over_16_ms': 0}
            episode = {'case_id': case['id'], 'repeat': repeat, 'arm': arm, 'feasible': case['feasible'],
                       'outcome': 'success' if success else 'timeout', 'elapsed_s': 20. if success else 90.,
                       'path_length_m': 10., 'cpu': cpu, 'control_cpu': cpu,
                       'resources': {'rss_peak_mib': 30.}, 'files_bytes': {'trace': 1000},
                       'acquisition': {'scored': {'payload_bytes_per_s': 3000.}}}
            for key in ('initial_position_m', 'initial_velocity_m_s', 'initial_yaw_rad',
                        'measured_initial', 'initialization', 'epoch_s', 'score_start_s'):
                episode[key] = 0.
            audit = {'mean_free_entries': 1000. if arm == 'reference' else 100.,
                     'mean_map_entries': 2000., 'peak_map_entries': 3000,
                     'expired_free': 0, 'budget_exhausted': False,
                     'raw_audit_passed': True, 'commands_checked': 10}
            rows.append({'episode': episode, 'mode': mode, 'audit': audit})
        result = summarize(rows, cases, load_spec())
        self.assertTrue(result['gates']['all_raw_audits_passed'])
        self.assertTrue(result['gates']['mean_free_ratio'])
        self.assertFalse(result['gates']['candidate_task_quality'])
        self.assertFalse(result['gates']['no_lost_reference_cases'])
        self.assertFalse(result['met'])
        self.assertIsNone(result['ratios']['elapsed_s_ratio'])
        self.assertEqual(result['lost_reference_case_ids'], ['feasible'])


if __name__ == '__main__':
    unittest.main()
