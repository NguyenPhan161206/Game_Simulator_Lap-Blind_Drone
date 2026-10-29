"""Re-audit complete DATA-04 development raw output without rerunning Webots."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'versions/navigation_v4'), str(ROOT / 'versions/data_occupied_v1'), str(ROOT / 'versions/data_history_v1'), str(ROOT / 'tools')]
from blind_drone.experiments.runtime_v3 import git
from blind_drone.world.scenarios import digest
from blind_drone_data04.audit import audit_data04_pair, summarize
from blind_drone_data04.protocol import inventory, load_spec, select_cases
from review_research_v3 import sha256_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--expected-source', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run = args.run.resolve()
    manifest = json.loads((run / 'result.json').read_text())
    cases, design = select_cases()
    expected = {c['id']: c for c in cases}
    current_inventory = inventory()
    if manifest['status'] != 'complete' or not manifest['integrity_passed']:
        raise ValueError('Study is not complete')
    if manifest['working_tree_dirty'] or manifest['source_commit'] != args.expected_source:
        raise ValueError('Source identity is dirty or differs from expected source')
    if git('rev-parse', 'HEAD') != args.expected_source or git('status', '--porcelain'):
        raise ValueError('Checkout does not match clean expected source')
    if manifest['files'] != current_inventory:
        raise ValueError('DATA-04 runtime inventory mismatch')
    if manifest['development_sha256'] != design or manifest['cases'] != [c['id'] for c in cases]:
        raise ValueError('Development case membership mismatch')
    if len(manifest['attempts']) != 176 or len(manifest['episodes']) != 352:
        raise ValueError('Expected complete 88-case, 352-episode development')
    attempts = {(a['case_id'], a['repeat']): a for a in manifest['attempts']}
    if len(attempts) != 176 or any(a['classification'] != 'valid' or not a['raw_integrity_passed'] for a in attempts.values()):
        raise ValueError('Missing/invalid paired attempts')
    episodes = []
    audits = []
    spec = load_spec()
    for case in cases:
        for repeat in (0, 1):
            attempt = attempts[(case['id'], repeat)]
            folder = Path(attempt['output'])
            if not folder.is_absolute():
                folder = ROOT / folder
            if not folder.exists():
                folder = run / Path(attempt['output']).name
            record = json.loads((folder / 'result.json').read_text())
            if record['status'] != 'complete' or len(record['episodes']) != 2:
                raise ValueError('Pair result incomplete: ' + case['id'])
            actual_case = json.loads((folder / 'case.json').read_text())
            if digest(actual_case) != digest(case):
                raise ValueError('Case fixture changed: ' + case['id'])
            for name, expected_hash in attempt['files_sha256'].items():
                if sha256_file(folder / name) != expected_hash:
                    raise ValueError('Raw output hash mismatch: ' + str(folder / name))
            episodes.extend(record['episodes'])
            audits.append(audit_data04_pair(folder, case, spec, record))
    if episodes != manifest['episodes']:
        raise ValueError('Manifest episode list differs from raw pair results')
    summary = summarize(episodes, cases, audits)
    if summary != manifest['summary']:
        raise ValueError('Independent raw replay summary mismatch')
    review = {'schema_version': 1, 'complete': True, 'raw_audit_passed': True,
              'source_commit': args.expected_source, 'development_sha256': design,
              'inventory_sha256': hashlib.sha256(json.dumps(current_inventory, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
              'cases': len(cases), 'episodes': len(episodes), 'pairs': len(audits), 'summary': summary}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(review, indent=2, allow_nan=False) + '\n')
    print('DATA03_RAW_REVIEW', json.dumps({'cases': len(cases), 'episodes': len(episodes),
                                           'engineering_targets_met': summary['data04']['engineering_targets_met']}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(2)
