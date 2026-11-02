"""Fresh sparse membership and fail-closed source/evidence authorization."""
import hashlib
import json
import os
from pathlib import Path
import tomllib

from blind_drone.experiments.runtime_v3 import git
from blind_drone.world.minimal_lab import ROOT
from blind_drone.world.scenarios import digest
from blind_drone_aa.protocol import generated_outputs as aa_outputs
from blind_drone_sensor_pilots.protocol import (inventory as sensor_inventory,
    generated_outputs as sensor_outputs, schedule, execution_arms)
from check_7a_readiness import NAMES, pick_candidate
from efficiency_design import (build_cases as fresh_cases, design_sources,
    INDEX as DESIGN_INDEX, LOCK as DESIGN_LOCK)

VERSION = ROOT/'versions/efficiency_runtime_v1'
WORLD = ROOT/'simulation/webots/worlds/efficiency_v1.wbt'
INDEX = VERSION/'preflight.index.json'
BINDING = VERSION/'binding.json'
LOCK = VERSION/'runtime.lock.json'
PREFLIGHT = VERSION/'preflight-review.json'
FIXTURE_DIR = ROOT/'artifacts/efficiency-runtime-fixtures'
SPLITS = ('development', 'validation', 'test')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_design():
    lock = json.loads(DESIGN_LOCK.read_text())
    files = design_sources()
    if lock['runtime_ready'] is not False or lock['files'] != files or lock['design_sha256'] != digest(files):
        raise ValueError('Fresh design/source commitment changed')
    return sha(DESIGN_LOCK)


def selection_evidence():
    reports = {key: json.loads((ROOT/'docs/research'/name).read_text()) for key, name in NAMES.items()}
    if any(report.get('local_review_matches_ci') is not True for report in reports.values()):
        raise ValueError('All three source-bound local reviews must match CI before binding')
    selected = pick_candidate(reports)
    if selected['status'] != 'register_fresh_evaluation' or selected['candidate'] != 'sparse':
        raise ValueError('Registered selection has not qualified the sparse candidate')
    return selected, {name: sha(ROOT/'docs/research'/name) for name in NAMES.values()}


def expected_binding():
    selected, hashes = selection_evidence()
    return {'schema_version': 1, 'candidate': 'sparse', 'candidate_source': selected['candidate_source'],
            'source_reviews_sha256': hashes, 'design_lock_sha256': verify_design(),
            'arms': ['reference', 'sparse'], 'scope': 'one fixed candidate; no retuning on validation/test'}


def verify_binding():
    if not BINDING.exists() or json.loads(BINDING.read_text()) != expected_binding():
        raise ValueError('Missing or changed fixed candidate binding')
    return sha(BINDING)


def load_spec(study='sparse', split='development'):
    if study != 'sparse' or split not in SPLITS:
        raise ValueError('Only the registered sparse study/splits are supported')
    spec = tomllib.loads((VERSION/'runtime.toml').read_text())
    if spec['arms'] != ['reference', 'sparse'] or spec['status'] != 'registered_sparse_efficiency_v1':
        raise ValueError('Sparse runtime configuration drift')
    spec['split'] = split
    spec['collector_wall_budget_s'] = 2700 if split == 'development' else 5400
    return spec


def profile_for(study, arm):
    if study != 'sparse' or arm not in ('reference', 'sparse'):
        raise ValueError('Unregistered evaluation profile')
    return 'full' if arm == 'reference' else 'sparse'


def generated_outputs():
    verify_design()
    old, _ = sensor_outputs()
    _, development = aa_outputs()
    proto = old[ROOT/'simulation/webots/protos/BlindDroneSensorPilots.proto'].replace(
        'BlindDroneSensorPilots', 'BlindDroneEfficiency').replace('"drone_sensor_pilots"', '"drone_efficiency"')
    world = old[ROOT/'simulation/webots/worlds/sensor_pilots_v1.wbt'].replace(
        'BlindDroneSensorPilots', 'BlindDroneEfficiency').replace('"lab_sensor_pilots"', '"lab_efficiency"')
    index = {'schema_version': 1, 'scope': 'exposed runtime equivalence preflight',
             'cases': [{'id': c['id'], 'case_sha256': digest(c)} for c in development]}
    return {ROOT/'simulation/webots/protos/BlindDroneEfficiency.proto': proto,
            WORLD: world, INDEX: json.dumps(index, indent=2)+'\n'}, development


def inventory():
    paths = list(VERSION.rglob('*.py')) + [VERSION/'runtime.toml', BINDING, INDEX, WORLD,
        ROOT/'simulation/webots/protos/BlindDroneEfficiency.proto', DESIGN_INDEX, DESIGN_LOCK,
        ROOT/'versions/efficiency_eval_v1/efficiency_design.py', ROOT/'tools/check_7a_readiness.py']
    paths += [ROOT/('tools/'+name+'.py') for name in ('build_efficiency_runtime', 'run_efficiency', 'review_efficiency')]
    for name in ('drone_efficiency', 'lab_efficiency'):
        paths += list((ROOT/'simulation/webots/controllers'/name).glob('*.py'))
    # Evidence/lock are bound separately to avoid self-referential source hashes.
    return {**sensor_inventory(), **{str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}}


