"""Privileged v3 design registration and fixtures, never a navigation input.

This is not an evaluation runner. Legacy runtime/configuration is immutable.
"""
import hashlib
import json
import math
import struct
import tomllib
from pathlib import Path

from blind_drone.experiments.protocol_v2 import verify_v2
from blind_drone.world.geometry import path_certificate
from blind_drone.world.minimal_lab import ROOT, load_config
from blind_drone.world.scenarios import digest, generate_case

CONFIG = ROOT / "configs/experiments/range_cadence_v3.toml"
INDEX = ROOT / "configs/scenarios/range_cadence_v3.index.json"
LOCK = ROOT / "configs/scenarios/protocol_v3.design.lock.json"
LEDGER = ROOT / "configs/scenarios/exposure_v3.json"
SPLITS = ("train", "development", "validation", "test")
DESIGN_FILES = (
    "configs/experiments/range_cadence_v3.toml",
    "configs/scenarios/range_cadence_v3.index.json",
    "docs/protocols/range-cadence-v3.md",
    "docs/decisions/0006-range-cadence-protocol-v3.md",
    "docs/research/2026-10-27-range-cadence-related-work.md",
    "src/blind_drone/experiments/protocol_v3.py",
    "tools/build_research_v3.py",
)


def load_spec():
    spec = tomllib.loads(CONFIG.read_text())
    validate_spec(spec)
    return spec


def validate_spec(spec):
    if spec["schema_version"] != 3 or spec["runtime_ready"] is not False:
        raise ValueError("Design-only v3 cannot authorize runtime evaluation")
    if set(spec["splits"]) != set(SPLITS):
        raise ValueError("Exactly four disjoint splits are required")
    periods = (spec["reference_period_ms"], spec["candidate_period_ms"])
    if periods != (32, 64) or any(p % spec["control_period_ms"] for p in periods):
        raise ValueError("Only the prespecified 32/64 ms comparison is registered")
    if max(periods) / 1000 >= spec["range_max_age_s"]:
        raise ValueError("Acquisition period must fit the common freshness threshold")
    if spec["range_count"] != 10 or struct.calcsize(spec["budget"]["range_packet_format"]) != spec["budget"]["range_packet_bytes"]:
        raise ValueError("Range accounting encoding mismatch")
    q = spec["quality"]
    if not 0 < q["one_sided_alpha"] < 1 or not 0 < q["maximum_adverse_pair_probability"] < 1:
        raise ValueError("Invalid confidence/margin")
    seen = set()
    for split in SPLITS:
        values = spec["splits"][split]
        if any(type(values[k]) is not int or values[k] <= 0 for k in ("first_seed", "feasible_cases", "negative_cases")):
            raise ValueError("Positive integer seeds/counts required")
        seeds = set(range(values["first_seed"], values["first_seed"] + values["feasible_cases"] + values["negative_cases"]))
        if seen & seeds:
            raise ValueError("Overlapping v3 case seeds")
        seen.update(seeds)
    c = spec["controls"]
    v2 = tomllib.loads((ROOT / c["policy_config_source"]).read_text())["navigation_v2"]
    lab = load_config()
    for key in ("speed_m_s", "scan_yaw_rad_s", "initial_scan_s", "replan_period_s"):
        if c[key] != v2[key]:
            raise ValueError("Mapped reference control drift: " + key)
    if spec["pose_period_ms"] != lab["sensor_period_ms"] or spec["control_period_ms"] != lab["basic_time_step_ms"]:
        raise ValueError("Pose/control cadence drift")
    for key in ("max_cells", "max_expansions"):
        if spec["budget"][key] != v2[key]:
            raise ValueError("Mapped reference budget drift")


def task_fingerprint(case):
    """Canonical task geometry under translation, quarter-turns and reflection.

    Ignores yaw conservatively: same task with another yaw is still duplicate.
    This does not prove separation of topology or family distributions.
    """
    start = case["start_m"]
    candidates = []
    for mirror in (-1, 1):
        for quarter in range(4):
            def point(p):
                x, y = p[0] - start[0], (p[1] - start[1]) * mirror
                for _ in range(quarter):
                    x, y = -y, x
                return [round(x, 6) + 0.0, round(y, 6) + 0.0, round(p[2] - start[2], 6) + 0.0]
            blocks = []
            for block in case["obstacles"]:
                sx, sy, sz = block["size_m"]
                size = [sy, sx, sz] if quarter % 2 else [sx, sy, sz]
                blocks.append([point(block["center_m"]), size])
            candidates.append(json.dumps([point(case["goal_m"]), sorted(blocks)], separators=(",", ":")))
    return hashlib.sha256(min(candidates).encode()).hexdigest()


def family_for_seed(seed, families):
    bits = hashlib.sha256(f"range_cadence_v3:family:{seed}".encode()).digest()
    return families[int.from_bytes(bits, "big") % len(families)]


