"""Development orchestration and case fixtures; never imported by navigation."""
import hashlib
import json
from pathlib import Path
import tomllib

from blind_drone.evaluation.cadence import pair_order
from blind_drone.world.minimal_lab import ROOT
from blind_drone.world.scenarios import digest
from blind_drone_v4.protocol import build_cases as v4_cases, generated_outputs as v4_outputs, inventory as v4_inventory

VERSION = ROOT / 'versions/initialization_aa_v1'
INDEX = VERSION / 'development.index.json'
FIXTURE = ROOT / 'artifacts/initialization-aa-fixtures/development.json'
WORLD = ROOT / 'simulation/webots/worlds/initialization_aa_v1.wbt'


def load_spec():
    spec = tomllib.loads((VERSION / 'development.toml').read_text())
    if (spec['schema_version'], spec['status'], spec['policy'], spec['modes'], spec['repetitions']) != (
            1, 'development_only', 'observed_detour_v4_full_history_both_labels', ['warm', 'cold'], 2):
        raise ValueError('A/A design mismatch')
    if any(spec[key] != expected for key, expected in [('reference_period_ms', 32), ('candidate_period_ms', 32),
            ('pose_period_ms', 32), ('control_period_ms', 16), ('warmup_s', 2.), ('max_infrastructure_retries', 1)]):
        raise ValueError('A/A timing/retry mismatch')
    if len(spec['case_ids']) != 12 or len(set(spec['case_ids'])) != 12:
        raise ValueError('A/A requires the twelve registered cases')
    return spec


def execution_arms(case_id, repeat, mode, arm=None):
    if type(repeat) is not int or repeat not in (0, 1):
        raise ValueError('Unexpected repeat')
    if mode == 'warm' and arm is None:
        return list(pair_order(case_id, repeat))
    if mode == 'cold' and arm in ('reference', 'candidate'):
        return [arm]
    raise ValueError('Invalid A/A mode/arm')


def schedule(cases, modes=('warm', 'cold')):
    if not modes or len(set(modes)) != len(modes) or any(m not in ('warm', 'cold') for m in modes):
        raise ValueError('Invalid A/A modes')
    for case in cases:
        for mode in modes:
            for repeat in (0, 1):
                for arm in ([None] if mode == 'warm' else pair_order(case['id'], repeat)):
                    yield case, mode, repeat, arm


def generated_outputs():
    selected = load_spec()['case_ids']
    by_id = {case['id']: case for case in v4_cases()}
    cases = [by_id[key] for key in selected]
    old, _ = v4_outputs()
    proto = old[ROOT / 'simulation/webots/protos/BlindDroneV4.proto'].replace('BlindDroneV4', 'BlindDroneAA').replace('"drone_v4"', '"drone_aa"')
    world = old[ROOT / 'simulation/webots/worlds/observed_v4.wbt'].replace('BlindDroneV4', 'BlindDroneAA').replace('"lab_v4"', '"lab_aa"')
    index = {'schema_version': 1, 'scope': 'exposed_development_only',
             'cases': [{'id': c['id'], 'case_sha256': digest(c)} for c in cases]}
    return {ROOT / 'simulation/webots/protos/BlindDroneAA.proto': proto,
            WORLD: world, INDEX: json.dumps(index, indent=2) + '\n'}, cases


def select_cases(split='development', requested=None):
    if split != 'development':
        raise ValueError('A/A is development only; no validation/test')
    cases = json.loads(FIXTURE.read_text())['cases']
    index = json.loads(INDEX.read_text())
    if [(c['id'], digest(c)) for c in cases] != [(c['id'], c['case_sha256']) for c in index['cases']]:
        raise ValueError('A/A development fixture mismatch')
    chosen = [c for c in cases if not requested or c['id'] in requested]
    if not chosen or (requested and set(requested) != {c['id'] for c in chosen}):
        raise ValueError('Unknown A/A development case')
    return chosen, digest({'index': index, 'spec': load_spec()})


def inventory():
    paths = list(VERSION.rglob('*.py')) + [VERSION / 'development.toml', INDEX, WORLD,
        ROOT / 'simulation/webots/protos/BlindDroneAA.proto']
    paths += [ROOT / ('tools/' + name + '.py') for name in ('build_initialization_aa', 'run_initialization_aa', 'review_initialization_aa')]
    for name in ('drone_aa', 'lab_aa'):
        paths += list((ROOT / 'simulation/webots/controllers' / name).glob('*.py'))
    return {**v4_inventory(), **{str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}}
