"""Build/check only the isolated DATA-04 development assets."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'versions/navigation_v4'), str(ROOT / 'versions/data_history_v1')]
from blind_drone.experiments.runtime_v3 import verify_runtime
from blind_drone_data04.protocol import FIXTURE, generated_outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    verify_runtime()
    outputs, cases = generated_outputs()
    for path, content in outputs.items():
        if path.exists():
            if path.read_text() != content:
                raise ValueError('DATA-04 generated asset differs; preserve prior evidence: ' + str(path))
        elif args.check:
            raise ValueError('Missing DATA-04 generated asset: ' + str(path))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    if not args.check:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps({'schema_version': 1, 'cases': cases}, indent=2) + '\n')
    print('DATA-04 development assets verified:', len(cases), 'cases; frozen v3/v4 sources unchanged')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(2)
