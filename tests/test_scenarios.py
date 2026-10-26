"""Scenario geometry, deterministic splits and protocol tamper checks."""
import copy
import json
from math import pi
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from blind_drone.experiments.protocol import FROZEN_FILES, make_lock, verify_lock
from blind_drone.evaluation.episode import summarize
from blind_drone.evaluation.study import validate_study
from blind_drone.world.geometry import inflated_rectangles, path_certificate, segment_clear
from blind_drone.world.scenarios import build_manifest, digest, generate_case
from blind_drone.world.minimal_lab import controller_config, load_config


class ScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = build_manifest()
        cls.cases = cls.manifest["cases"]
        cls.body = load_config()["vehicle"]["body_size_m"]

    def test_manifest_is_exactly_reproducible(self):
        self.assertEqual(digest(self.manifest),digest(build_manifest()))
        self.assertEqual(generate_case("single_block",21001,"development"),generate_case("single_block",21001,"development"))

    def test_splits_seeds_and_geometry_are_disjoint(self):
        self.assertEqual(len(self.cases),36)
        self.assertEqual(len({c["geometry_sha256"] for c in self.cases}),36)
        seed_groups = list(self.manifest["specification"]["splits"].values())
        for i,seeds in enumerate(seed_groups):
            for other in seed_groups[i+1:]:
                self.assertFalse(set(seeds)&set(other))
        counts = {s:sum(c["split"]==s for c in self.cases) for s in self.manifest["specification"]["splits"]}
        self.assertEqual(counts,{"train_reserved":12,"development":12,"validation":6,"test":6})

    def test_families_have_positive_witness_or_proven_negative_label(self):
        for case in self.cases:
            certificate = case["certificate"]
            if case["feasible"]:
                self.assertEqual(certificate["kind"],"conservative_horizontal_grid_witness")
                route = certificate["waypoints_m"]
                self.assertEqual(route[0],case["start_m"])
                self.assertEqual(route[-1],case["goal_m"])
                rectangles = inflated_rectangles(case["obstacles"],certificate["radius_m"])
                for a,b in zip(route,route[1:]):
                    self.assertTrue(segment_clear(a,b,rectangles),case["id"])
                    self.assertTrue(all(-9<=v<=9 for v in (*a[:2],*b[:2])))
            else:
                self.assertEqual(case["family"],"blocked_goal")
                self.assertEqual(certificate["kind"],"goal_inside_solid")
                self.assertFalse(certificate["waypoints_m"])
                # The task succeeds anywhere in a 0.5 m goal ball, not only at
                # its centre. Every generated negative control encloses that
                # entire ball in an actual solid, so its label is meaningful.
                self.assertTrue(any(all(abs(case["goal_m"][i]-o["center_m"][i])+.5 <= o["size_m"][i]/2
                                            for i in range(3)) for o in case["obstacles"]))

    def test_yaw_and_start_goal_vary(self):
        self.assertGreater(len({c["start_yaw_rad"] for c in self.cases}),30)
        self.assertTrue(any(c["start_yaw_rad"]< -pi/2 for c in self.cases))
        self.assertTrue(any(c["start_yaw_rad"]>pi/2 for c in self.cases))
        self.assertGreater(len({tuple(c["start_m"]) for c in self.cases}),30)

    def test_swept_segment_cannot_cut_obstacle_corner(self):
        rectangles = [(0,1,0,1)]
        self.assertFalse(segment_clear((-1,.5),(2,.5),rectangles))
        self.assertFalse(segment_clear((-.1,.9),(.9,-.1),rectangles))
        self.assertFalse(segment_clear((-1,0),(2,0),rectangles))
        self.assertTrue(segment_clear((-1,-.1),(2,-.1),rectangles))

    def test_bad_geometry_and_wrong_feasibility_labels_fail(self):
        case = generate_case("single_block",21001,"development")
        bad = copy.deepcopy(case)
        bad["obstacles"][0]["size_m"][0] = -1
        with self.assertRaises(ValueError):
            path_certificate(bad,self.body)
        bad = copy.deepcopy(case)
        bad["start_m"][0] = float("nan")
        with self.assertRaises(ValueError):
            path_certificate(bad,self.body)
        bad = generate_case("empty",21001,"development")
        bad["feasible"] = False
        with self.assertRaisesRegex(ValueError,"proof"):
            path_certificate(bad,self.body)
        bad = generate_case("blocked_goal",21001,"development")
        bad["feasible"] = True
        with self.assertRaisesRegex(ValueError,"overlaps"):
            path_certificate(bad,self.body)

    def test_grid_failure_does_not_silently_become_negative_control(self):
        case = {"start_m":[-4,0,1.5],"goal_m":[4,0,1.5],"start_yaw_rad":0,"feasible":True,
                "obstacles":[{"center_m":[0,0,1.5],"size_m":[.5,18.6,3]}]}
        with self.assertRaisesRegex(ValueError,"No certified grid path"):
            path_certificate(case,self.body)

    def test_private_cases_and_witnesses_never_enter_drone_config(self):
        config = load_config()
        original = controller_config(config)
        altered = copy.deepcopy(config)
        altered["world"]["obstacles"] = self.cases[0]["obstacles"]
        altered["cases"] = self.cases
        altered["certificate"] = self.cases[0]["certificate"]
        self.assertEqual(original,controller_config(altered))


