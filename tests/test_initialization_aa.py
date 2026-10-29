"""Behavior/integrity checks for development A/A orchestration and review."""
import ast
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'versions/navigation_v4'), str(ROOT/'versions/initialization_aa_v1'), str(ROOT/'tools')]
from blind_drone.contracts.runtime import VehicleState
from blind_drone.experiments.protocol_v2 import load_v2_config
from blind_drone.navigation.observed import MissionV2
from blind_drone.sensors.acquisition import SampledObservation
from blind_drone_v4.navigation import ObservedDetourNavigator
from blind_drone_aa.adapters.webots.drone import policy_factory
from blind_drone_aa.audit import compare_value, summarize
from blind_drone_aa.protocol import execution_arms, generated_outputs, load_spec, schedule, select_cases
from review_initialization_aa import check_attempt_classification, safe_file


class InitializationAATests(unittest.TestCase):
    def test_matrix_has_96_episodes_in_72_processes_and_reverses_slots(self):
        _, cases = generated_outputs()
        records = list(schedule(cases))
        self.assertEqual(len(cases), 12)
        self.assertEqual(sum(c['feasible'] for c in cases), 11)
        self.assertEqual(len(records), 72)
        keys = [(c['id'], mode, repeat, role) for c, mode, repeat, arm in records
                for role in execution_arms(c['id'], repeat, mode, arm)]
        self.assertEqual(len(keys), 96)
        self.assertEqual(len(set(keys)), 96)
        for case in cases:
            self.assertEqual(execution_arms(case['id'], 0, 'warm'), execution_arms(case['id'], 1, 'warm')[::-1])

    def test_no_heldout_or_ambiguous_mode_and_repeat(self):
        for split in ('test', 'validation', 'train'):
            with self.assertRaisesRegex(ValueError, 'development only'):
                select_cases(split)
        for repeat, mode, arm in [(True, 'warm', None), (2, 'warm', None), (0, 'cold', None),
                                  (0, 'warm', 'reference'), (0, 'unknown', None)]:
            with self.assertRaises(ValueError):
                execution_arms('case', repeat, mode, arm)

    def test_both_instances_use_v4_and_missing_sensor_data_stops(self):
        left = policy_factory(MissionV2((5., 0., 1.5), 'mapped'), load_v2_config())
        right = policy_factory(MissionV2((5., 0., 1.5), 'mapped'), load_v2_config())
        self.assertIs(type(left), ObservedDetourNavigator)
        self.assertIs(type(right), ObservedDetourNavigator)
        state = VehicleState(0., (0., 0., 1.5), (0., 0., 0.), (0., 0., 0.), (0., 0., 0.))
        observation = SampledObservation.construct(state, None)
        self.assertEqual(left.step(observation), right.step(observation))
        self.assertEqual(left.status, 'invalid_or_stale_observation')

    def test_equivalence_checks_timestamps_flags_lengths_and_nonfinite(self):
        tolerance = load_spec()['equivalence']
        self.assertIsNone(compare_value({'x': 0., 'time_s': 0.}, {'x': 1e-6, 'time_s': 1e-9}, tolerance))
        self.assertIsNotNone(compare_value({'time_s': 0.}, {'time_s': 2e-9}, tolerance))
        for other in ({'x': float('nan')}, {'x': True}, {'x': [0.]}, {'x': 2e-6}):
            self.assertIsNotNone(compare_value({'x': 0.}, other, tolerance))
        self.assertIsNotNone(compare_value([1], [1, 2], tolerance))
        self.assertIsNotNone(compare_value({'status': 'scan'}, {'status': 'follow'}, tolerance))

    def test_missing_matrix_never_qualifies(self):
        with self.assertRaisesRegex(ValueError, 'Incomplete/duplicate'):
            summarize([], [{'id': 'case'}], load_spec())

    def test_algorithm_or_exit_failure_cannot_be_reclassified_as_infrastructure(self):
        row = {'result': None, 'watchdog': False, 'returncode': 1, 'classification': 'infrastructure'}
        check_attempt_classification(row, 'could not connect to display')
        with self.assertRaisesRegex(ValueError, 'classification'):
            check_attempt_classification(row, 'Controller algorithm exception')
        row.update(result={'status': 'complete'}, classification='valid')
        with self.assertRaisesRegex(ValueError, 'classification'):
            check_attempt_classification(row, '')

    def test_reviewer_rejects_path_traversal_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); raw = base/'raw'; raw.mkdir()
            outside = base/'outside'; outside.write_text('private')
            (raw/'link').symlink_to(outside)
            for name in ('../outside', str(outside), 'link'):
                with self.assertRaisesRegex(ValueError, 'escapes'):
                    safe_file(raw, name)

    def test_robot_adapter_has_no_supervisor_or_case_lookup(self):
        source = (ROOT/'versions/initialization_aa_v1/blind_drone_aa/adapters/webots/drone.py').read_text()
        tree = ast.parse(source)
        self.assertNotIn('Supervisor', {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)})
        for forbidden in ('getFromDef', 'getPosition', 'BLIND_DRONE_CASE', 'BLIND_DRONE_AA_MODE', 'BLIND_DRONE_AA_ARM'):
            self.assertNotIn(forbidden, source)


if __name__ == '__main__':
    unittest.main()
