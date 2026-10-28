"""Sequential real-Webots v3 pairs; default development, held-out fail closed."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from blind_drone.evaluation.cadence import aggregate, classify_attempt, pair_order
from blind_drone.evaluation.cadence_audit import audit_pair, audit_study
from blind_drone.experiments.protocol_v3 import load_spec
from blind_drone.experiments.runtime_v3 import LOCK, WORLD, exposure, git, inventory, outputs, select_cases, verify_runtime
from blind_drone.world.scenarios import digest
from run_webots import find_webots


def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def run_pair(executable,env,output,timeout):
    home=Path(executable).parent
    binary=home/'bin/webots-bin'
    if binary.exists():
        executable=str(binary);env['WEBOTS_HOME']=str(home)
        env['LD_LIBRARY_PATH']=str(home/'lib/webots')+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
        env.setdefault('QT_QPA_PLATFORM','xcb')
        env['WEBOTS_TMPDIR']='/tmp';env['TMPDIR']='/tmp'
    env['BLIND_DRONE_OUTPUT']=str(output)
    command=[executable,'--batch','--stdout','--stderr','--no-rendering','--mode=fast',str(WORLD)]
    started=time.monotonic();timed_out=False;peak_rss=0
    with (output/'console.log').open('w') as log:
        process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        while process.poll() is None:
            try:
                rss=int(Path(f'/proc/{process.pid}/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')/1024**2
                peak_rss=max(peak_rss,rss)
            except (OSError,IndexError):pass
            if time.monotonic()-started>timeout:
                timed_out=True;os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
                break
            try:process.wait(timeout=.1)
            except subprocess.TimeoutExpired:pass
    path=output/'result.json'
    try:result=json.loads(path.read_text()) if path.exists() else None
    except (OSError,ValueError):result=None
    console=(output/'console.log').read_text(errors='replace')
    classification=classify_attempt(result,console,timed_out)
    if classification=='valid' and process.returncode!=0:classification='unresolved'
    return {'classification':classification,'returncode':process.returncode,'watchdog':timed_out,
            'wall_s':time.monotonic()-started,'webots_peak_rss_mib':peak_rss,'command':command,
            'result':result,'files_sha256':{p.name:file_hash(p) for p in output.iterdir() if p.is_file()}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--split',choices=('development','validation','test'),default='development')
    p.add_argument('--case',action='append',help='Development subset only; repeat to select several cases')
    p.add_argument('--output',type=Path);p.add_argument('--webots')
    p.add_argument('--validation-result',type=Path)
    args=p.parse_args()
    if args.case and args.split!='development':raise ValueError('Held-out requires complete split')
    cases,design=select_cases(args.split,args.case)
    spec=load_spec()
    runtime=verify_runtime() if LOCK.exists() else None
    if args.split=='test':
        if not args.validation_result:raise ValueError('Test requires reviewed complete validation result')
        validation=json.loads(args.validation_result.read_text())
        if not (validation.get('split')=='validation' and validation.get('status')=='complete'
                and validation.get('complete_split') and validation.get('gate',{}).get('met')
                and validation.get('integrity_passed') and validation.get('runtime_sha256')==runtime
                and validation.get('design_sha256')==design and validation.get('files')==inventory()):
            raise ValueError('Validation did not qualify this exact frozen runtime')
        validation_cases,_=select_cases('validation')
        audit_study(validation,validation_cases,spec)
    for path,text in outputs().items():
        if not path.exists() or path.read_text()!=text:raise ValueError('Generate/check v3 world before running')
    executable=find_webots(args.webots)
    if not executable:raise ValueError('Real Webots R2025a executable is missing')
    version_file=Path(executable).parent/'resources/version.txt'
    if not version_file.exists() or version_file.read_text().strip()!='R2025a':
        raise ValueError('Specify the pinned Webots R2025a wrapper path; version must be verified')
    source=git('rev-parse','HEAD')
    # Exposure ledger is expected to change during a run. No runtime source drift
    # is allowed between pairs; actual hashes are captured even in debug builds.
    dirty=bool(git('status','--porcelain'))
    if args.split!='development' and dirty:raise ValueError('Held-out requires clean checkout before exposure')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output=(args.output or ROOT/f'artifacts/research-v3-{args.split}-{stamp}').resolve()
    if output.exists():raise ValueError('Use fresh output; never overwrite attempts')
    output.mkdir(parents=True)
    collector_lock=ROOT/'.local/local-session/active.lock'
    collector_lock.parent.mkdir(parents=True,exist_ok=True)
    lock=collector_lock.open('a+')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise ValueError('A local collector is active; preserve its checkout')
    files=inventory()
    home=Path(executable).parent
    binary=home/'bin/webots-bin' if (home/'bin/webots-bin').exists() else Path(executable)
    report={'schema_version':3,'split':args.split,'status':'running','source_commit':source,
            'working_tree_dirty':dirty,'files':files,'design_sha256':design,'runtime_sha256':runtime,
            'complete_split':not args.case,'cases':[c['id'] for c in cases],'episodes':[],'attempts':[],
            'environment':{'hostname':platform.node(),'platform':platform.platform(),'python':sys.version,
                           'cpu':platform.processor(),'cpu_affinity':sorted(os.sched_getaffinity(0)),
                           'load_average':list(os.getloadavg()),'binary_sha256':file_hash(binary),
                           'webots_version':'R2025a','rendering':False,
                           'environment_sha256':digest({k:os.environ.get(k) for k in ('DISPLAY','QT_QPA_PLATFORM','LD_LIBRARY_PATH','LIBGL_ALWAYS_SOFTWARE','OMP_NUM_THREADS')})}}
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    exposure(args.split,'intent',source,str(output)+'; automated selected geometry only; no held-out outcomes opened',False,False)
    print('Output:',output,flush=True)
    env=os.environ.copy()
    env.update({'BLIND_DRONE_SPLIT':args.split,'PYTHONUNBUFFERED':'1','LIBGL_ALWAYS_SOFTWARE':'1',
                'XDG_CONFIG_HOME':str(ROOT/'.local/webots-v3/config'),'XDG_CACHE_HOME':str(ROOT/'.local/webots-v3/cache')})
    for key in ('XDG_CONFIG_HOME','XDG_CACHE_HOME'):Path(env[key]).mkdir(parents=True,exist_ok=True)
    try:
        for case in cases:
            for repeat in (0,1):
                for attempt in range(2):
                    if inventory()!=files or git('rev-parse','HEAD')!=source:
                        raise ValueError('Source changed during collector; preserve current evidence')
                    directory=output/f"{case['id']}-r{repeat}-a{attempt}"
                    directory.mkdir()
                    env['BLIND_DRONE_CASE']=case['id'];env['BLIND_DRONE_REPEAT']=str(repeat)
                    record=run_pair(executable,env,directory,spec['wall_watchdog_s'])
                    record.update({'case_id':case['id'],'repeat':repeat,'attempt':attempt,'output':str(directory),
                                   'order':pair_order(case['id'],repeat)})
                    report['attempts'].append(record)
                    (directory/'attempt.json').write_text(json.dumps(record,indent=2)+'\n')
                    if record['classification']=='valid':
                        audit_pair(directory,case,spec,record['result'])
                        record['raw_integrity_passed']=True
                        report['episodes'].extend(record['result']['episodes']);break
                    if record['classification']!='infrastructure' or attempt==1:
                        raise ValueError('Pair incomplete: '+record['classification']+'; '+str(directory))
                print(case['id'],'repeat',repeat,[(e['arm'],e['outcome']) for e in record['result']['episodes']],flush=True)
                (output/'progress.json').write_text(json.dumps(report,indent=2)+'\n')
        report['gate']=aggregate(report['episodes'],cases,spec)
        # Development success rate is an outcome, not an integrity requirement.
        report['integrity_passed']=all(e['acquisition']['schedule_complete'] and e['acquisition']['all']['invalid_values']==0
                                      for e in report['episodes'])
        report['status']='complete'
    except Exception as error:
        report['status']='incomplete';report['error']=str(error)
        print(error,file=sys.stderr,flush=True)
    finally:
        report['environment']['load_average_end']=list(os.getloadavg())
        report['actual_files_bytes']={str(p.relative_to(output)):p.stat().st_size for p in output.rglob('*') if p.is_file()}
        (output/'result.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        exposure(args.split,'result',source,str(output)+'; status='+report['status']+'; all failures and attempts retained',True,True)
        fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
    print('V3',report['status'],'episodes',len(report['episodes']),'gate',report.get('gate',{}).get('met'),flush=True)
    return 0 if report['status']=='complete' and report['integrity_passed'] else 1


if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError) as error:print(error,file=sys.stderr);raise SystemExit(2)