class ProtocolTests(unittest.TestCase):
    def test_lock_detects_code_changes_without_rewriting_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in FROZEN_FILES:
                p = root/name
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text(name+"\n")
            lock = make_lock(root)
            path = root/"configs/scenarios/protocol_v1.lock.json"
            path.write_text(json.dumps(lock))
            self.assertEqual(verify_lock(root),digest(lock))
            (root/"src/blind_drone/navigation/baseline.py").write_text("changed")
            with self.assertRaisesRegex(ValueError,"baseline.py"):
                verify_lock(root)
            self.assertEqual(json.loads(path.read_text()),lock)

    def test_missing_lock_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,"missing"):
                verify_lock(Path(tmp))


class StudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = build_manifest()

    def reports(self):
        reports = []
        for split in ("development","validation","test"):
            episodes = []
            for case in self.manifest["cases"]:
                if case["split"]!=split:
                    continue
                for policy in ("direct","reactive"):
                    outcome = "success" if case["family"]=="empty" else "collision" if case["family"]=="single_block" and policy=="direct" else "timeout"
                    episodes.append({"case_id":case["id"],"policy":policy,**{k:case[k] for k in ("family","seed","feasible","geometry_sha256")},
                                     "initial_position_m":case["start_m"],"initial_yaw_rad":case["start_yaw_rad"],
                                     "outcome":outcome,"elapsed_s":75,"path_length_m":10})
            reports.append({"split":split,"suite":"seeded","status":"passed","complete_split":True,
                            "checks":{"coverage":{"passed":True}},"source_commit":"0"*40,
                            "protocol_sha256":"lock","manifest_sha256":digest(self.manifest),
                            "episodes":episodes,"summary":summarize(episodes)})
        return reports

    def test_full_study_counts_failures_without_requiring_reactive_perfection(self):
        result = validate_study(self.reports(),self.manifest,"lock")
        self.assertEqual(result["evaluated_episodes"],48)
        self.assertEqual(result["reserved_training_cases"],12)
        self.assertEqual(result["summary_by_split"]["test"]["reactive"]["feasible"]["successes"],1)

    def test_duplicate_missing_partial_and_wrong_provenance_are_rejected(self):
        for mutation in ("duplicate","missing","partial","manifest","commit"):
            reports = self.reports()
            if mutation=="duplicate": reports[0]["episodes"].append(reports[0]["episodes"][0])
            if mutation=="missing": reports[0]["episodes"].pop()
            if mutation=="partial": reports[0]["complete_split"] = False
            if mutation=="manifest": reports[0]["manifest_sha256"] = "wrong"
            if mutation=="commit": reports[0]["source_commit"] = "1"*40
            with self.assertRaises(ValueError,msg=mutation):
                validate_study(reports,self.manifest,"lock")

    def test_false_negative_control_success_and_hidden_dropped_failures_fail(self):
        reports = self.reports()
        episode = next(e for e in reports[0]["episodes"] if not e["feasible"])
        episode["outcome"] = "success"
        reports[0]["summary"] = summarize(reports[0]["episodes"])
        with self.assertRaisesRegex(ValueError,"Impossible"):
            validate_study(reports,self.manifest,"lock")
        reports = self.reports()
        reports[0]["summary"]["reactive"]["feasible"]["successes"] = 10
        with self.assertRaisesRegex(ValueError,"Summary"):
            validate_study(reports,self.manifest,"lock")


if __name__ == "__main__":
    unittest.main()
