"""Commit/check conditional fresh 7A geometry; never run navigation or v3 test."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'versions/navigation_v4'), str(ROOT/'versions/efficiency_eval_v1')]
from blind_drone.world.scenarios import digest
from efficiency_design import INDEX, LOCK, build_cases, design_sources, generated_index


def text(value):
    return json.dumps(value, indent=2, allow_nan=False)+'\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--materialize', action='store_true', help='Write ignored geometry fixtures, not navigation outcomes')
    args = parser.parse_args()
    cases = build_cases()
    value = text(generated_index(cases))
    if INDEX.exists() and INDEX.read_text() != value:
        raise ValueError('Fresh dataset commitment differs; never replace a frozen design')
    if not INDEX.exists():
        if args.check:
            raise ValueError('Missing fresh dataset commitment')
        INDEX.write_text(value)
    files = design_sources()
    value = text({'schema_version': 1, 'runtime_ready': False, 'files': files, 'design_sha256': digest(files)})
    if LOCK.exists() and LOCK.read_text() != value:
        raise ValueError('Conditional design lock differs; use a new version, never regenerate silently')
    if not LOCK.exists():
        if args.check:
            raise ValueError('Missing conditional design lock')
        LOCK.write_text(value)
    if args.materialize:
        directory = ROOT/'artifacts/efficiency-eval-fixtures'
        directory.mkdir(parents=True, exist_ok=True)
        for split in ('validation', 'test'):
            (directory/(split+'.json')).write_text(text({'cases': [c for c in cases if c['split'] == split]}))
    print('Conditional geometry commitments verified: 144 fresh cases; no candidate/runtime/evaluation qualified')


if __name__ == '__main__':
    main()
