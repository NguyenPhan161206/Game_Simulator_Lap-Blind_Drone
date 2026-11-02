"""Source/proof/exposure guards for one fixed fresh sparse evaluation."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'versions/navigation_v4'), str(ROOT/'versions/initialization_aa_v1'),
    str(ROOT/'versions/retention_cold_v1'), str(ROOT/'versions/sensor_pilots_v1'),
    str(ROOT/'versions/efficiency_eval_v1'), str(ROOT/'versions/efficiency_runtime_v1'), str(ROOT/'tools')]
from blind_drone_efficiency import protocol
from blind_drone_efficiency import audit


class EfficiencyRuntimeTests(unittest.TestCase):
    def proof(self):
        return {'protocol_version': 'efficiency_runtime_v1', 'split': 'validation', 'complete': True,
            'raw_audit_passed': True, 'episodes': 288, 'cases': 72, 'runtime_sha256': 'runtime',
            'binding_sha256': 'binding', 'design_lock_sha256': 'design', 'source_commit': 'a'*40,
            'summary': {'met': True, 'gates': {'case_bound': True, 'safety': True}}}

    def test_test_requires_complete_source_matched_positive_validation(self):
        args = ('runtime', 'binding', 'design', 'a'*40)
        protocol.validate_test_proof(self.proof(), *args)
        changes = ({'split': 'test'}, {'complete': False}, {'episodes': 287}, {'runtime_sha256': 'other'},
                   {'source_commit': 'b'*40}, {'binding_sha256': 'other'})
        for change in changes:
            proof = self.proof(); proof.update(change)
            with self.assertRaises(ValueError): protocol.validate_test_proof(proof, *args)
        for summary in ({'met': False, 'gates': {'case_bound': False}},
                        {'met': True, 'gates': {'case_bound': False}}, {'met': True, 'gates': {}}):
            proof = self.proof(); proof['summary'] = summary
            with self.assertRaisesRegex(ValueError, 'did not qualify'): protocol.validate_test_proof(proof, *args)

    def test_heldout_subsets_and_other_candidates_rejected_before_reading_fixture(self):
        for split in ('validation', 'test'):
            with self.assertRaisesRegex(ValueError, 'No held-out subsets'):
                protocol.select_cases(split, ['one-case'])
        for arm in ('dropout', 'candidate', 'other'):
            with self.assertRaises(ValueError): protocol.profile_for('sparse', arm)
        self.assertEqual(protocol.profile_for('sparse', 'reference'), 'full')
        self.assertEqual(protocol.profile_for('sparse', 'sparse'), 'sparse')

    def test_exposure_marker_blocks_second_output_and_workflow_rerun(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict('os.environ', {'GITHUB_RUN_ATTEMPT': '1'}):
            protocol.claim_exposure('validation', 'hash', '/run/first', directory)
            with self.assertRaisesRegex(ValueError, 'already claimed'):
                protocol.claim_exposure('validation', 'hash', '/run/different', directory)
            with patch.dict('os.environ', {'GITHUB_RUN_ATTEMPT': '2'}):
                with self.assertRaisesRegex(ValueError, 'Workflow reruns'):
                    protocol.claim_exposure('test', 'hash', '/run/test', directory)

    def test_missing_runtime_lock_never_authorizes_heldout(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(protocol, 'verify_binding', return_value='binding'), \
                patch.object(protocol, 'LOCK', Path(directory)/'absent'):
            with self.assertRaisesRegex(ValueError, 'equivalence proof and lock required'):
                protocol.verify_authorization('validation')

    def test_case_confidence_uses_sixty_cases_not_one_hundred_twenty_repeats(self):
        group = {'reference': {'feasible_case_success': 60, 'feasible_cases': 60},
                 'sparse': {'feasible_case_success': 59, 'feasible_cases': 60}}
        base = {'by_arm': group, 'gates': {'raw': True}, 'met': True}
        cases = [{'id': 'case'+str(i), 'family': 'empty', 'feasible': i < 60} for i in range(72)]
        rows = [{'episode': {'case_id': c['id'], 'arm': a, 'outcome': 'success'}} for c in cases for a in group]
        with patch.object(audit, 'sensor_summary', return_value=deepcopy(base)):
            result = audit.summarize(rows, cases, {'split': 'validation'})
        self.assertTrue(result['gates']['reference_success_lower_bound'])
        self.assertFalse(result['gates']['sparse_success_lower_bound'])
        self.assertFalse(result['met'])

    def test_robot_entrypoint_reuses_qualified_adapter_without_world_access(self):
        source = (ROOT/'simulation/webots/controllers/drone_efficiency/drone_efficiency.py').read_text()
        self.assertIn('from blind_drone_sensor_pilots.adapters.webots.drone import main', source)
        self.assertNotIn('Supervisor', source)
        self.assertNotIn('BLIND_DRONE_CASE', source)


if __name__ == '__main__':
    unittest.main()
