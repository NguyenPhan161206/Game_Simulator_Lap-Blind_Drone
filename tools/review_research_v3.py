"""Review downloaded v3 evidence without modifying the frozen runtime or raw data.

This is offline postprocessing, never imported by the evaluated controller or
runner. Path relocation occurs in a deep copy; the original result is hashed.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from blind_drone.evaluation.cadence import classify_attempt
from blind_drone.evaluation.cadence_audit import audit_study
from blind_drone.experiments.protocol_v3 import load_spec, verify_design
from blind_drone.experiments.runtime_v3 import inventory, select_cases, verify_runtime
from blind_drone.world.scenarios import digest


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def validate_identity(report, split, source, design, runtime, files, case_ids):
    if split not in ('development', 'validation', 'test'):
        raise ValueError('Train remains reserved')
    if len(source) != 40 or any(c not in '0123456789abcdef' for c in source):
        raise ValueError('Expected source must be a full commit SHA from CI metadata')
    if split != 'development' and not runtime:
        raise ValueError('Held-out evidence requires a runtime lock at execution')
    expected = {'schema_version': 3, 'split': split, 'source_commit': source,
                'design_sha256': design, 'runtime_sha256': runtime,
                'status': 'complete', 'complete_split': True,
                'working_tree_dirty': False, 'integrity_passed': True}
    for key, value in expected.items():
        if key not in report or type(report[key]) is not type(value) or report[key] != value:
            raise ValueError('Study identity/completeness mismatch: ' + key)
    if report.get('files') != files or report.get('cases') != case_ids:
        raise ValueError('Runtime inventory or complete split membership mismatch')


def checked_path(root, name):
    root = Path(root).resolve()
    if not isinstance(name, str) or Path(name).name != name or name in ('.', '..'):
        raise ValueError('Unsafe artifact basename')
    path = root / name
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError('Artifact path escapes evidence directory')
    return path


def relocate_and_verify(report, directory, cases):
    """Verify bytes/provenance before replay; preserve the input report exactly."""
    root = Path(directory).resolve()
    expected_cases = {c['id']: c for c in cases}
    relocated = deepcopy(report)
    for attempt in relocated['attempts']:
        case_id = attempt['case_id']
        if case_id not in expected_cases or type(attempt['repeat']) is not int or attempt['repeat'] not in (0, 1):
            raise ValueError('Unknown case/repeat in attempt')
        if type(attempt['attempt']) is not int or attempt['attempt'] not in (0, 1):
            raise ValueError('Unregistered retry number')
        if type(attempt['returncode']) is not int or type(attempt['watchdog']) is not bool:
            raise ValueError('Ambiguous process status')
        name = f"{case_id}-r{attempt['repeat']}-a{attempt['attempt']}"
        if Path(attempt['output']).name != name:
            raise ValueError('Attempt directory identity mismatch')
        folder = checked_path(root, name)
        if not folder.is_dir():
            raise ValueError('Missing attempt evidence')
        hashes = attempt.get('files_sha256', {})
        if 'console.log' not in hashes:
            raise ValueError('Missing raw console commitment')
        for filename, sha in hashes.items():
            if sha256_file(checked_path(folder, filename)) != sha:
                raise ValueError('Raw file hash mismatch: ' + filename)
        console = checked_path(folder, 'console.log').read_text(errors='replace')
        result_path = checked_path(folder, 'result.json')
        raw_result = json.loads(result_path.read_text()) if result_path.exists() else None
        if raw_result != attempt['result']:
            raise ValueError('Pair result differs from committed study attempt')
        kind = classify_attempt(raw_result, console, attempt['watchdog'])
        if kind == 'valid' and attempt['returncode'] != 0:
            kind = 'unresolved'
        if kind != attempt['classification']:
            raise ValueError('Attempt failure classification mismatch')
        if kind == 'valid':
            required = {'case.json', 'result.json', 'evaluation.jsonl'}
            required.update(name for row in raw_result['episodes'] for name in row['files_bytes'])
            if not required <= set(hashes):
                raise ValueError('Missing raw file commitments')
            if attempt.get('raw_integrity_passed') is not True:
                raise ValueError('Runtime did not attest raw pair integrity')
            case_path = checked_path(folder, 'case.json')
            if digest(json.loads(case_path.read_text())) != digest(expected_cases[case_id]):
                raise ValueError('Pair fixture differs from registered case')
        attempt['output'] = str(folder)
    return relocated


def review(directory, split, source):
    directory = Path(directory).resolve()
    result_path = checked_path(directory, 'result.json')
    result = json.loads(result_path.read_text())
    design, runtime = verify_design(), verify_runtime()
    cases, _ = select_cases(split)
    # Original development evidence predates the additive runtime lock. This
    # exception never applies to validation/test and still pins exact file hashes.
    executed_runtime = None if split == 'development' and result.get('runtime_sha256') is None else runtime
    validate_identity(result, split, source, design, executed_runtime, inventory(), [c['id'] for c in cases])
    relocated = relocate_and_verify(result, directory, cases)
    audit_study(relocated, cases, load_spec())
    return {'schema_version': 3, 'kind': 'offline_frozen_v3_review', 'split': split,
            'source_commit': source, 'raw_result_sha256': sha256_file(result_path),
            'design_sha256': design, 'runtime_sha256': runtime,
            'execution_runtime_sha256': result['runtime_sha256'],
            'review_tool_sha256': sha256_file(Path(__file__)),
            'complete': True, 'raw_audit_passed': True,
            'study_outcome': 'passed' if result['gate']['met'] else 'not_met',
            'test_qualified': split == 'validation' and result['gate']['met'] is True,
            'cases': len(cases), 'episodes': len(result['episodes']),
            'attempts': len(result['attempts']), 'gate': result['gate'],
            'path_relocation': 'memory_only; original result and raw files unchanged'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--expected-split', choices=('development', 'validation', 'test'), required=True)
    parser.add_argument('--expected-source', required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    output = args.output or args.directory / 'review.json'
    if output.resolve() == (args.directory / 'result.json').resolve() or output.exists():
        parser.error('Review must use a fresh output and must not overwrite evidence')
    try:
        value = review(args.directory, args.expected_split, args.expected_source)
    except (ValueError, OSError, KeyError, TypeError) as error:
        print('Incomplete/unverifiable v3 study:', error, file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    print('V3_REVIEW ' + json.dumps({k: v for k, v in value.items() if k != 'gate'}, separators=(',', ':')))
    # A valid negative research result is not an infrastructure/job failure.
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
