"""Two separately registered sensor studies on the same exposed pilot cases."""
import hashlib
import json
import tomllib

from blind_drone.world.minimal_lab import ROOT
from blind_drone.world.scenarios import digest
from blind_drone_aa.protocol import generated_outputs as aa_outputs
from blind_drone_retention.protocol import inventory as retention_inventory
from blind_drone_v4.protocol import generated_outputs as v4_outputs

VERSION = ROOT/'versions/sensor_pilots_v1'
INDEX = VERSION/'development.index.json'
FIXTURE = ROOT/'artifacts/sensor-pilots-fixtures/development.json'
WORLD = ROOT/'simulation/webots/worlds/sensor_pilots_v1.wbt'


def load_spec(study):
    if study not in ('adaptive', 'sparse'):
        raise ValueError('Unknown sensor study')
    spec = tomllib.loads((VERSION/(study+'.toml')).read_text())
    arms = ['reference', 'candidate'] if study == 'adaptive' else ['reference', 'dropout', 'sparse']
    if (spec['study'], spec['arms'], spec['status'], spec['repetitions'], spec['modes']) != (
            study, arms, 'development_only', 2, ['cold']):
        raise ValueError('Sensor study design mismatch')
    if any(spec[arm+'_period_ms'] != 32 for arm in arms):
        raise ValueError('Sensor studies start at 32 ms')
    return spec


def profile_for(study, arm):
    spec = load_spec(study)
    if arm not in spec['arms']:
        raise ValueError('Arm is outside this registered study')
    return 'adaptive' if study == 'adaptive' and arm == 'candidate' else 'full' if arm == 'reference' else arm


def execution_arms(case_id, repeat, mode, arm=None):
    if type(repeat) is not int or repeat not in (0, 1) or mode != 'cold' or arm not in ('reference', 'candidate', 'dropout', 'sparse'):
        raise ValueError('Cold isolated sensor arm/repeat required')
    return [arm]


def schedule(cases, spec):
    arms = spec['arms']
    for case in cases:
        offset = int(hashlib.sha256(case['id'].encode()).hexdigest(), 16) % len(arms)
        order = arms[offset:]+arms[:offset]
        for repeat in (0, 1):
            for arm in (order if repeat == 0 else order[::-1]):
                yield case, 'cold', repeat, arm


def generated_outputs():
    for study in ('adaptive', 'sparse'):
        load_spec(study)
    _, cases = aa_outputs()
    old, _ = v4_outputs()
    proto = old[ROOT/'simulation/webots/protos/BlindDroneV4.proto'].replace('BlindDroneV4', 'BlindDroneSensorPilots').replace('"drone_v4"', '"drone_sensor_pilots"')
    world = old[ROOT/'simulation/webots/worlds/observed_v4.wbt'].replace('BlindDroneV4', 'BlindDroneSensorPilots').replace('"lab_v4"', '"lab_sensor_pilots"')
    index = {'schema_version': 1, 'scope': 'twelve exposed A/A pilot cases',
             'cases': [{'id': c['id'], 'case_sha256': digest(c)} for c in cases]}
    return {ROOT/'simulation/webots/protos/BlindDroneSensorPilots.proto': proto, WORLD: world,
            INDEX: json.dumps(index, indent=2)+'\n'}, cases


def select_cases(split='development', requested=None, study='adaptive'):
    if split != 'development':
        raise ValueError('Sensor pilots are development only; validation/test remain closed')
    cases = json.loads(FIXTURE.read_text())['cases']
    index = json.loads(INDEX.read_text())
    if [(c['id'], digest(c)) for c in cases] != [(c['id'], c['case_sha256']) for c in index['cases']]:
        raise ValueError('Sensor pilot fixture commitment mismatch')
    chosen = [c for c in cases if not requested or c['id'] in requested]
    if not chosen or (requested and set(requested) != {c['id'] for c in chosen}):
        raise ValueError('Unknown sensor pilot case')
    return chosen, digest({'index': index, 'spec': load_spec(study)})


def inventory():
    paths = list(VERSION.rglob('*.py')) + list(VERSION.glob('*.toml')) + [INDEX, WORLD,
            ROOT/'simulation/webots/protos/BlindDroneSensorPilots.proto']
    paths += [ROOT/('tools/'+name+'.py') for name in ('build_sensor_pilots', 'run_sensor_pilots', 'review_sensor_pilots')]
    for name in ('drone_sensor_pilots', 'lab_sensor_pilots'):
        paths += list((ROOT/'simulation/webots/controllers'/name).glob('*.py'))
    return {**retention_inventory(), **{str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}}
