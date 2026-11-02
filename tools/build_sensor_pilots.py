"""Build/check separate registered sensor pilot assets without changing old locks."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'versions/navigation_v4'), str(ROOT/'versions/sensor_pilots_v1'), str(ROOT/'versions/retention_cold_v1'), str(ROOT/'versions/initialization_aa_v1')]
from blind_drone.experiments.runtime_v3 import verify_runtime
from blind_drone_sensor_pilots.protocol import FIXTURE, generated_outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    verify_runtime()
    outputs, cases = generated_outputs()
    for path, value in outputs.items():
        if path.exists():
            if path.read_text() != value:
                raise ValueError('sensor pilot asset differs; preserve old source/evidence: ' + str(path))
        elif args.check:
            raise ValueError('Missing sensor pilot asset: ' + str(path))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value)
    if not args.check:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps({'cases': cases}, indent=2) + '\n')
    print('sensor pilot development assets verified:', len(cases), 'exposed cases')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
