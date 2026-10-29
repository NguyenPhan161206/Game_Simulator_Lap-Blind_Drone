"""DATA-03 development spec and additive, isolated Webots fixture."""
import hashlib
import json
from pathlib import Path
import tomllib

from blind_drone.world.minimal_lab import ROOT
from blind_drone_v4.protocol import build_cases as v4_build_cases, inventory as v4_inventory, select_cases as v4_select

VERSION = ROOT / 'versions/data_occupied_v1'
SPEC = VERSION / 'development.toml'
FIXTURE = ROOT / 'artifacts/data03-fixtures/development.json'
INDEX = VERSION / 'development.index.json'
WORLD = ROOT / 'simulation/webots/worlds/occupied_only_data03.wbt'
PROTO = ROOT / 'simulation/webots/protos/BlindDroneData03.proto'


def load_spec():
    spec = tomllib.loads((VERSION / 'development.toml').read_text())
    if (spec['schema_version'], spec['status'], spec['reference_period_ms'], spec['candidate_period_ms']) != (1, 'development_only', 32, 32):
        raise ValueError('DATA-03 is development-only with matched 32 ms acquisition')
    return spec


def generated_outputs():
    cases = v4_build_cases()
    v4_world = (ROOT / 'simulation/webots/worlds/observed_v4.wbt').read_text()
    v4_proto = (ROOT / 'simulation/webots/protos/BlindDroneV4.proto').read_text()
    world = v4_world.replace('../protos/BlindDroneV4.proto', '../protos/BlindDroneData03.proto').replace('BlindDroneV4', 'BlindDroneData03').replace('"lab_v4"', '"lab_data03"')
    proto = v4_proto.replace('BlindDroneV4', 'BlindDroneData03').replace('"drone_v4"', '"drone_data03"')
    index = {'schema_version': 1, 'kind': 'development_only', 'parent_case_index': 'versions/navigation_v4/development.index.json',
             'cases': [{'id': c['id'], 'sha256': __import__('hashlib').sha256(json.dumps(c, sort_keys=True, separators=(',', ':')).encode()).hexdigest()} for c in cases]}
    return {WORLD: world, PROTO: proto, INDEX: json.dumps(index, indent=2) + '\n'}, cases


def select_cases(split='development', requested=None):
    if split != 'development':
        raise ValueError('DATA-03 has no validation/test protocol')
    return v4_select(split, requested)


def inventory():
    # Pin every v4 dependency as well as DATA-03-specific code/assets.
    files = dict(v4_inventory())
    paths = list(VERSION.rglob('*.py')) + [VERSION / 'development.toml', INDEX]
    paths += [WORLD, PROTO, ROOT / 'tools/build_data03.py', ROOT / 'tools/run_data03.py',
              ROOT / 'tools/review_data03.py']
    for name in ('drone_data03', 'lab_data03'):
        paths += list((ROOT / 'simulation/webots/controllers' / name).glob('*.py'))
    for path in sorted(set(paths)):
        files[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files