def check_disjoint(cases, exposed):
    """Reject, never silently drop/reseed an inconvenient case."""
    seen_geometry = {case["geometry_sha256"] for case in exposed}
    seen_tasks = {task_fingerprint(case) for case in exposed}
    seen_seeds = {case["seed"] for case in exposed}
    ids = set()
    for case in cases:
        fingerprint = task_fingerprint(case)
        if case["id"] in ids or case["seed"] in seen_seeds:
            raise ValueError("Duplicate case ID or seed")
        if case["geometry_sha256"] in seen_geometry or fingerprint in seen_tasks:
            raise ValueError("Duplicate geometry or equivalent transformed task")
        ids.add(case["id"])
        seen_seeds.add(case["seed"])
        seen_geometry.add(case["geometry_sha256"])
        seen_tasks.add(fingerprint)


def build_cases(spec=None):
    spec = load_spec() if spec is None else spec
    validate_spec(spec)
    c = spec["data"]
    body = load_config()["vehicle"]["body_size_m"]
    cases = []
    for split in SPLITS:
        values = spec["splits"][split]
        for i in range(values["feasible_cases"] + values["negative_cases"]):
            seed = values["first_seed"] + i
            family = family_for_seed(seed, c["feasible_families"]) if i < values["feasible_cases"] else c["negative_family"]
            case = generate_case(family, seed, split)
            case["certificate"] = path_certificate(case, body, c["witness_step_m"], c["witness_margin_m"], c["witness_bounds_m"])
            cases.append(case)
    exposed = []
    for name in ("seeded_v1.json", "observed_v2.json"):
        exposed.extend(json.loads((ROOT / "configs/scenarios" / name).read_text())["cases"])
    check_disjoint(cases, exposed)
    return cases


def index_for_cases(cases):
    return {
        "schema_version": 3,
        "name": "range_cadence_v3",
        "generator_source_sha256": hashlib.sha256((ROOT / "src/blind_drone/world/scenarios.py").read_bytes()).hexdigest(),
        "cases": [{**{key: case[key] for key in ("id", "split", "seed", "family", "feasible", "geometry_sha256")},
                   "task_sha256": task_fingerprint(case), "case_sha256": digest(case),
                   "certificate_kind": case["certificate"]["kind"]} for case in cases],
    }


def ledger_genesis():
    return {"event_id": "v3-design-registration", "date": "2026-10-27",
            "actor": "Codex", "source": "9cf51ade2d11b9c2e1520517b18d6a0947785567",
            "splits": list(SPLITS), "purpose": "design_and_automated_geometry_audit",
            "access": "spec_and_index_human; geometry_and_certificates_programmatic_only",
            "outcomes_viewed": False, "navigation_executed": False,
            "note": "v1/v2 outcomes exposed; v3 public seeds and generator, no v3 outcome/trajectory used for tuning"}


def verify_ledger(path=LEDGER):
    value = json.loads(Path(path).read_text())
    events = value.get("events", [])
    if value.get("schema_version") != 3 or not events or events[0] != ledger_genesis():
        raise ValueError("Exposure ledger genesis mismatch")
    ids = set()
    for event in events:
        required = {"event_id", "date", "actor", "source", "splits", "purpose", "access", "outcomes_viewed", "navigation_executed", "note"}
        if not required <= event.keys() or event["event_id"] in ids:
            raise ValueError("Incomplete/duplicate exposure event")
        if not event["splits"] or not set(event["splits"]) <= set(SPLITS):
            raise ValueError("Unknown exposure split")
        if any(type(event[key]) is not bool for key in ("outcomes_viewed", "navigation_executed")):
            raise ValueError("Exposure flags must be explicit booleans")
        if not all(isinstance(event[k], str) and event[k].strip() for k in ("event_id", "date", "actor", "source", "purpose", "access", "note")):
            raise ValueError("Empty exposure provenance")
        ids.add(event["event_id"])
    return len(events)


def design_hashes():
    return {"schema_version": 3, "lock_kind": "design_only", "legacy_v2": verify_v2(),
            "runtime_ready": False, "ledger_genesis_sha256": digest(ledger_genesis()),
            "files": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in DESIGN_FILES}}


def verify_design():
    if not LOCK.exists() or json.loads(LOCK.read_text()) != design_hashes():
        raise ValueError("V3 design lock missing/mismatch; never replace a frozen lock")
    load_spec()
    verify_ledger()
    return digest(json.loads(LOCK.read_text()))


def require_evaluation_ready():
    verify_design()
    raise ValueError("V3 runtime not implemented/frozen: evaluation is disabled; design lock alone is insufficient")


def adverse_upper_bound(adverse, n, alpha=0.05):
    """One-sided exact binomial bound, not a simulation result or power claim."""
    if type(adverse) is not int or type(n) is not int or not 0 <= adverse <= n or n <= 0 or not 0 < alpha < 1:
        raise ValueError("Invalid binomial counts/alpha")
    if adverse == n:
        return 1.0
    if adverse == 0:
        return -math.expm1(math.log(alpha) / n)
    def cdf(p):
        logs = [math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
                + k * math.log(p) + (n - k) * math.log1p(-p) for k in range(adverse + 1)]
        top = max(logs)
        return math.exp(top) * sum(math.exp(term - top) for term in logs)
    lo, hi = 0.0, 1.0
    for _ in range(64):
        mid = (lo + hi) / 2
        if mid == lo or mid == hi:
            break
        if cdf(mid) > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2
