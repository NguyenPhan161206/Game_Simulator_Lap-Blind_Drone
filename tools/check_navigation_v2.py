"""Check complete frozen v2 study, including failures and resource counters."""
import argparse
import json
from pathlib import Path
import sys
import tomllib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from blind_drone.evaluation.study_v2 import validate_v2
from blind_drone.experiments.protocol_v2 import CONFIG,MANIFEST,verify_v2


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("reports",nargs=3,type=Path);p.add_argument("--output",type=Path,default=ROOT/"artifacts/v2-study.json")
    args=p.parse_args()
    try:
        spec=tomllib.loads(CONFIG.read_text())
        result=validate_v2([json.loads(p.read_text()) for p in args.reports],json.loads(MANIFEST.read_text()),verify_v2(),spec["policies"],spec["navigation_v2"]["max_cells"])
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+"\n")
        print("V2_STUDY "+json.dumps(result,separators=(",",":")))
        return 0
    except (OSError,ValueError,KeyError) as error:print("FAIL:",error,file=sys.stderr);return 1


if __name__=="__main__":raise SystemExit(main())
