"""Fresh geometry commitments only; not an executable evaluation runtime."""
import hashlib
import json
from math import comb
import tomllib

from blind_drone.experiments.protocol_v2 import load_v2_config
from blind_drone.experiments.protocol_v3 import task_fingerprint
from blind_drone.world.geometry import path_certificate
from blind_drone.world.minimal_lab import ROOT
from blind_drone.world.scenarios import digest, generate_case
from blind_drone_v4.protocol import build_cases as exposed_v4, inventory as v4_inventory

VERSION = ROOT/'versions/efficiency_eval_v1'
INDEX = VERSION/'design.index.json'
LOCK = VERSION/'design.lock.json'


def spec():
    value = tomllib.loads((VERSION/'design.toml').read_text())
    if value['runtime_ready'] is not False or value['candidate'] != 'pending_development_readiness_0022':
        raise ValueError('Conditional design cannot become a runtime through a flag change')
    return value


def historical_commitments():
    # v3 test contributes hashes only; its geometry/outcomes are never generated/read.
    old = json.loads((ROOT/'configs/scenarios/range_cadence_v3.index.json').read_text())['cases']
    old = [{k: row[k] for k in ('seed', 'geometry_sha256', 'task_sha256')} for row in old]
    cases = exposed_v4()
    for name in ('seeded_v1.json', 'observed_v2.json'):
        cases += json.loads((ROOT/'configs/scenarios'/name).read_text())['cases']
    old += [{'seed': case['seed'], 'geometry_sha256': case['geometry_sha256'],
             'task_sha256': task_fingerprint(case)} for case in cases]
    return old


def assert_disjoint(cases, commitments):
    seen = {key: {row[key] for row in commitments} for key in ('seed', 'geometry_sha256', 'task_sha256')}
    ids = set()
    for case in cases:
        values = {'seed': case['seed'], 'geometry_sha256': case['geometry_sha256'], 'task_sha256': task_fingerprint(case)}
        if case['id'] in ids or any(value in seen[key] for key, value in values.items()):
            raise ValueError('Duplicate seed, geometry or canonical task; stop without reseeding')
        ids.add(case['id'])
        for key, value in values.items():
            seen[key].add(value)


def build_cases():
    design = spec()
    body = load_v2_config()['vehicle']['body_size_m']
    cases = []
    for split, values in design['splits'].items():
        for index in range(values['feasible_cases']+values['negative_cases']):
            family = design['feasible_families'][index % 5] if index < values['feasible_cases'] else design['negative_family']
            case = generate_case(family, values['first_seed']+index, split)
            case['certificate'] = path_certificate(case, body, .25, .12, [-9., 9.])
            expected = 'conservative_horizontal_grid_witness' if case['feasible'] else 'goal_inside_solid'
            if case['certificate']['kind'] != expected:
                raise ValueError('Invalid registered feasibility certificate')
            cases.append(case)
    assert_disjoint(cases, historical_commitments())
    return cases


def generated_index(cases):
    return {'schema_version': 1, 'scope': 'conditional fresh 7A design, geometry metadata only',
            'runtime_ready': False, 'cases': [{k: c[k] for k in ('id', 'split', 'seed', 'family', 'feasible', 'geometry_sha256')}
                | {'case_sha256': digest(c), 'task_sha256': task_fingerprint(c),
                   'certificate_kind': c['certificate']['kind']} for c in cases]}


def design_sources():
    paths = [VERSION/'design.toml', VERSION/'efficiency_design.py', INDEX,
             ROOT/'tools/build_efficiency_design.py', ROOT/'tools/check_7a_readiness.py']
    paths += [ROOT/'configs/scenarios'/name for name in ('seeded_v1.json', 'observed_v2.json', 'range_cadence_v3.index.json')]
    return {**v4_inventory(), **{str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}


def success_lower_bound(successes, cases, alpha=.05):
    """One-sided exact binomial bound, conditional on the stated task model."""
    if type(successes) is not int or type(cases) is not int or cases < 1 or not 0 <= successes <= cases or not 0 < alpha < 1:
        raise ValueError('Invalid case counts or confidence alpha')
    if not successes:
        return 0.
    low, high = 0., 1.
    for _ in range(80):
        probability = (low+high)/2
        tail = sum(comb(cases, k)*probability**k*(1-probability)**(cases-k) for k in range(successes, cases+1))
        if tail < alpha:
            low = probability
        else:
            high = probability
    return (low+high)/2
