"""Build/check additive assets; bind and lock only from complete reviewed evidence."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'versions/navigation_v4'), str(ROOT/'versions/initialization_aa_v1'),
    str(ROOT/'versions/retention_cold_v1'), str(ROOT/'versions/sensor_pilots_v1'),
    str(ROOT/'versions/efficiency_eval_v1'), str(ROOT/'versions/efficiency_runtime_v1'), str(ROOT/'tools')]
from blind_drone.experiments.runtime_v3 import verify_runtime
from blind_drone.world.scenarios import digest
from blind_drone_efficiency.protocol import (BINDING, LOCK, PREFLIGHT, FIXTURE_DIR,
    generated_outputs, fresh_cases, expected_binding, inventory, sha, verify_design, verify_lock)


def write_once(path, value, check=False):
    if path.exists():
        if path.read_text() != value:
            raise ValueError('Immutable asset/evidence differs: '+str(path))
    elif check:
        raise ValueError('Missing registered asset: '+str(path))
    else:
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--bind', action='store_true')
    parser.add_argument('--lock-from-preflight', type=Path)
    args = parser.parse_args()
    verify_runtime()
    outputs, development = generated_outputs()
    for path, value in outputs.items():
        write_once(path, value, args.check)
    if args.bind:
        write_once(BINDING, json.dumps(expected_binding(), indent=2)+'\n', args.check)
    if args.lock_from_preflight:
        proof = json.loads(args.lock_from_preflight.read_text())
        if (proof.get('protocol_version') != 'efficiency_runtime_v1' or not proof['complete']
                or not proof['raw_audit_passed'] or proof['split'] != 'development' or proof['episodes'] != 48
                or not proof['preflight_equivalence']['met'] or proof['runtime_sha256'] != digest(inventory())
                or proof['binding_sha256'] != sha(BINDING) or proof['design_lock_sha256'] != verify_design()):
            raise ValueError('Complete source-matched equivalence preflight required')
        write_once(PREFLIGHT, args.lock_from_preflight.read_text(), args.check)
        lock = {'schema_version': 1, 'runtime_sha256': digest(inventory()), 'binding_sha256': sha(BINDING),
                'design_lock_sha256': verify_design(), 'preflight_review_sha256': sha(PREFLIGHT),
                'preflight_source_commit': proof['source_commit'], 'heldout_runtime_ready': True}
        write_once(LOCK, json.dumps(lock, indent=2)+'\n', args.check)
    if LOCK.exists():
        verify_lock()
    if not args.check:
        FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
        cases = development+fresh_cases()
        for split in ('development', 'validation', 'test'):
            (FIXTURE_DIR/(split+'.json')).write_text(json.dumps({'cases': [c for c in cases if c['split'] == split]}, indent=2)+'\n')
    print('Efficiency assets verified; binding:', BINDING.exists(), 'held-out lock:', LOCK.exists())


if __name__ == '__main__':
    main()
