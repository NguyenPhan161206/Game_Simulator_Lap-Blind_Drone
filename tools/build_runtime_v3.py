"""Generate/check v3 world, or add the runtime lock after reviewed development."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from blind_drone.experiments.runtime_v3 import LOCK, git, inventory, outputs, verify_runtime
from blind_drone.experiments.runtime_v3 import select_cases
from blind_drone.experiments.protocol_v3 import verify_design, load_spec
from blind_drone.evaluation.cadence import aggregate
from blind_drone.evaluation.cadence_audit import audit_study
from blind_drone.world.scenarios import digest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true')
    p.add_argument('--freeze',type=Path,metavar='DEVELOPMENT_RESULT')
    args=p.parse_args()
    design=verify_design()
    for path,text in outputs().items():
        if args.check or LOCK.exists():
            if not path.exists() or path.read_text()!=text:raise ValueError('Stale v3 generated file: '+str(path))
        else:path.write_text(text)
    if args.freeze:
        if LOCK.exists():raise ValueError('Refusing to overwrite runtime lock')
        result=json.loads(args.freeze.read_text())
        if result.get('split')!='development' or result.get('status')!='complete' or not result.get('complete_split'):
            raise ValueError('Runtime freeze requires a complete real development split')
        if result.get('design_sha256')!=design or result.get('files')!=inventory():
            raise ValueError('Development source does not match current implementation')
        if not result.get('integrity_passed') or result.get('working_tree_dirty'):
            raise ValueError('Development must have verified acquisition/accounting and clean source')
        cases,_=select_cases('development')
        audit_study(result,cases,load_spec())
        source=result['source_commit']
        current=inventory()
        for name,sha in current.items():
            import hashlib,subprocess
            data=subprocess.check_output(['bash',str(ROOT/'tools/git.sh'),'show',source+':'+name],cwd=ROOT)
            if hashlib.sha256(data).hexdigest()!=sha:raise ValueError('Source commit mismatch: '+name)
        value={'schema_version':3,'lock_kind':'runtime_source','design_sha256':design,
               'source_commit':source,'development_evidence_sha256':digest(result),'files':current}
        LOCK.write_text(json.dumps(value,indent=2)+'\n')
    if LOCK.exists():print('Runtime v3 verified:',verify_runtime())
    else:print('V3 development only; held-out evaluation requires a separate runtime lock')
    return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError) as error:print(error,file=sys.stderr);raise SystemExit(2)
