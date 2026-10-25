"""Build or check generated Webots files from the prototype preset."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from blind_drone.world.minimal_lab import load_config, outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    failed = False
    for path, content in outputs(load_config()).items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                print("STALE:", path.relative_to(ROOT))
                failed = True
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print("WROTE:", path.relative_to(ROOT))
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
