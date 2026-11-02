"""Fresh commitments and uncertainty are design evidence, not navigation evidence."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'versions/navigation_v4'), str(ROOT/'versions/efficiency_eval_v1')]
from blind_drone.experiments.protocol_v3 import task_fingerprint
from blind_drone.world.scenarios import digest
from efficiency_design import assert_disjoint, build_cases, generated_index, historical_commitments, spec, success_lower_bound


class EfficiencyDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = build_cases()

    def test_fresh_balanced_commitments_remain_non_runnable(self):
        self.assertEqual(len(self.cases), 144)
        self.assertFalse(spec()['runtime_ready'])
        self.assertEqual(spec()['candidate'], 'pending_development_readiness_0022')
        for split in ('validation', 'test'):
            group = [c for c in self.cases if c['split'] == split]
            self.assertEqual(len(group), 72)
            self.assertEqual(sum(c['feasible'] for c in group), 60)
            self.assertEqual(set(Counter(c['family'] for c in group).values()), {12})
        index = generated_index(self.cases)
        self.assertNotIn('obstacles', index['cases'][0])
        self.assertNotIn('waypoints_m', str(index))
        assert_disjoint(self.cases, historical_commitments())

    def test_same_task_with_new_seed_yaw_and_translation_is_still_duplicate(self):
        first = self.cases[0]
        other = deepcopy(first)
        other.update(id='different-label', seed=9999999, start_yaw_rad=2.)
        for key in ('start_m', 'goal_m'):
            other[key][0] += 1.; other[key][1] += 2.
        for obstacle in other['obstacles']:
            obstacle['center_m'][0] += 1.; obstacle['center_m'][1] += 2.
        other['geometry_sha256'] = digest({k: other[k] for k in ('start_m', 'goal_m', 'obstacles')})
        self.assertNotEqual(first['geometry_sha256'], other['geometry_sha256'])
        self.assertEqual(task_fingerprint(first), task_fingerprint(other))
        with self.assertRaisesRegex(ValueError, 'canonical task'):
            assert_disjoint([first, other], [])

    def test_exact_case_bound_cannot_qualify_one_failed_case_in_sixty(self):
        self.assertAlmostEqual(success_lower_bound(60, 60), .05**(1/60), places=12)
        self.assertGreaterEqual(success_lower_bound(60, 60), .95)
        self.assertLess(success_lower_bound(59, 60), .95)
        self.assertEqual(success_lower_bound(0, 60), 0.)
        for success, total in ((61, 60), (1, 0), (True, 60)):
            with self.assertRaises(ValueError): success_lower_bound(success, total)


if __name__ == '__main__':
    unittest.main()