def verify_lock():
    verify_binding()
    if not LOCK.exists() or not PREFLIGHT.exists():
        raise ValueError('Runtime equivalence proof and lock required before held-out execution')
    lock = json.loads(LOCK.read_text()); proof = json.loads(PREFLIGHT.read_text())
    if (lock['runtime_sha256'] != digest(inventory()) or lock['binding_sha256'] != sha(BINDING)
            or lock['design_lock_sha256'] != verify_design() or lock['preflight_review_sha256'] != sha(PREFLIGHT)
            or not proof['complete'] or not proof['raw_audit_passed'] or proof['split'] != 'development'
            or proof['episodes'] != 48 or not proof['preflight_equivalence']['met']
            or proof['runtime_sha256'] != lock['runtime_sha256']):
        raise ValueError('Runtime/source/preflight lock mismatch')
    return sha(LOCK)


def validate_test_proof(proof, runtime_hash, binding_hash, design_hash, source):
    if (proof.get('protocol_version') != 'efficiency_runtime_v1' or proof.get('split') != 'validation'
            or proof.get('complete') is not True or proof.get('raw_audit_passed') is not True
            or proof.get('episodes') != 288 or proof.get('cases') != 72
            or proof.get('runtime_sha256') != runtime_hash or proof.get('binding_sha256') != binding_hash
            or proof.get('design_lock_sha256') != design_hash or proof.get('source_commit') != source):
        raise ValueError('Complete source-matched validation review required for test')
    summary = proof.get('summary', {})
    gates = summary.get('gates', {})
    if summary.get('met') is not True or not gates or any(value is not True for value in gates.values()):
        raise ValueError('Validation did not qualify test; do not rerun or retune')


def verify_authorization(split, validation_review=None):
    if split not in SPLITS:
        raise ValueError('Unknown evaluation split')
    verify_binding()
    if split != 'development':
        verify_lock()
    if split == 'test':
        path = validation_review or os.environ.get('BLIND_DRONE_VALIDATION_REVIEW')
        if not path:
            raise ValueError('Missing validation proof; test remains closed')
        validate_test_proof(json.loads(Path(path).read_text()), digest(inventory()), sha(BINDING),
                            verify_design(), git('rev-parse', 'HEAD'))


def fixture_cases(split, validation_review=None):
    verify_authorization(split, validation_review)
    cases = json.loads((FIXTURE_DIR/(split+'.json')).read_text())['cases']
    index = json.loads((INDEX if split == 'development' else DESIGN_INDEX).read_text())['cases']
    expected = [c for c in index if split == 'development' or c['split'] == split]
    if [(c['id'], digest(c)) for c in cases] != [(c['id'], c['case_sha256']) for c in expected]:
        raise ValueError('Evaluation fixture commitment mismatch')
    return cases


def protocol_digest(split):
    return digest({'split': split, 'spec': load_spec('sparse', split), 'binding_sha256': sha(BINDING),
                   'design_lock_sha256': verify_design(), 'preflight_index_sha256': sha(INDEX)})


def select_cases(split='development', requested=None, study='sparse', validation_review=None):
    if study != 'sparse' or (requested and split != 'development'):
        raise ValueError('No held-out subsets or alternative candidates')
    cases = fixture_cases(split, validation_review)
    selected = [c for c in cases if not requested or c['id'] in requested]
    if not selected or (requested and set(requested) != {c['id'] for c in selected}):
        raise ValueError('Unknown registered case')
    return selected, protocol_digest(split)


def select_case(split, case_id, study='sparse'):
    # Supervisor selects the one episode assigned by the complete collector.
    cases, design = select_cases(split, study=study)
    selected = [c for c in cases if c['id'] == case_id]
    if len(selected) != 1:
        raise ValueError('Supervisor received an unregistered case')
    return selected, design


def claim_exposure(split, runtime_hash, output, directory=None):
    if os.environ.get('GITHUB_RUN_ATTEMPT', '1') != '1':
        raise ValueError('Workflow reruns cannot expose validation/test again')
    directory = Path(directory) if directory else ROOT/'artifacts/efficiency-exposure'
    directory.mkdir(parents=True, exist_ok=True)
    marker = directory/(runtime_hash+'-'+split+'.json')
    try:
        with marker.open('x') as stream:
            stream.write(json.dumps({'split': split, 'runtime_sha256': runtime_hash, 'output': str(output),
                                     'source_commit': git('rev-parse', 'HEAD')})+'\n')
    except FileExistsError:
        raise ValueError('Split exposure already claimed; preserve attempts, do not rerun')
    return marker
