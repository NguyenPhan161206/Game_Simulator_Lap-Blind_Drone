"""Sequential DATA-03 occupied-only paired development on real Webots."""
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

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'versions/navigation_v4'),str(ROOT/'versions/data_occupied_v1'),str(ROOT/'tools')]
from blind_drone.evaluation.cadence import classify_attempt, pair_order
from blind_drone.experiments.runtime_v3 import git, verify_runtime
from blind_drone.world.scenarios import digest
from blind_drone_data03.audit import audit_data03_pair, summarize
from blind_drone_data03.protocol import WORLD, generated_outputs, inventory, load_spec, select_cases
from review_research_v3 import sha256_file
from run_webots import find_webots


def run_pair(executable,env,output,timeout):
    home=Path(executable).parent;binary=home/'bin/webots-bin'
    if binary.exists():
        executable=str(binary)
        env['WEBOTS_HOME']=str(home)
        env['LD_LIBRARY_PATH']=str(home/'lib/webots')+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
        env.setdefault('QT_QPA_PLATFORM','xcb')
        env['WEBOTS_TMPDIR']='/tmp';env['TMPDIR']='/tmp'
    env['BLIND_DRONE_OUTPUT']=str(output)
    command=[executable,'--batch','--stdout','--stderr','--no-rendering','--mode=fast',str(WORLD)]
    started=time.monotonic();timed_out=False
    with (output/'console.log').open('w') as log:
        process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True;os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
    result_path=output/'result.json'
    try:result=json.loads(result_path.read_text()) if result_path.exists() else None
    except (OSError,ValueError):result=None
    kind=classify_attempt(result,(output/'console.log').read_text(errors='replace'),timed_out)
    if kind=='valid' and process.returncode!=0:kind='unresolved'
    return {'classification':kind,'returncode':process.returncode,'watchdog':timed_out,
            'wall_s':time.monotonic()-started,'command':command,'result':result,
            'files_sha256':{p.name:sha256_file(p) for p in output.iterdir() if p.is_file()}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split',choices=('development',),default='development')
    parser.add_argument('--case',action='append')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--webots')
    args=parser.parse_args()
    shared=verify_runtime()
    cases,development=select_cases(args.split,args.case)
    spec=load_spec()
    outputs,_=generated_outputs()
    if any(not p.exists() or p.read_text()!=content for p,content in outputs.items()):
        raise ValueError('Build/check DATA-03 assets before execution')
    executable=find_webots(args.webots)
    if not executable or (Path(executable).parent/'resources/version.txt').read_text().strip()!='R2025a':
        raise ValueError('Real Webots R2025a is required; missing runtime must not skip')
    output=args.output.resolve()
    if output.exists():raise ValueError('Use fresh output; never overwrite prior attempts')
    lock_path=ROOT/'.local/local-session/active.lock';lock_path.parent.mkdir(parents=True,exist_ok=True)
    with lock_path.open('a+') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('Local collector is active; preserve checkout')
        files=inventory();source=git('rev-parse','HEAD');dirty=bool(git('status','--porcelain'))
        output.mkdir(parents=True)
        report={'schema_version':1,'kind':'paired_data03_development','status':'running','split':'development',
                'source_commit':source,'working_tree_dirty':dirty,'files':files,'runtime_sha256':digest(files),
                'shared_v3_runtime_sha256':shared,'development_sha256':development,'complete_split':not args.case,
                'cases':[c['id'] for c in cases],'episodes':[],'attempts':[],'pair_audits':[],
                'locks_file_sha256':{str(p.relative_to(ROOT)):sha256_file(p) for p in sorted((ROOT/'configs/scenarios').glob('*.lock.json'))},
                'environment':{'platform':platform.platform(),'python':sys.version,'cpu_affinity':sorted(os.sched_getaffinity(0)),
                               'webots_version':'R2025a','rendering':False,'started_utc':datetime.now(timezone.utc).isoformat()}}
        (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
        env=os.environ.copy()
        env.update({'BLIND_DRONE_SPLIT':'development','PYTHONUNBUFFERED':'1','LIBGL_ALWAYS_SOFTWARE':'1',
                    'XDG_CONFIG_HOME':str(ROOT/'.local/webots-data03/config'),'XDG_CACHE_HOME':str(ROOT/'.local/webots-data03/cache')})
        for key in ('XDG_CONFIG_HOME','XDG_CACHE_HOME'):Path(env[key]).mkdir(parents=True,exist_ok=True)
        try:
            for case in cases:
                for repeat in (0,1):
                    for attempt in range(2):
                        if inventory()!=files or git('rev-parse','HEAD')!=source:
                            raise ValueError('Runtime/source changed during collector')
                        directory=output/f"{case['id']}-r{repeat}-a{attempt}";directory.mkdir()
                        env['BLIND_DRONE_CASE']=case['id'];env['BLIND_DRONE_REPEAT']=str(repeat)
                        record=run_pair(executable,env,directory,spec['wall_watchdog_s'])
                        record.update(case_id=case['id'],repeat=repeat,attempt=attempt,output=str(directory),order=pair_order(case['id'],repeat))
                        report['attempts'].append(record)
                        if record['classification']=='valid':
                            audits=audit_data03_pair(directory,case,spec,record['result'])
                            record['raw_integrity_passed']=True
                            report['pair_audits'].append(audits)
                            report['episodes'].extend(record['result']['episodes'])
                        (directory/'attempt.json').write_text(json.dumps(record,indent=2)+'\n')
                        if record['classification']=='valid':break
                        if record['classification']!='infrastructure' or attempt==1:
                            raise ValueError('Incomplete pair: '+record['classification']+'; '+str(directory))
                    print('DATA03_PAIR',case['id'],repeat,[(e['arm'],e['outcome']) for e in record['result']['episodes']],flush=True)
                    (output/'progress.json').write_text(json.dumps(report,indent=2)+'\n')
            report['summary']=summarize(report['episodes'],cases,report['pair_audits'])
            report['integrity_passed']=True;report['status']='complete'
        except Exception as error:
            report['status']='incomplete';report['error']=str(error)
            print(error,file=sys.stderr,flush=True)
        finally:
            (output/'result.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
            fcntl.flock(lock,fcntl.LOCK_UN)
    print('DATA03_DEVELOPMENT',report['status'],len(report['episodes']),'episodes',flush=True)
    return 0 if report['status']=='complete' and report['integrity_passed'] else 1


if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError) as error:print(error,file=sys.stderr);raise SystemExit(2)
