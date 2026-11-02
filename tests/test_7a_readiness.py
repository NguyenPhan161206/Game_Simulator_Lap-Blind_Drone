"""Conditional development selection cannot silently authorize held-out runs."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from check_7a_readiness import pick_candidate


class ReadinessTests(unittest.TestCase):
    def reports(self):
        result = {}
        for key, count, arm in (('retention', 352, 'candidate'), ('adaptive', 48, 'candidate'), ('sparse', 72, 'sparse')):
            result[key] = {'episodes': count, 'complete': True, 'raw_audit_passed': True,
                'source_commit': 'a'*40, 'summary': {'met': True, 'gates': {
                    'reference_task_quality': True, 'initialization_equivalent': True},
                    'by_arm': {arm: {'payload_rate_mean_B_s': 2000.}}}}
        return result

    def test_missing_review_is_pending_not_a_negative_or_permission_to_run(self):
        result = pick_candidate({})
        self.assertEqual(result['status'], 'pending_development')
        self.assertFalse(result['validation_authorized'])
        self.assertFalse(result['test_authorized'])

    def test_fixed_tie_break_and_acquisition_priority_precede_retention(self):
        reports = self.reports()
        result = pick_candidate(reports)
        self.assertEqual(result['candidate'], 'sparse')
        self.assertFalse(result['validation_authorized'])
        reports['adaptive']['summary']['by_arm']['candidate']['payload_rate_mean_B_s'] = 1800.
        self.assertEqual(pick_candidate(reports)['candidate'], 'adaptive')
        for key in ('adaptive', 'sparse'):
            reports[key]['summary']['gates']['candidate_task_quality'] = False
            reports[key]['summary']['met'] = False
        self.assertEqual(pick_candidate(reports)['candidate'], 'retention')

    def test_negative_complete_evidence_never_opens_test(self):
        reports = self.reports()
        for report in reports.values():
            report['summary']['met'] = False
            report['summary']['gates']['data_reduction'] = False
        result = pick_candidate(reports)
        self.assertEqual(result['status'], 'development_not_met')
        self.assertIsNone(result['candidate'])
        self.assertFalse(result['test_authorized'])

    def test_bad_baseline_blocks_even_before_sensor_reports_exist(self):
        reports = self.reports()
        base = reports['retention']; base['summary']['gates']['reference_task_quality'] = False
        base['summary']['met'] = False
        result = pick_candidate({'retention': base})
        self.assertEqual(result['status'], 'baseline_not_ready')

    def test_incomplete_or_contradictory_success_is_rejected(self):
        reports = self.reports()
        for change in ({'episodes': 1}, {'complete': False}, {'source_commit': 'short'}):
            altered = deepcopy(reports); altered['adaptive'].update(change)
            with self.assertRaises(ValueError): pick_candidate(altered)
        reports['adaptive']['summary']['gates']['candidate_task_quality'] = False
        with self.assertRaises(ValueError): pick_candidate(reports)


if __name__ == '__main__':
    unittest.main()
