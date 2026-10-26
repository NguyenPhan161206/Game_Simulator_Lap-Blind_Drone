"""Evidence validation only: these tests do not launch or observe a GUI."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
spec = importlib.util.spec_from_file_location("local_session", ROOT / "tools/local_session.py")
local = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local)


class LocalEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.reference = json.loads(local.REFERENCE.read_text())
        self.report = copy.deepcopy(self.reference["reports"][0])
        self.report["episodes"] = [e for e in self.report["episodes"]
                                   if e["case_id"] == local.CASE and e["policy"] == "mapped"]
        self.session = {"protocol_sha256": self.report["protocol_sha256"],
                        "source_commit": self.report["source_commit"],
                        "working_tree_dirty": self.report["working_tree_dirty"],
                        "exit_code": 0, "status": "process_exited"}

    def compare(self):
        return local.compare_mapped(self.report, self.session, self.reference)

    def test_same_numbers_are_only_diagnostic_not_gui_proof(self):
        result = self.compare()
        self.assertTrue(result["identity_valid"])
        self.assertEqual(result["classification"], "numerically_close")
        self.assertNotIn("gui_verified", result)

    def test_missing_or_failed_checks_rejected(self):
        for checks in ({}, {"failure": {"passed": False}}, {"bad": True}):
            with self.subTest(checks=checks):
                self.report["checks"] = checks
                self.assertFalse(self.compare()["identity_valid"])

    def test_wrong_protocol_geometry_source_and_dirty_rejected(self):
        for key in ("protocol_sha256", "manifest_sha256", "source_commit", "working_tree_dirty"):
            with self.subTest(key=key):
                original = self.report[key]
                self.report[key] = "wrong"
                self.assertFalse(self.compare()["identity_valid"])
                self.report[key] = original
        self.report["episodes"][0]["geometry_sha256"] = "wrong"
        self.assertFalse(self.compare()["identity_valid"])

    def test_extra_or_missing_episode_rejected(self):
        self.report["episodes"] *= 2
        self.assertFalse(self.compare()["identity_valid"])
        self.report["episodes"] = []
        self.assertFalse(self.compare()["identity_valid"])

    def test_failed_process_cannot_reuse_result(self):
        self.session["exit_code"] = 1
        self.assertFalse(self.compare()["identity_valid"])
        self.session.update(exit_code=0, status="timeout")
        self.assertFalse(self.compare()["identity_valid"])

    def test_outcome_difference_retained(self):
        self.report["episodes"][0]["outcome"] = "collision"
        result = self.compare()
        self.assertTrue(result["identity_valid"])
        self.assertFalse(result["same_outcome"])
        self.assertEqual(result["classification"], "outcome_mismatch")

    def test_numeric_difference_not_assigned_a_cause(self):
        self.report["episodes"][0]["path_length_m"] += 0.1
        result = self.compare()
        self.assertEqual(result["classification"], "numeric_difference_review_required")
        self.assertAlmostEqual(result["local_minus_ci"]["path_length_m"], 0.1)

    def test_nonfinite_measurement_rejected(self):
        self.report["episodes"][0]["elapsed_s"] = float("nan")
        self.assertFalse(self.compare()["identity_valid"])

    def test_environment_clears_stale_mission_and_ci_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            (home / "bin").mkdir()
            (home / "resources").mkdir()
            (home / "bin/webots-bin").touch()  # Path fixture only; never executed.
            (home / "resources/version.txt").write_text("R2025a")
            with patch.dict(local.os.environ, {"BLIND_DRONE_CASE": "stale", "GITHUB_SHA": "stale",
                                               "GITHUB_RUN_ID": "stale", "BLIND_DRONE_MODE": "smoke"}):
                binary, env = local.desktop_environment(home / "webots", True)
            self.assertEqual(binary, str(home / "bin/webots-bin"))
            self.assertFalse(any(k.startswith("BLIND_DRONE_") for k in env))
            self.assertNotIn("GITHUB_SHA", env)
            self.assertNotIn("GITHUB_RUN_ID", env)
            self.assertEqual(env["LIBGL_ALWAYS_SOFTWARE"], "1")
            (home / "resources/version.txt").write_text("R2023b")
            with self.assertRaisesRegex(ValueError, "R2025a"):
                local.desktop_environment(home / "webots", False)


if __name__ == "__main__":
    unittest.main()
