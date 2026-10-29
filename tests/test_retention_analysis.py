"""Evidence analysis must reject missing repeats and changed raw files."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from analyze_retention_failures import case_outcomes, checked_bytes, decision_profile, goal_dwell_profile


class RetentionAnalysisTests(unittest.TestCase):
    def test_repeat_failure_is_kept_and_negative_controls_excluded(self):
        rows = [{"arm": "candidate", "feasible": True, "case_id": "a",
                 "repeat": r, "outcome": o} for r, o in [(1, "timeout"), (0, "success")]]
        rows.append({"arm": "candidate", "feasible": False, "case_id": "negative",
                     "repeat": 0, "outcome": "timeout"})
        self.assertEqual(case_outcomes(rows, "candidate"), {"a": ["success", "timeout"]})
        with self.assertRaisesRegex(ValueError, "Missing repeat"):
            case_outcomes(rows[1:], "candidate")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            case_outcomes(rows + [rows[0]], "candidate")

    def test_hash_drift_and_decision_time_reversal_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raw"
            path.write_bytes(b"raw")
            expected = hashlib.sha256(b"raw").hexdigest()
            self.assertEqual(checked_bytes(path, expected), b"raw")
            path.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                checked_bytes(path, expected)
        row = {"time_s": 2., "status": "scan_no_observed_route",
               "command": {"forward_m_s": 0., "left_m_s": 0.}}
        with self.assertRaisesRegex(ValueError, "unordered"):
            decision_profile([row, row])

    def test_near_goal_without_continuous_slow_dwell_is_distinct(self):
        rows = [{"time_s": time, "position_m": [0., 0., 0.],
                 "velocity_m_s": [speed, 0., 0.]}
                for time, speed in [(88., .1), (88.5, .1), (89., .3), (89.5, .1), (90., .1)]]
        value = goal_dwell_profile(rows, [0., 0., 0.],
                                   {"goal_radius_m": .5, "stop_speed_m_s": .18})
        self.assertEqual(value["first_inside_goal_s"], 88.)
        self.assertEqual(value["longest_slow_goal_interval_s"], .5)


if __name__ == "__main__":
    unittest.main()
