"""Generate/check seeded scenarios and create an immutable-by-default protocol lock."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from blind_drone.experiments.protocol import LOCK, make_lock, verify_lock
from blind_drone.world.scenarios import MANIFEST, build_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true")
    parser.add_argument("--freeze",action="store_true")
    args = parser.parse_args()
    try:
        manifest = build_manifest()
        text = json.dumps(manifest,indent=2,allow_nan=False) + "\n"
        if args.check:
            if not MANIFEST.is_file() or MANIFEST.read_text()!=text:
                raise ValueError("Scenario manifest differs from deterministic generator")
        else:
            if LOCK.exists() and (not MANIFEST.exists() or MANIFEST.read_text()!=text):
                raise ValueError("Refusing to overwrite scenarios under frozen protocol; version the protocol")
            MANIFEST.parent.mkdir(parents=True,exist_ok=True)
            MANIFEST.write_text(text)
        if args.freeze:
            if LOCK.exists():
                raise ValueError("Protocol lock already exists; refusing to replace it")
            LOCK.write_text(json.dumps(make_lock(),indent=2)+"\n")
        if LOCK.exists():
            print("Frozen protocol SHA256:",verify_lock())
        elif args.check:
            raise ValueError("Protocol has not been frozen")
        print("PASS:",len(manifest["cases"]),"deterministic, geometry-checked cases")
        return 0
    except (ValueError,OSError) as error:
        print("FAIL:",error,file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
