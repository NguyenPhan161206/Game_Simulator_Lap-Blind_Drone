"""Aggregate all frozen split results; missing/failing/partial runs are errors."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from blind_drone.evaluation.study import validate_study
from blind_drone.experiments.protocol import verify_lock
from blind_drone.world.scenarios import MANIFEST


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("reports",nargs=3,type=Path)
    p.add_argument("--output",type=Path,default=ROOT/"artifacts/seeded-study.json")
    args = p.parse_args()
    try:
        reports = [json.loads(path.read_text()) for path in args.reports]
        result = validate_study(reports,json.loads(MANIFEST.read_text()),verify_lock())
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+"\n")
        print("SEEDED_STUDY_RESULT " + json.dumps(result))
        return 0
    except (OSError,ValueError,KeyError) as error:
        print("FAIL:",error,file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
