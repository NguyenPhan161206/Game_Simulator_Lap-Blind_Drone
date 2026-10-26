"""Evidence validation only: these tests do not launch or observe a GUI."""
import copy
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import subprocess
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
        quiet = patch("builtins.print")
        quiet.start()
        self.addCleanup(quiet.stop)
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

    def test_review_preserves_malformed_result_without_accepting_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "run").mkdir()
            local.write_json(root / "session.json", {**self.session, "mode": "mapped", "wall_s": 1})
            for raw in ("{bad", "[]", '{"episodes":42}'):
                with self.subTest(raw=raw):
                    (root / "run/result.json").write_text(raw)
                    result = local.review(root)
                    self.assertFalse(result["comparison"]["identity_valid"])
                    self.assertEqual((root / "run/result.json").read_text(), raw)
                    self.assertNotIn("sim_s_over_total_wall_s", result)

    def test_manual_attestation_with_zero_commands_requires_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "run").mkdir()
            local.write_json(root / "session.json", {"mode": "manual"})
            local.write_json(root / "operator.json", {"answers": {"key_W": "yes"}, "responsiveness_notes": "y"})
            raw = json.dumps({"time_s": 0.016, "navigation": {"command": {"forward_m_s": 0.0}}}) + "\n"
            (root / "run/telemetry.jsonl").write_text(raw)
            before = (root / "operator.json").read_bytes()
            result = local.review(root)
            self.assertEqual(len(result["manual_evidence_warnings"]), 2)
            self.assertEqual((root / "operator.json").read_bytes(), before)
            self.assertFalse(result["gui_verified_automatically"])

    def test_lock_blocks_another_process_and_releases_after_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "active.lock"
            code = ("import fcntl,sys\n"
                    "with open(sys.argv[1],'a+') as f:\n"
                    " try: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)\n"
                    " except BlockingIOError: sys.exit(4)\n")
            with self.assertRaisesRegex(RuntimeError, "fixture failure"):
                with local.exclusive_session(path):
                    child = subprocess.run([sys.executable, "-c", code, str(path)])
                    self.assertEqual(child.returncode, 4)
                    raise RuntimeError("fixture failure")
            self.assertTrue(path.exists())
            self.assertEqual(subprocess.run([sys.executable, "-c", code, str(path)]).returncode, 0)

    def test_operator_record_creation_cannot_overwrite_existing_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "operator.json"
            local.write_json(path, {"original": True}, exclusive=True)
            original = path.read_bytes()
            with self.assertRaises(FileExistsError):
                local.write_json(path, {"original": False}, exclusive=True)
            self.assertEqual(path.read_bytes(), original)

    def write_batch_fixture(self, root):
        """Synthetic gate data only, never evidence of GUI interaction."""
        for mode in ("manual", "mapped"):
            folder = root / mode
            (folder / "run").mkdir(parents=True)
            start, end = ("00:00:00", "00:01:00") if mode == "manual" else ("00:02:00", "00:03:00")
            session = {**self.session, "mode": mode, "helper_sha256": "fixture",
                       "started_utc": "2026-10-26T" + start + "+00:00",
                       "ended_utc": "2026-10-26T" + end + "+00:00", "wall_s": 60}
            local.write_json(folder / "session.json", session)
            keys = ["gui_opened", "correct_world_controllers"]
            keys += ["key_" + k for k in local.KEYS] if mode == "manual" else ["motion_seen", "completion_seen"]
            local.write_json(folder / "operator.json", {"kind": "operator_self_report",
                "answers": {k: "yes" for k in keys}, "responsiveness": "minor_lag",
                "simulation_control_changes": "unchanged", "responsiveness_notes": "fixture"})
            packets = [{"time_s": i + 1, "navigation": {"command": {axis: value for axis in
                        ("forward_m_s", "left_m_s", "up_m_s", "yaw_rate_rad_s")}}} for i, value in enumerate((0.1, -0.1))]
            (folder / "run/telemetry.jsonl").write_text("".join(json.dumps(p) + "\n" for p in packets))
            if mode == "mapped":
                local.write_json(folder / "run/result.json", self.report)

    def test_batch_requires_operator_observation_and_preserves_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_batch_fixture(root)
            operator = root / "mapped/operator.json"
            original = operator.read_bytes()
            summary = local.audit_batch(root)
            self.assertTrue(summary["ready_for_review"])
            self.assertFalse(summary["project_checklist_modified"])
            self.assertEqual(operator.read_bytes(), original)
            operator.unlink()
            self.assertFalse(local.audit_batch(root)["ready_for_review"])

    def test_batch_rejects_overlap_source_change_and_dirty_source(self):
        for change in ("overlap", "source", "dirty"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.write_batch_fixture(root)
                path = root / "mapped/session.json"
                session = json.loads(path.read_text())
                if change == "overlap":
                    session["started_utc"] = "2026-10-26T00:00:30+00:00"
                elif change == "source":
                    session["source_commit"] = "different"
                else:
                    session["working_tree_dirty"] = True
                local.write_json(path, session)
                self.assertFalse(local.audit_batch(root)["ready_for_review"])

    def test_batch_rejects_pause_unknown_performance_and_mismatched_commands(self):
        for change in ("pause", "unobserved", "zero_commands"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.write_batch_fixture(root)
                path = root / "mapped/operator.json"
                operator = json.loads(path.read_text())
                if change == "pause":
                    operator["simulation_control_changes"] = "paused"
                elif change == "unobserved":
                    operator["responsiveness"] = "not_observed"
                else:
                    (root / "manual/run/telemetry.jsonl").write_text('{"time_s":1,"navigation":{"command":{}}}\n')
                local.write_json(path, operator)
                self.assertFalse(local.audit_batch(root)["ready_for_review"])

    def test_accept_requires_interactive_terminal_before_creating_output(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(local.sys.stdin, "isatty", return_value=False):
            output = Path(directory) / "batch"
            with self.assertRaisesRegex(ValueError, "interactive desktop"):
                local.accept(argparse.Namespace(output=output))
            self.assertFalse(output.exists())

    def test_accept_does_not_launch_mapped_after_inconsistent_manual(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "batch"
            calls = []
            def launch_fixture(args):
                calls.append(args.mode)
                self.write_batch_fixture(root)
                # Leave mapped fixture out of the partial run; only the manual process is simulated here.
                import shutil
                shutil.rmtree(root / "mapped")
                (root / "manual/run/telemetry.jsonl").write_text('{"time_s":1,"navigation":{"command":{}}}\n')
                return 0
            args = argparse.Namespace(output=root, manual_timeout=10, mapped_timeout=10, webots=None, software_rendering=False)
            with patch.object(local.sys.stdin, "isatty", return_value=True), patch.object(local, "launch", side_effect=launch_fixture):
                self.assertEqual(local.accept(args), 1)
            self.assertEqual(calls, ["manual"])
            self.assertFalse(json.loads((root / "acceptance.json").read_text())["ready_for_review"])


if __name__ == "__main__":
    unittest.main()
