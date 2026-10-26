"""Frozen engineering protocol verification. Never imported by drone/navigation."""
import hashlib
import json

from blind_drone.world.minimal_lab import ROOT
from blind_drone.world.scenarios import MANIFEST, digest

LOCK = ROOT / "configs/scenarios/protocol_v1.lock.json"
FROZEN_FILES = (
    "configs/lab_v1.toml", "configs/navigation_v1.toml", "configs/scenario_suite_v1.toml",
    "configs/scenarios/seeded_v1.json",
    "src/blind_drone/navigation/baseline.py", "src/blind_drone/contracts/navigation.py",
    "src/blind_drone/contracts/runtime.py", "src/blind_drone/control/stabilizer.py",
    "src/blind_drone/adapters/webots/drone.py", "src/blind_drone/adapters/webots/navigation_lab.py",
    "src/blind_drone/evaluation/episode.py", "src/blind_drone/evaluation/study.py", "src/blind_drone/world/geometry.py",
    "src/blind_drone/world/scenarios.py", "src/blind_drone/world/minimal_lab.py",
    "src/blind_drone/experiments/protocol.py", "tools/run_webots.py", "tools/check_study.py",
    "simulation/webots/worlds/minimal_lab.wbt", "simulation/webots/protos/BlindDrone.proto",
)


def make_lock(root=ROOT):
    return {"schema_version":1,"name":"seeded_horizontal_v1_frozen_protocol",
            "baseline_source_commit":"555f59fd856f73a3f44018ce334c0faa2ef7c0b6",
            "rule":"No tuning on validation/test outcomes; changed frozen files require a new protocol version.",
            "files_sha256":{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in FROZEN_FILES}}


def verify_lock(root=ROOT):
    path = root / "configs/scenarios/protocol_v1.lock.json"
    if not path.is_file():
        raise ValueError("Frozen protocol missing; generate and freeze before simulator evaluation")
    recorded = json.loads(path.read_text())
    current = make_lock(root)
    if recorded != current:
        different = [name for name,value in current["files_sha256"].items() if recorded.get("files_sha256",{}).get(name)!=value]
        raise ValueError("Frozen protocol mismatch: " + ", ".join(different))
    return digest(recorded)


def select_suite(split, requested_case=None):
    lock_hash = verify_lock()
    manifest = json.loads(MANIFEST.read_text())
    if split not in {"development","validation","test"}:
        raise ValueError("train_reserved is not evaluated in this stage")
    cases = [c for c in manifest["cases"] if c["split"] == split]
    if requested_case:
        cases = [c for c in cases if c["id"] == requested_case]
    if not cases:
        raise ValueError("No case matches split/case selection")
    return manifest,cases,lock_hash
