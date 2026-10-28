"""Privileged development fixtures and additive inventory. Not a policy import."""
import hashlib
import json
from math import pi
from pathlib import Path
import tomllib

from blind_drone.experiments.protocol_v2 import load_v2_config
from blind_drone.experiments.runtime_v3 import inventory as shared_inventory, outputs as v3_outputs
from blind_drone.world.geometry import path_certificate
from blind_drone.world.minimal_lab import ROOT
from blind_drone.world.scenarios import digest, generate_case

VERSION = ROOT / 'versions/navigation_v4'
INDEX = VERSION / 'development.index.json'
FIXTURE = ROOT / 'artifacts/navigation-v4-fixtures/development.json'
WORLD = ROOT / 'simulation/webots/worlds/observed_v4.wbt'


def load_spec():
    spec = tomllib.loads((VERSION / 'development.toml').read_text())
    if (spec['schema_version'], spec['status'], spec['reference_period_ms'], spec['candidate_period_ms']) != (4, 'development_only', 32, 32):
        raise ValueError('V4 development contract mismatch')
    return spec


def build_cases():
    body = load_v2_config()['vehicle']['body_size_m']
    entries = json.loads((ROOT / 'configs/scenarios/range_cadence_v3.index.json').read_text())['cases']
    cases = []
    for item in entries:
        if item['split'] != 'development':
            continue
        case = generate_case(item['family'], item['seed'], 'development')
        case['certificate'] = path_certificate(case, body)
        if digest(case) != item['case_sha256']:
            raise ValueError('V3 development regression commitment mismatch')
        cases.append(case)
    offsets = ((.025,.125),(.125,.025),(.125,.225),(.225,.125),
               (.000001,.125),(.249999,.125),(.125,.000001),(.125,.249999))
    targets = []
    for x, y in offsets:
        for yaw in (0., pi/4):
            targets.append(('empty_offset', [-5+x,y,1.5], [4.875,.125,1.5], yaw, [], True))
    for y in (-.25, -.125, 0., .125):
        targets.append(('near_wall', [-4.875,y,1.5], [4.875,y,1.5], pi/3,
                        [{'center_m':[0.,-1.5,1.5], 'size_m':[8.,.5,3.]}], True))
    for y in (-.2, -.05, .05, .2):
        targets.append(('narrow_gap', [-5.125,y,1.5], [5.125,y,1.5], -pi/4,
                        [{'center_m':[0.,sign*2.8,1.5], 'size_m':[1.,4.,3.]} for sign in (-1,1)], True))
    for x in (.025, .125, .225, .249999):
        targets.append(('blocked_goal', [-5+x,.125,1.5], [0.,0.,1.5], pi/2,
                        [{'center_m':[0.,0.,1.5], 'size_m':[2.,2.,3.]}], False))
    for index, (family, start, goal, yaw, obstacles, feasible) in enumerate(targets):
        case = {'id': f'development-v4-{family}-{index:02d}', 'family':family, 'seed':4100000+index,
                'split':'development', 'start_m':start, 'goal_m':goal, 'start_yaw_rad':yaw,
                'obstacles':obstacles, 'feasible':feasible}
        case['geometry_sha256'] = digest({k:case[k] for k in ('start_m','goal_m','obstacles')})
        case['certificate'] = path_certificate(case, body)
        cases.append(case)
    if len(cases) != 88 or len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Unexpected development membership')
    return cases


def generated_outputs():
    cases = build_cases()
    old = v3_outputs()
    proto = old[ROOT / 'simulation/webots/protos/BlindDroneV3.proto'].replace('BlindDroneV3', 'BlindDroneV4').replace('"drone_v3"', '"drone_v4"')
    world = old[ROOT / 'simulation/webots/worlds/cadence_v3.wbt'].replace('BlindDroneV3', 'BlindDroneV4').replace('"lab_v3"', '"lab_v4"')
    index = {'schema_version':4, 'kind':'development_only',
             'cases':[{k:c[k] for k in ('id','family','feasible','geometry_sha256')} | {'case_sha256':digest(c)} for c in cases]}
    return {ROOT / 'simulation/webots/protos/BlindDroneV4.proto':proto,
            WORLD:world, INDEX:json.dumps(index, indent=2)+'\n'}, cases


def select_cases(split='development', requested=None):
    if split != 'development':
        raise ValueError('V4 has no validation/test protocol; development only')
    cases = json.loads(FIXTURE.read_text())['cases']
    index = json.loads(INDEX.read_text())['cases']
    if [(c['id'], digest(c)) for c in cases] != [(c['id'], c['case_sha256']) for c in index]:
        raise ValueError('V4 fixture commitment mismatch')
    chosen = [c for c in cases if not requested or c['id'] in requested]
    if not chosen or (requested and set(requested) != {c['id'] for c in chosen}):
        raise ValueError('Unknown development case')
    return chosen, digest({'index':json.loads(INDEX.read_text()), 'spec':load_spec()})


def inventory():
    paths = list(VERSION.rglob('*.py')) + [VERSION / 'development.toml', INDEX]
    paths += [ROOT / p for p in ('tools/run_navigation_v4.py', 'tools/build_navigation_v4.py',
                                'tools/review_navigation_v4.py', 'simulation/webots/protos/BlindDroneV4.proto',
                                'simulation/webots/worlds/observed_v4.wbt')]
    for name in ('drone_v4', 'lab_v4'):
        paths += list((ROOT / 'simulation/webots/controllers' / name).glob('*.py'))
    return {**shared_inventory(), **{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}}
