"""Run separately registered cold-isolated efficiency runtime on real Webots; development only."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'versions/efficiency_eval_v1'), str(ROOT/'versions/efficiency_runtime_v1'),  str(ROOT/'versions/navigation_v4'), str(ROOT/'versions/sensor_pilots_v1'), str(ROOT/'versions/retention_cold_v1'), str(ROOT/'versions/initialization_aa_v1'), str(ROOT/'tools')]
from blind_drone.evaluation.cadence import classify_attempt
from blind_drone.experiments.runtime_v3 import git, verify_runtime
from blind_drone.world.scenarios import digest
from blind_drone_efficiency.audit import audit_attempt, summarize, compare_preflight
from blind_drone_efficiency.protocol import WORLD, generated_outputs, inventory, load_spec, schedule, select_cases, verify_authorization, verify_design, verify_lock, BINDING, sha, claim_exposure
from review_research_v3 import sha256_file
from run_webots import find_webots


def run_process(executable, env, output, timeout):
    home = Path(executable).parent
    binary = home/'bin/webots-bin'
    if binary.exists():
        executable = str(binary)
        env['WEBOTS_HOME'] = str(home)
        env['LD_LIBRARY_PATH'] = str(home/'lib/webots') + (':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
        env.setdefault('QT_QPA_PLATFORM', 'xcb')
        env['WEBOTS_TMPDIR'] = env['TMPDIR'] = '/tmp'
    env['BLIND_DRONE_OUTPUT'] = str(output)
    command = [executable, '--batch', '--stdout', '--stderr', '--no-rendering', '--mode=fast', str(WORLD)]
    started = time.monotonic(); timed_out = False
    with (output/'console.log').open('w') as log:
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True; os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL); process.wait()
    try:
        result = json.loads((output/'result.json').read_text())
    except (OSError, ValueError):
        result = None
    kind = classify_attempt(result, (output/'console.log').read_text(errors='replace'), timed_out)
    if kind == 'valid' and process.returncode != 0:
        kind = 'unresolved'
    return {'classification': kind, 'returncode': process.returncode, 'watchdog': timed_out,
            'wall_s': time.monotonic()-started, 'command': command, 'result': result,
            'files_sha256': {p.name: sha256_file(p) for p in output.iterdir() if p.is_file()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split', choices=('development','validation','test'), default='development')
    parser.add_argument('--case', action='append')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--webots')
    parser.add_argument('--study', choices=('sparse',), default='sparse')
    parser.add_argument('--validation-review', type=Path)
    args = parser.parse_args()
    shared = verify_runtime()
    verify_authorization(args.split, args.validation_review)
    cases, design = select_cases(args.split, args.case, args.study, args.validation_review)
    spec = load_spec(args.study,args.split); outputs, _ = generated_outputs()
    if any(not p.exists() or p.read_text() != value for p, value in outputs.items()):
        raise ValueError('Build/check efficiency runtime assets before execution')
    executable = find_webots(args.webots)
    if not executable or (Path(executable).parent/'resources/version.txt').read_text().strip() != 'R2025a':
        raise ValueError('Real Webots R2025a is required; never skip missing runtime')
    output = args.output.resolve()
    if output.exists():
        raise ValueError('Fresh output required; preserve all prior attempts')
    (ROOT/'.local/local-session').mkdir(parents=True, exist_ok=True)
    with (ROOT/'.local/local-session/active.lock').open('a+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Collector active; preserve checkout')
        if git('status', '--porcelain'):
            raise ValueError('efficiency runtime requires a clean source checkpoint')
        source, files = git('rev-parse', 'HEAD'), inventory()
        claim_exposure(args.split,digest(files),output)
        output.mkdir(parents=True)
        report = {'schema_version': 1, 'kind': 'efficiency_runtime_v1', 'status': 'running',
            'source_commit': source, 'working_tree_dirty': False, 'files': files, 'runtime_sha256': digest(files),
            'protocol_sha256': design, 'shared_v3_runtime_sha256': shared, 'complete_split': not args.case,
            'protocol_version':'efficiency_runtime_v1', 'binding_sha256':sha(BINDING), 'design_lock_sha256':verify_design(),
            'runtime_lock_sha256':verify_lock() if args.split!='development' else None,
            'study': args.study, 'split': args.split, 'cases': [c['id'] for c in cases], 'attempts': [], 'rows': [],
            'locks_file_sha256': {str(p.relative_to(ROOT)): sha256_file(p) for p in sorted((ROOT/'configs/scenarios').glob('*.lock.json'))},
            'environment': {'webots_version': 'R2025a', 'rendering': False, 'python': sys.version,
                'platform': platform.platform(), 'cpu_affinity': sorted(os.sched_getaffinity(0)),
                'started_utc': datetime.now(timezone.utc).isoformat()}}
        (output/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
        env = os.environ.copy()
        env.update({'BLIND_DRONE_SENSOR_STUDY': args.study, 'BLIND_DRONE_SPLIT': args.split, 'PYTHONUNBUFFERED': '1', 'LIBGL_ALWAYS_SOFTWARE': '1',
            'XDG_CONFIG_HOME': str(ROOT/'.local/webots-sensor-pilots/config'), 'XDG_CACHE_HOME': str(ROOT/'.local/webots-sensor-pilots/cache')})
        if args.validation_review:
            env['BLIND_DRONE_VALIDATION_REVIEW']=str(args.validation_review.resolve())
        else:
            env.pop('BLIND_DRONE_VALIDATION_REVIEW',None)
        for key in ('XDG_CONFIG_HOME', 'XDG_CACHE_HOME'):
            Path(env[key]).mkdir(parents=True, exist_ok=True)
        collector_start = time.monotonic()
        try:
            for case, mode, repeat, arm in schedule(cases, spec):
                if time.monotonic()-collector_start > spec['collector_wall_budget_s']:
                    raise ValueError('Registered collector wall budget exceeded; incomplete')
                for attempt in range(2):
                    if inventory() != files or git('rev-parse', 'HEAD') != source or git('status', '--porcelain'):
                        raise ValueError('Source changed while collector active')
                    name = f"{case['id']}-{mode}-r{repeat}-{arm or 'pair'}-a{attempt}"
                    directory = output/name; directory.mkdir()
                    env.update({'BLIND_DRONE_CASE': case['id'], 'BLIND_DRONE_REPEAT': str(repeat), 'BLIND_DRONE_SENSOR_MODE': mode})
                    env.pop('BLIND_DRONE_SENSOR_ARM', None)
                    if arm is not None:
                        env['BLIND_DRONE_SENSOR_ARM'] = arm
                    record = run_process(executable, env, directory, spec['wall_watchdog_s'])
                    record.update(case_id=case['id'], mode=mode, repeat=repeat, arm=arm, attempt=attempt, output=name)
                    report['attempts'].append(record)
                    if record['classification'] == 'valid':
                        audits = audit_attempt(directory, case, spec, record['result'], mode, repeat, arm)
                        record['raw_integrity_passed'] = True
                        report['rows'].extend({'mode': mode, 'episode': row, 'folder': name, 'audit': audit}
                                              for row, audit in zip(record['result']['episodes'], audits))
                    (directory/'attempt.json').write_text(json.dumps(record, indent=2)+'\n')
                    if record['classification'] == 'valid':
                        break
                    if record['classification'] != 'infrastructure' or attempt == 1:
                        raise ValueError('Incomplete efficiency runtime process; '+record['classification']+'; '+name)
                print('EFFICIENCY_PROCESS', mode, case['id'], repeat, arm or 'pair',
                      [(r['arm'], r['outcome']) for r in record['result']['episodes']], flush=True)
                (output/'progress.json').write_text(json.dumps(report, indent=2)+'\n')
            report['summary'] = summarize([row | {'folder': output/row['folder']} for row in report['rows']], cases, spec)
            report['status'] = 'complete'; report['integrity_passed'] = True
            report['study_outcome'] = 'met' if report['summary']['met'] else 'not_met'
        except Exception as error:
            report['status'] = 'incomplete'; report['error'] = str(error)
            print(error, file=sys.stderr, flush=True)
        finally:
            (output/'result.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print('EFFICIENCY_RESULT', report['status'], len(report['rows']), 'episodes', report.get('study_outcome'), flush=True)
    return 0 if report['status'] == 'complete' else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr); raise SystemExit(2)
