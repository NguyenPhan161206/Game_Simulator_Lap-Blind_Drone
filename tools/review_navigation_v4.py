"""Independent raw v4 development review; path relocation is in memory only."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'versions/navigation_v4'),str(ROOT/'tools')]
from blind_drone.experiments.runtime_v3 import verify_runtime
from blind_drone.world.scenarios import digest
from blind_drone_v4.audit import audit_v4_pair,summarize
from blind_drone_v4.protocol import inventory,load_spec,select_cases
from review_research_v3 import checked_path,relocate_and_verify,sha256_file


def review(directory,source):
    directory=Path(directory).resolve()
    raw_path=checked_path(directory,'result.json');raw=json.loads(raw_path.read_text())
    cases,development=select_cases()
    shared=verify_runtime();files=inventory()
    expected={'schema_version':4,'kind':'paired_navigation_development','status':'complete','split':'development',
              'working_tree_dirty':False,'integrity_passed':True,'complete_split':True,'source_commit':source,
              'files':files,'runtime_sha256':digest(files),'shared_v3_runtime_sha256':shared,
              'development_sha256':development,'cases':[c['id'] for c in cases]}
    if len(source)!=40 or any(c not in '0123456789abcdef' for c in source):
        raise ValueError('Expected full source SHA')
    for key,value in expected.items():
        if type(raw.get(key)) is not type(value) or raw[key]!=value:
            raise ValueError('V4 identity/completeness mismatch: '+key)
    for path,sha in files.items():
        import hashlib
        content=subprocess.check_output(['bash',str(ROOT/'tools/git.sh'),'show',source+':'+path],cwd=ROOT)
        if hashlib.sha256(content).hexdigest()!=sha:raise ValueError('Source differs from inventory: '+path)
    locks={str(p.relative_to(ROOT)):sha256_file(p) for p in sorted((ROOT/'configs/scenarios').glob('*.lock.json'))}
    if raw['locks_file_sha256']!=locks:raise ValueError('Legacy lock bytes changed')
    relocated=relocate_and_verify(raw,directory,cases)
    index={c['id']:c for c in cases};audits=[];episodes=[];groups={}
    for attempt in relocated['attempts']:
        key=attempt['case_id'],attempt['repeat'];groups.setdefault(key,[]).append(attempt)
        if attempt['classification']=='valid':
            audits.append(audit_v4_pair(Path(attempt['output']),index[key[0]],load_spec(),attempt['result']))
            episodes.extend(attempt['result']['episodes'])
        elif attempt['classification']!='infrastructure':raise ValueError('Unresolved attempt')
    for group in groups.values():
        if len(group)>2 or [a['attempt'] for a in group]!=list(range(len(group))) or group[-1]['classification']!='valid':
            raise ValueError('Invalid retry history')
    summary=summarize(episodes,cases,audits)
    if episodes!=raw['episodes'] or audits!=raw['pair_audits'] or summary!=raw['summary']:
        raise ValueError('Independent v4 raw review differs from collector')
    return {'schema_version':4,'kind':'offline_v4_development_review','source_commit':source,
            'complete':True,'raw_audit_passed':True,'raw_result_sha256':sha256_file(raw_path),
            'runtime_sha256':raw['runtime_sha256'],'shared_v3_runtime_sha256':shared,
            'development_sha256':development,'locks_file_sha256':locks,
            'cases':len(cases),'episodes':len(episodes),'attempts':len(relocated['attempts']),
            'summary':summary,'test_qualified':False,'heldout_protocol_exists':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('--expected-source',required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists() or args.output.resolve()==(args.directory/'result.json').resolve():
        parser.error('Use fresh review output; never overwrite evidence')
    try:result=review(args.directory,args.expected_source)
    except (ValueError,OSError,KeyError,TypeError) as error:
        print('V4_REVIEW_FAILED:',error,file=sys.stderr);return 2
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print('V4_REVIEW',json.dumps(result['summary'],separators=(',',':')))
    return 0


if __name__=='__main__':raise SystemExit(main())
