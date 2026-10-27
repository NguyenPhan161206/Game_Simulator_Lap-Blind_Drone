"""Generate/check design fixtures only; never launch Webots or train a policy."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from blind_drone.experiments.protocol_v3 import (
    INDEX, LEDGER, LOCK, SPLITS, build_cases, design_hashes, index_for_cases,
    ledger_genesis, require_evaluation_ready, verify_design,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--evaluate", action="store_true", help="always rejected: runtime v3 is not ready")
    args = parser.parse_args()
    if args.evaluate:
        require_evaluation_ready()
    if args.check and args.freeze:
        parser.error("--check and --freeze are mutually exclusive")
    if args.freeze and LOCK.exists():
        raise ValueError("Refusing to replace existing v3 design lock")
    # Check legacy immutability before doing privileged fixture generation.
    from blind_drone.experiments.protocol_v2 import verify_v2
    verify_v2()
    cases = build_cases()
    index_text = json.dumps(index_for_cases(cases), indent=2) + "\n"
    if args.check or LOCK.exists():
        if not INDEX.exists() or INDEX.read_text() != index_text:
            raise ValueError("V3 generated index differs from registered design")
    else:
        INDEX.write_text(index_text)
        if not LEDGER.exists():
            LEDGER.write_text(json.dumps({"schema_version": 3, "events": [ledger_genesis()]}, indent=2) + "\n")
    if args.freeze:
        # Exclusive creation is intentional; an existing lock is never rewritten.
        with LOCK.open("x") as target:
            target.write(json.dumps(design_hashes(), indent=2) + "\n")
    if args.check or LOCK.exists():
        print("Design-only v3:", verify_design())
    if not args.check:
        folder = ROOT / "artifacts/research-v3-fixtures"
        folder.mkdir(parents=True, exist_ok=True)
        for split in SPLITS:
            (folder / (split + ".json")).write_text(json.dumps({"schema_version": 3, "cases": [c for c in cases if c["split"] == split]}, indent=2) + "\n")
        print("Generated complete fixtures in artifacts/research-v3-fixtures (ignored; not navigation inputs)")
    print("PASS: 480 registered cases checked; no v3 navigation/evaluation/training executed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, FileNotFoundError) as error:
        raise SystemExit(str(error))
