"""Research design integrity/statistics tests; not v3 flight evidence."""
import copy
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from blind_drone.experiments import protocol_v3 as p
from blind_drone.world.scenarios import generate_case


class ResearchV3Tests(unittest.TestCase):
    def test_registered_index_counts_seeds_and_hashes(self):
        index = json.loads(p.INDEX.read_text())
        spec = p.load_spec()
        cases = index["cases"]
        self.assertEqual(len(cases), 480)
        for key in ("id", "seed", "geometry_sha256", "task_sha256", "case_sha256"):
            self.assertEqual(len({c[key] for c in cases}), len(cases), key)
        for split in p.SPLITS:
            group = [c for c in cases if c["split"] == split]
            self.assertEqual(sum(c["feasible"] for c in group), spec["splits"][split]["feasible_cases"])
            self.assertEqual(sum(not c["feasible"] for c in group), spec["splits"][split]["negative_cases"])
            self.assertEqual({c["family"] for c in group if c["feasible"]}, set(spec["data"]["feasible_families"]))
            self.assertTrue(all(c["certificate_kind"] == ("conservative_horizontal_grid_witness" if c["feasible"] else "goal_inside_solid") for c in group))

    def test_fingerprint_rejects_transformed_duplicate_and_different_yaw(self):
        original = generate_case("single_block", 3200001, "development")
        moved = copy.deepcopy(original)
        def transform(point):
            return [-point[1] + 2, point[0] - 1, point[2]]
        moved["start_m"] = transform(original["start_m"])
        moved["goal_m"] = transform(original["goal_m"])
        for block in moved["obstacles"]:
            block["center_m"] = transform(block["center_m"])
            x, y, z = block["size_m"]
            block["size_m"] = [y, x, z]
        moved.update(id="new-id", seed=9999999, geometry_sha256="different-raw-hash", start_yaw_rad=0)
        self.assertEqual(p.task_fingerprint(original), p.task_fingerprint(moved))
        with self.assertRaisesRegex(ValueError, "equivalent transformed"):
            p.check_disjoint([moved], [original])

    def test_duplicate_seed_rejected_even_with_different_geometry(self):
        a = generate_case("single_block", 1, "development")
        b = generate_case("u_trap", 1, "test")
        with self.assertRaisesRegex(ValueError, "seed"):
            p.check_disjoint([a, b], [])

    def test_spec_rejects_overlapping_seeds_or_hidden_runtime_activation(self):
        spec = p.load_spec()
        spec["splits"]["test"]["first_seed"] = spec["splits"]["development"]["first_seed"]
        with self.assertRaisesRegex(ValueError, "Overlapping"):
            p.validate_spec(spec)
        spec = p.load_spec()
        spec["runtime_ready"] = True
        with self.assertRaisesRegex(ValueError, "Design-only"):
            p.validate_spec(spec)

    def test_sensor_and_reference_control_drift_rejected(self):
        for path, value, error in (("candidate_period_ms", 96, "32/64"), ("pose_period_ms", 64, "cadence"), ("range_max_age_s", .032, "freshness")):
            spec = p.load_spec()
            spec[path] = value
            with self.assertRaisesRegex(ValueError, error):
                p.validate_spec(spec)
        spec = p.load_spec()
        spec["controls"]["speed_m_s"] = .8
        with self.assertRaisesRegex(ValueError, "control drift"):
            p.validate_spec(spec)

    def test_ledger_genesis_preserved_and_explicit_exposure_required(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "exposure.json"
            genesis = p.ledger_genesis()
            path.write_text(json.dumps({"schema_version": 3, "events": [genesis]}))
            self.assertEqual(p.verify_ledger(path), 1)
            event = {**genesis, "event_id": "development-debug", "splits": ["development"], "navigation_executed": True}
            path.write_text(json.dumps({"schema_version": 3, "events": [genesis, event]}))
            self.assertEqual(p.verify_ledger(path), 2)
            del event["outcomes_viewed"]
            path.write_text(json.dumps({"schema_version": 3, "events": [genesis, event]}))
            with self.assertRaisesRegex(ValueError, "Incomplete"):
                p.verify_ledger(path)
            genesis["outcomes_viewed"] = True
            path.write_text(json.dumps({"schema_version": 3, "events": [genesis]}))
            with self.assertRaisesRegex(ValueError, "genesis mismatch"):
                p.verify_ledger(path)

    def test_exact_bound_known_cases_and_monotonicity(self):
        self.assertAlmostEqual(p.adverse_upper_bound(0, 200), 1 - .05 ** (1 / 200), places=13)
        self.assertAlmostEqual(p.adverse_upper_bound(1, 2), math.sqrt(.95), places=13)
        self.assertEqual(p.adverse_upper_bound(200, 200), 1)
        self.assertLess(p.adverse_upper_bound(0, 200), .05)
        self.assertGreater(p.adverse_upper_bound(10, 200), .05)
        values = [p.adverse_upper_bound(k, 20) for k in range(21)]
        self.assertEqual(values, sorted(values))
        for args in ((-1, 200), (201, 200), (0, 0), (True, 200), (1, 20, 0)):
            with self.assertRaises(ValueError):
                p.adverse_upper_bound(*args)

    def test_actual_lock_and_legacy_locks_valid_but_evaluation_denied(self):
        self.assertEqual(len(p.verify_design()), 64)
        with self.assertRaisesRegex(ValueError, "evaluation is disabled"):
            p.require_evaluation_ready()

    def test_modified_design_or_missing_lock_fails(self):
        hashes = p.design_hashes()
        hashes["runtime_ready"] = True
        with patch.object(p, "design_hashes", return_value=hashes):
            with self.assertRaisesRegex(ValueError, "mismatch"):
                p.verify_design()
        with tempfile.TemporaryDirectory() as folder, patch.object(p, "LOCK", Path(folder) / "missing.json"):
            with self.assertRaisesRegex(ValueError, "missing"):
                p.verify_design()

    def test_cli_cannot_overwrite_lock_or_launch_unimplemented_evaluation(self):
        before = p.LOCK.read_bytes()
        for option, error in (("--freeze", "Refusing to replace"), ("--evaluate", "evaluation is disabled")):
            result = subprocess.run([sys.executable, "tools/build_research_v3.py", option], cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(error, result.stderr)
        self.assertEqual(p.LOCK.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
