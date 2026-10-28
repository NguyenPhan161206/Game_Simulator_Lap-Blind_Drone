"""V3 world, fixture commitments, provenance and additive runtime source lock."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from blind_drone.experiments.protocol_v2 import load_v2_config
from blind_drone.experiments.protocol_v3 import INDEX, LEDGER, LOCK as DESIGN_LOCK, verify_design, load_spec
from blind_drone.world.minimal_lab import ROOT, controller_config, proto_text, world_text
from blind_drone.world.scenarios import digest

LOCK = ROOT/'configs/scenarios/protocol_v3.runtime.lock.json'
WORLD = ROOT/'simulation/webots/worlds/cadence_v3.wbt'


def git(*args):
    return subprocess.check_output(['bash',str(ROOT/'tools/git.sh'),*args],cwd=ROOT,text=True).strip()


def outputs():
    config=load_v2_config()
    public=controller_config(config)
    public['navigation_v2']=config['navigation_v2']
    old=json.dumps(json.dumps(controller_config(config),separators=(',',':')))
    new=json.dumps(json.dumps(public,separators=(',',':')))
    proto=proto_text(config).replace('PROTO BlindDrone [','PROTO BlindDroneV3 [').replace('controller "drone_controller"','controller "drone_v3"')
    world=world_text(config).replace('protos/BlindDrone.proto','protos/BlindDroneV3.proto').replace('DEF DRONE BlindDrone {','DEF DRONE BlindDroneV3 {').replace('controller "lab_supervisor"','controller "lab_v3"').replace(old,new)
    return {ROOT/'simulation/webots/protos/BlindDroneV3.proto':proto,WORLD:world}


def inventory():
    # Include the complete Python core, not just direct adapter imports. Entrypoints,
    # controller runtime settings, world/proto and all numerical configs are pinned.
    paths=list((ROOT/'src').rglob('*.py'))
    paths += [ROOT/p for p in ('tools/run_research_v3.py','tools/build_runtime_v3.py','tools/run_webots.py','tools/git.sh',
        'configs/lab_v1.toml','configs/navigation_v1.toml','configs/navigation_v2.toml',
        'configs/experiments/range_cadence_v3.toml','configs/scenarios/range_cadence_v3.index.json')]
    paths += list(outputs())
    for controller in ('drone_v3','lab_v3'):
        paths += list((ROOT/'simulation/webots/controllers'/controller).glob('*'))
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths) if p.is_file()}


def verify_runtime(path=LOCK):
    design=verify_design()
    if not Path(path).exists():raise ValueError('V3 runtime lock missing; held-out evaluation is disabled')
    value=json.loads(Path(path).read_text())
    if value.get('schema_version')!=3 or value.get('design_sha256')!=design or value.get('files')!=inventory():
        raise ValueError('Runtime lock mismatch; never regenerate after held-out exposure')
    # source_commit names the reviewed implementation, not this additive lock commit.
    if len(value.get('source_commit',''))!=40 or not value.get('development_evidence_sha256'):
        raise ValueError('Runtime lock lacks source/development provenance')
    if subprocess.call(['bash',str(ROOT/'tools/git.sh'),'merge-base','--is-ancestor',value['source_commit'],'HEAD'],cwd=ROOT):
        raise ValueError('Locked implementation is not an ancestor of this checkout')
    for name,sha in value['files'].items():
        committed=subprocess.check_output(['bash',str(ROOT/'tools/git.sh'),'show',value['source_commit']+':'+name],cwd=ROOT)
        if hashlib.sha256(committed).hexdigest()!=sha:raise ValueError('Lock does not match implementation commit: '+name)
    return digest(value)


def select_cases(split, requested=None):
    if split not in ('development','validation','test'):raise ValueError('Train is reserved; not executable')
    design=verify_design()
    if split!='development':verify_runtime()
    fixture=ROOT/f'artifacts/research-v3-fixtures/{split}.json'
    data=json.loads(fixture.read_text())
    cases=data['cases'] if isinstance(data,dict) else data
    index={c['id']:c for c in json.loads(INDEX.read_text())['cases'] if c['split']==split}
    if {c['id'] for c in cases}!=set(index):raise ValueError('Fixture split membership mismatch')
    for c in cases:
        if digest(c)!=index[c['id']]['case_sha256']:raise ValueError('Fixture commitment mismatch')
    chosen=[c for c in cases if not requested or c['id'] in requested]
    if not chosen or (requested and {c['id'] for c in chosen}!=set(requested)):raise ValueError('Unknown requested case')
    return chosen,design


def exposure(split, purpose, source, note, executed, viewed):
    value=json.loads(LEDGER.read_text())
    stamp=datetime.now(timezone.utc).isoformat()
    value['events'].append({'event_id':'v3-'+purpose+'-'+stamp,'date':stamp,'actor':'Codex/runtime_v3',
        'source':source,'splits':[split],'purpose':purpose,'access':'automated geometry and runtime; public observation to policy only',
        'outcomes_viewed':viewed,'navigation_executed':executed,'note':note})
    LEDGER.write_text(json.dumps(value,indent=2)+'\n')
