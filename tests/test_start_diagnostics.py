"""Offline diagnosis behavior; no simulator or recorded artifacts required."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tools'))
from blind_drone.contracts.runtime import VehicleState
from blind_drone.experiments.protocol_v2 import load_v2_config
from blind_drone.observation.range_grid import RangeGrid
from blind_drone.sensors.acquisition import RANGE_NAMES
from diagnose_navigation_start import (SegmentProbe, cell_coverage_geometry, diagnose,
                                       explain_segment, reference_samples, replay_observation)


def grid():
    config = load_v2_config()
    result = RangeGrid(config['navigation_v2'], config['vehicle']['body_size_m'], .33)
    result.origin = (0., 0.)
    return result


def row(time=0., position=(.125, .025, 1.5)):
    pose = VehicleState(time, position, (0., 0., 0.), (0., 0., 0.), (0., 0., 0.))
    return {'time_s': time, 'pose_time_s': time, 'pose': asdict(pose),
            'readings': {name: {'distance_m': 8., 'valid': True, 'at_limit': True} for name in RANGE_NAMES}}


class SegmentExplanationTests(unittest.TestCase):
    def test_unknown_is_distinct_from_blocked_and_can_pass_relaxed_check(self):
        g = grid();g.free.add((0, 0))
        detail = explain_segment(g, (.125, .125), (.375, .125))
        self.assertEqual(detail['reason'], 'unknown')
        self.assertEqual(detail['cell'], [1, 0])
        self.assertTrue(explain_segment(g, (.125, .125), (.375, .125), False)['ok'])
        g.blocked.add((1, 0))
        self.assertEqual(explain_segment(g, (.125, .125), (.375, .125))['reason'], 'blocked')

    def test_first_sample_and_outside_precedence(self):
        g = grid()
        self.assertEqual(explain_segment(g, (.01, .01), (.3, .01))['sample_index'], 0)
        g.blocked.add((80, 0))
        self.assertEqual(explain_segment(g, (20., .01), (.01, .01))['reason'], 'outside')

    def test_negative_coordinates_and_cell_edge_use_floor(self):
        g = grid();g.free.add((-1, 0))
        detail = explain_segment(g, (-.01, .01), (0., .01))
        self.assertEqual(detail['cell'], [0, 0])
        self.assertEqual(detail['sample_index'], detail['steps'])

    def test_degenerate_segment_is_checked(self):
        g = grid()
        self.assertFalse(explain_segment(g, (.1, .1), (.1, .1))['ok'])
        g.free.add((0, 0))
        self.assertTrue(explain_segment(g, (.1, .1), (.1, .1))['ok'])

    def test_probe_returns_frozen_predicate_without_grid_mutation(self):
        g = grid();g.free.add((0, 0))
        before = deepcopy(g.__dict__)
        probe = SegmentProbe(g)
        self.assertFalse(probe((.1, .1), (.4, .1), True))
        self.assertTrue(probe((.1, .1), (.4, .1), False))
        self.assertEqual(g.__dict__, before)
        self.assertEqual(probe.calls, 2)
        self.assertTrue(probe.rejections[0]['allowed_without_free'])

    def test_many_segments_match_original_with_overlapping_states(self):
        g = grid();rng = random.Random(13)
        g.free = {(x, y) for x in range(-5, 6) for y in range(-5, 6) if rng.random() < .7}
        g.blocked = {(x, y) for x in range(-5, 6) for y in range(-5, 6) if rng.random() < .1}
        for _ in range(150):
            start = (rng.uniform(-2, 2), rng.uniform(-2, 2))
            end = (rng.uniform(-13, 13), rng.uniform(-13, 13))
            for require_free in (True, False):
                self.assertEqual(explain_segment(g, start, end, require_free)['ok'],
                                 g.segment_ok(start, end, require_free))


class ObservationReplayTests(unittest.TestCase):
    def test_pose_sample_and_current_time_are_separate(self):
        samples = reference_samples([row(0.), row(.032)], 32)
        obs = replay_observation({'pose_time_s': .032, 'sample_time_s': 0., 'time_s': .048}, samples)
        self.assertEqual(obs.state.time_s, .048)
        self.assertEqual(obs.sample_time_s, 0.)
        self.assertEqual(obs.acquisition_state.time_s, 0.)
        self.assertTrue(obs.usable(.12, 8.))

    def test_candidate_duplicate_missing_and_misaligned_pose_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Only reference'):reference_samples([row()], 64)
        for rows in ([row(), row()], [row(), row(.064)]):
            with self.assertRaisesRegex(ValueError, 'Duplicate, missing'):reference_samples(rows, 32)
        value = row();value['pose']['time_s'] = .016
        with self.assertRaisesRegex(ValueError, 'timestamp mismatch'):reference_samples([value], 32)

    def test_missing_pose_and_future_pose_cannot_be_interpolated(self):
        samples = reference_samples([row(), row(.032)], 32)
        with self.assertRaisesRegex(ValueError, 'interpolation'):
            replay_observation({'pose_time_s': .016, 'sample_time_s': 0., 'time_s': .032}, samples)
        with self.assertRaisesRegex(ValueError, 'Future'):
            replay_observation({'pose_time_s': .032, 'sample_time_s': 0., 'time_s': .016}, samples)

    def test_extra_trace_metadata_is_not_forwarded_to_observation(self):
        value = row();value['obstacles'] = ['not navigation data']
        samples = reference_samples([value], 32)
        obs = replay_observation({'pose_time_s': 0., 'sample_time_s': 0., 'time_s': .016}, samples)
        self.assertEqual(set(obs.__dict__), {'state', 'sample_time_s', 'frame', 'ranges', 'acquisition_state'})

    def test_stale_measurement_stays_stale(self):
        obs = replay_observation({'pose_time_s': 0., 'sample_time_s': 0., 'time_s': .5},
                                 reference_samples([row()], 32))
        self.assertFalse(obs.usable(.12, 8.))

    def test_heldout_input_rejected_before_audit_or_output_creation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for split in ('validation', 'test'):
                (root / 'result.json').write_text(json.dumps({'split': split}))
                with self.assertRaisesRegex(ValueError, 'development-only'):
                    diagnose(root, 'a'*40, root / 'new')
                self.assertFalse((root / 'new').exists())


class RingGeometryTests(unittest.TestCase):
    def observation(self, position):
        return replay_observation({'pose_time_s': 0., 'sample_time_s': 0., 'time_s': .016},
                                  reference_samples([row(position=position)], 32))

    def test_wholly_inside_cell_is_unreachable_but_not_marked_free(self):
        g = grid();obs = self.observation((.125, .025, 1.5))
        before = deepcopy(g.__dict__)
        result = cell_coverage_geometry(g, (0, -1), [obs])
        self.assertTrue(result['ray_unreachable_for_entire_trace'])
        self.assertFalse(result['final_free'])
        self.assertEqual(g.__dict__, before)

    def test_center_retained_or_partly_outside_is_not_certified_unreachable(self):
        g = grid();obs = self.observation((.125, .025, 1.5))
        self.assertFalse(cell_coverage_geometry(g, (0, 0), [obs])['ray_unreachable_for_entire_trace'])
        self.assertFalse(cell_coverage_geometry(g, (1, 0), [obs])['ray_unreachable_for_entire_trace'])


if __name__ == '__main__':
    unittest.main()
