"""Generate/check v2 files without modifying any v1 frozen file."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from blind_drone.experiments.protocol_v2 import LOCK, candidate_hashes, outputs, verify_v2


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check",action="store_true");p.add_argument("--freeze",action="store_true")
    args=p.parse_args()
    for path,text in outputs().items():
        if args.check or LOCK.exists():
            if not path.exists() or path.read_text()!=text:raise SystemExit("Stale/locked file: "+str(path))
        else:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    if args.freeze:
        if LOCK.exists():raise SystemExit("Refusing to replace existing v2 lock")
        LOCK.write_text(json.dumps(candidate_hashes(),indent=2)+"\n")
    if LOCK.exists():print("Frozen v2:",verify_v2())
    else:print("Candidate development only; fresh splits disabled")
    return 0


if __name__=="__main__":raise SystemExit(main())
