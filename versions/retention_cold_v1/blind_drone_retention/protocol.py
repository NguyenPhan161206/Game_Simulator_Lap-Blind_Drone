"""Registered exposed development fixtures; never imported by the navigator."""
import hashlib
import json
import tomllib

from blind_drone.evaluation.cadence import pair_order
from blind_drone.world.minimal_lab import ROOT
from blind_drone.world.scenarios import digest
from blind_drone_v4.protocol import build_cases, generated_outputs as v4_outputs, inventory as v4_inventory

VERSION = ROOT/'versions/retention_cold_v1'
INDEX = VERSION/'development.index.json'
FIXTURE = ROOT/'artifacts/retention-cold-fixtures/development.json'
WORLD = ROOT/'simulation/webots/worlds/retention_cold_v1.wbt'


def load_spec():
    spec = tomllib.loads((VERSION/'development.toml').read_text())
    if (spec['schema_version'], spec['status'], spec['policy'], spec['modes'], spec['repetitions']) != (
            1, 'development_only', 'v4_free_history_2s', ['cold'], 2):
        raise ValueError('Retention design mismatch')
    expected = {'reference_period_ms': 32, 'candidate_period_ms': 32, 'pose_period_ms': 32,
                'control_period_ms': 16, 'warmup_s': 2., 'max_infrastructure_retries': 1}
    if any(spec[k] != value for k, value in expected.items()) or spec['retention'] != {'free_ttl_s': 2., 'max_entries': 16000}:
        raise ValueError('Retention timing/budget mismatch')
    return spec


def execution_arms(case_id, repeat, mode, arm=None):
    if type(repeat) is not int or repeat not in (0, 1) or mode != 'cold' or arm not in ('reference', 'candidate'):
        raise ValueError('Cold isolated arm/repeat required')
    return [arm]


def schedule(cases):
    for case in cases:
        for repeat in (0, 1):
            for arm in pair_order(case['id'], repeat):
                yield case, 'cold', repeat, arm


def generated_outputs():
    load_spec()
    cases = build_cases()
    old, _ = v4_outputs()
    proto = old[ROOT/'simulation/webots/protos/BlindDroneV4.proto'].replace('BlindDroneV4', 'BlindDroneRetention').replace('"drone_v4"', '"drone_retention"')
    world = old[ROOT/'simulation/webots/worlds/observed_v4.wbt'].replace('BlindDroneV4', 'BlindDroneRetention').replace('"lab_v4"', '"lab_retention"')
    index = {'schema_version': 1, 'scope': 'exposed_development_only',
             'cases': [{'id': c['id'], 'case_sha256': digest(c)} for c in cases]}
    return {ROOT/'simulation/webots/protos/BlindDroneRetention.proto': proto,
            WORLD: world, INDEX: json.dumps(index, indent=2)+'\n'}, cases


def select_cases(split='development', requested=None):
    if split != 'development':
        raise ValueError('Retention is development only; validation/test remain closed')
    cases = json.loads(FIXTURE.read_text())['cases']
    index = json.loads(INDEX.read_text())
    if [(c['id'], digest(c)) for c in cases] != [(c['id'], c['case_sha256']) for c in index['cases']]:
        raise ValueError('Retention fixture commitment mismatch')
    chosen = [c for c in cases if not requested or c['id'] in requested]
    if not chosen or (requested and set(requested) != {c['id'] for c in chosen}):
        raise ValueError('Unknown retention development case')
    return chosen, digest({'index': index, 'spec': load_spec()})


def inventory():
    paths = list(VERSION.rglob('*.py')) + [VERSION/'development.toml', INDEX, WORLD,
            ROOT/'simulation/webots/protos/BlindDroneRetention.proto']
    paths += [ROOT/('tools/'+name+'.py') for name in ('build_retention_cold', 'run_retention_cold', 'review_retention_cold')]
    for name in ('drone_retention', 'lab_retention'):
        paths += list((ROOT/'simulation/webots/controllers'/name).glob('*.py'))
    paths += list((ROOT/'versions/initialization_aa_v1').rglob('*.py'))
    return {**v4_inventory(), **{str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}}
