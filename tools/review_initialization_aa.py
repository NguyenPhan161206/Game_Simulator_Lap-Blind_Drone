"""Independently review complete A/A raw evidence; never rerun Webots."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'versions/navigation_v4'), str(ROOT/'versions/initialization_aa_v1'), str(ROOT/'tools')]
from blind_drone.experiments.runtime_v3 import git, verify_runtime
from blind_drone.evaluation.cadence import classify_attempt
from blind_drone.world.scenarios import digest
from blind_drone_aa.audit import audit_attempt, summarize
from blind_drone_aa.protocol import inventory, load_spec, schedule, select_cases
from review_research_v3 import sha256_file


def safe_file(directory, name):
    if Path(name).name != name or not (directory/name).resolve().is_relative_to(directory.resolve()):
        raise ValueError('Raw path escapes attempt directory')
    return directory/name


def check_attempt_classification(attempt, console):
    actual = classify_attempt(attempt['result'], console, attempt['watchdog'])
    if actual == 'valid' and attempt['returncode'] != 0:
        actual = 'unresolved'
    if actual != attempt['classification']:
        raise ValueError('Attempt classification differs from raw evidence')


def review(run, source):
    verify_runtime()
    if len(source) != 40 or any(c not in '0123456789abcdef' for c in source):
        raise ValueError('Full expected source SHA required')
    if git('rev-parse', 'HEAD') != source or git('status', '--porcelain'):
        raise ValueError('Reviewer requires clean expected source checkout')
    manifest = json.loads((run/'result.json').read_text())
    cases, design = select_cases()
    files = inventory()
    if (manifest['status'] != 'complete' or not manifest['integrity_passed'] or not manifest['complete_split'] or
            manifest['source_commit'] != source or manifest['working_tree_dirty'] or manifest['files'] != files or
            manifest['runtime_sha256'] != digest(files) or manifest['development_sha256'] != design or
            manifest['cases'] != [c['id'] for c in cases] or manifest['split'] != 'development'):
        raise ValueError('Incomplete/changed A/A source/design/membership')
    locks = {str(p.relative_to(ROOT)): sha256_file(p) for p in sorted((ROOT/'configs/scenarios').glob('*.lock.json'))}
    if manifest['locks_file_sha256'] != locks:
        raise ValueError('Legacy lock bytes differ')
    spec = load_spec()
    expected = {(c['id'], mode, repeat, arm) for c, mode, repeat, arm in schedule(cases)}
    index = {c['id']: c for c in cases}; groups = {}; rows = []
    for attempt in manifest['attempts']:
        key = attempt['case_id'], attempt['mode'], attempt['repeat'], attempt['arm']
        if key not in expected:
            raise ValueError('Unknown A/A attempt')
        group = groups.setdefault(key, [])
        if attempt['attempt'] != len(group) or len(group) >= 2 or (group and group[-1]['classification'] != 'infrastructure'):
            raise ValueError('Invalid retry history')
        group.append(attempt)
        folder = run/attempt['output']
        if Path(attempt['output']).name != attempt['output'] or not folder.resolve().is_relative_to(run.resolve()):
            raise ValueError('Attempt path escapes run')
        for name, expected_hash in attempt['files_sha256'].items():
            if sha256_file(safe_file(folder, name)) != expected_hash:
                raise ValueError('Raw hash mismatch: '+name)
        check_attempt_classification(attempt, safe_file(folder, 'console.log').read_text(errors='replace'))
        if attempt['classification'] == 'infrastructure':
            if attempt['result'] is not None:
                raise ValueError('Infrastructure attempt has algorithm result')
            continue
        if attempt['classification'] != 'valid' or not attempt['raw_integrity_passed'] or attempt['returncode'] != 0:
            raise ValueError('Unresolved attempt')
        case = index[attempt['case_id']]
        if json.loads((folder/'case.json').read_text()) != case:
            raise ValueError('Raw case changed')
        result = json.loads((folder/'result.json').read_text())
        required = {'case.json', 'result.json', 'evaluation.jsonl', 'console.log'}
        for row in result['episodes']:
            token = row['arm']+str(row['repeat'])
            required.update(token+suffix for suffix in ('-acquisition.jsonl', '-range.bin', '-decisions.jsonl', '-initialization.json'))
        if not required.issubset(attempt['files_sha256']):
            raise ValueError('Missing raw hash coverage')
        if result != attempt['result'] or result['development_sha256'] != design:
            raise ValueError('Raw result/design changed')
        audits = audit_attempt(folder, case, spec, result, attempt['mode'], attempt['repeat'], attempt['arm'])
        rows.extend({'mode': attempt['mode'], 'episode': row, 'folder': attempt['output'], 'audit': audit}
                    for row, audit in zip(result['episodes'], audits))
    if set(groups) != expected or any(group[-1]['classification'] != 'valid' for group in groups.values()) or rows != manifest['rows']:
        raise ValueError('Missing/duplicate A/A process or episode evidence')
    summary = summarize([r | {'folder': run/r['folder']} for r in rows], cases, spec)
    if summary != manifest['summary'] or manifest['study_outcome'] != ('met' if summary['met'] else 'not_met'):
        raise ValueError('Independent A/A summary mismatch')
    return {'schema_version': 1, 'complete': True, 'raw_audit_passed': True, 'source_commit': source,
            'raw_result_sha256': sha256_file(run/'result.json'), 'runtime_sha256': digest(files),
            'development_sha256': design, 'cases': len(cases), 'episodes': len(rows),
            'processes': len(expected), 'attempts': len(manifest['attempts']), 'summary': summary}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--expected-source', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = review(args.run.resolve(), args.expected_source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print('AA_RAW_REVIEW', result['episodes'], 'episodes', result['summary']['gates'])


if __name__ == '__main__':
    main()
