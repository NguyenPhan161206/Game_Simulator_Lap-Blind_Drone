"""Evidence aggregation must not turn a frontier into qualification."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from build_7a_tradeoffs import build_report, pareto


class TradeoffTests(unittest.TestCase):
    def test_frontier_retains_equal_and_quality_cost_tradeoffs(self):
        a = {'case_successes': 74, 'feasible_cases': 74, 'cpu': 1., 'data': 10.}
        b = a | {'case_successes': 67, 'data': 5.}
        worse = a | {'cpu': 2.}
        self.assertEqual(set(pareto({'a': a, 'b': b, 'equal': a.copy(), 'worse': worse}, ('cpu', 'data'))),
                         {'a', 'b', 'equal'})

    def test_incompatible_denominator_and_invalid_metrics_are_rejected(self):
        a = {'case_successes': 45, 'feasible_cases': 50, 'cpu': 1.}
        for other in (a | {'feasible_cases': 74}, a | {'cpu': float('nan')},
                      a | {'case_successes': 51}, a | {'cpu': -1.}):
            with self.assertRaises(ValueError):
                pareto({'a': a, 'b': other}, ('cpu',))

    def test_historical_groups_remain_separate_with_failures_and_sources(self):
        report = build_report()
        self.assertIsNone(report['global_frontier'])
        self.assertGreaterEqual(len(report['groups']), 4)
        for group in report['groups']:
            self.assertTrue(group['not_a_configuration_selection'])
            self.assertEqual(len(group['source_commit']), 40)
        cadence = report['groups'][0]
        self.assertFalse(cadence['quality_gate_met'])
        self.assertEqual(cadence['points']['candidate']['feasible_episode_outcomes']['timeout'], 7)
        self.assertEqual(len(report['sources_sha256']), len(report['groups']))


if __name__ == '__main__':
    unittest.main()
