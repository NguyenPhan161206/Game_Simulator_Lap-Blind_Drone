"""Offline A/A evidence audit. Privileged physics is used only for scoring."""
from dataclasses import replace
import json
from math import cos, dist, hypot, isfinite, pi, sin

from blind_drone.contracts.runtime import VehicleState
from blind_drone.evaluation.cadence import CadenceEvaluator
from blind_drone.experiments.protocol_v2 import load_v2_config
from blind_drone.navigation.cadence import AcquisitionGrid
from blind_drone.sensors.acquisition import SampledObservation, acquisition_summary, cpu_summary, encode_packet
from blind_drone_v4.audit import actual_clearance
from blind_drone_v4.navigation import observed_segment
from blind_drone_aa.protocol import execution_arms


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def audit_episode(folder, case, spec, row):
    if (row['case_id'] != case['id'] or row['geometry_sha256'] != case['geometry_sha256'] or
            row['policy_version'] != 'observed_detour_v4_aa' or row['period_ms'] != 32):
        raise ValueError('A/A case/policy identity mismatch')
    token = row['arm'] + str(row['repeat'])
    samples = read_rows(folder / (token + '-acquisition.jsonl'))
    binary = (folder / (token + '-range.bin')).read_bytes()
    if len(binary) != len(samples)*96:
        raise ValueError('Acquisition binary length mismatch')
    by_time = {}
    for index, sample in enumerate(samples):
        pose = VehicleState(**{k: tuple(v) if isinstance(v, list) else v for k, v in sample['pose'].items()})
        packet = {'sample_time_s': sample['time_s'], 'frame': 'body_FLU',
                  'readings': sample['readings'], 'acquisition_state': pose}
        if (sample['time_s'] in by_time or pose.time_s != sample['time_s'] or
                encode_packet(sample['sequence'], packet) != binary[index*96:(index+1)*96]):
            raise ValueError('Acquisition sequence/pose/binary mismatch')
        by_time[sample['time_s']] = packet
    kept = [s for s in samples if s['time_s'] <= row['end_s']+1e-8]
    summary = acquisition_summary(kept, row['epoch_s'], row['end_s'], 32, row['score_start_s'])
    if summary != row['acquisition'] or not summary['schedule_complete']:
        raise ValueError('Acquisition schedule/accounting mismatch')
    if set(row['device_periods_ms'].values()) != {32} or set(row['pose_periods_ms'].values()) != {32}:
        raise ValueError('Wrong effective device cadence')
    if json.loads((folder / (token + '-initialization.json')).read_text()) != row['initialization']:
        raise ValueError('Initialization metadata mismatch')
    decisions = read_rows(folder / (token + '-decisions.jsonl'))
    decisions = [d for d in decisions if row['score_start_s']+1e-8 < d['time_s'] <= row['end_s']+1e-8]
    if len(decisions) != round((row['end_s']-row['score_start_s'])/.016):
        raise ValueError('Incomplete decision trace')
    if cpu_summary([d['cpu_ms'] for d in decisions]) != row['cpu'] or cpu_summary([d['wall_ms'] for d in decisions]) != row['decision_wall']:
        raise ValueError('CPU/wall accounting mismatch')
    config = load_v2_config()
    grid = AcquisitionGrid(config['navigation_v2'], config['vehicle']['body_size_m'], config['sensors']['horizontal_origin_radius_m'])
    moving = 0
    for index, decision in enumerate(decisions):
        if index and abs(decision['time_s']-decisions[index-1]['time_s']-.016) > 1e-8:
            raise ValueError('Missing decision tick')
        if (not 0 <= decision['time_s']-decision['sample_time_s'] <= spec['range_max_age_s'] or
                not 0 <= decision['time_s']-decision['pose_time_s'] < .032+1e-8 or
                decision['reused'] != (index > 0 and decision['sample_time_s'] == decisions[index-1]['sample_time_s'])):
            raise ValueError('Observation timing/reuse mismatch')
        pose = replace(by_time[decision['pose_time_s']]['acquisition_state'], time_s=decision['time_s'])
        observation = SampledObservation.construct(pose, by_time[decision['sample_time_s']])
        if not observation.usable(config['navigation']['range_max_age_s'], config['sensors']['range_max_m']):
            raise ValueError('Invalid observation in ideal A/A development')
        grid.update(observation)
        if decision['target_m'] is not None and not observed_segment(grid, pose.position_m, decision['target_m'], decision['recovery']):
            raise ValueError('Unobserved selected target')
        command = decision['command']; yaw = pose.attitude_rad[2]
        vx, vy = cos(yaw)*command['forward_m_s']-sin(yaw)*command['left_m_s'], sin(yaw)*command['forward_m_s']+cos(yaw)*command['left_m_s']
        if hypot(vx, vy) > .4+1e-8:
            raise ValueError('A/A exceeded fixed speed')
        if hypot(vx, vy) > 1e-9:
            moving += 1
            if decision['target_m'] is None or not observed_segment(grid, pose.position_m,
                    (pose.position_m[0]+vx*.016, pose.position_m[1]+vy*.016), decision['recovery']):
                raise ValueError('Unobserved final command')
    reads = {'policy_reads': len(decisions), 'reused_reads': sum(d['reused'] for d in decisions),
             'unique_samples_read': len({d['sample_time_s'] for d in decisions}),
             'scored_acquisitions': summary['scored']['packets']}
    if row['observation'] != reads:
        raise ValueError('Read/reuse accounting mismatch')
    evaluator = CadenceEvaluator(case['goal_m'], spec['quality'])
    evaluator.update(0, row['initial_position_m'], row['initial_velocity_m_s'], 0)
    physics = [p for p in read_rows(folder / 'evaluation.jsonl') if p['arm'] == row['arm']]
    scored = None
    for index, point in enumerate(physics, 1):
        if abs(point['time_s']-index*.016) > 1e-8:
            raise ValueError('Missing physics tick')
        scored = evaluator.update(point['time_s'], point['position_m'], point['velocity_m_s'], point['contact_count'])
        if scored and index != len(physics):
            raise ValueError('Scoring continued beyond outcome')
    if not scored or any(row[key] != value for key, value in scored.items()):
        raise ValueError('Physics outcome/path replay mismatch')
    for name, size in row['files_bytes'].items():
        if (folder / name).stat().st_size != size:
            raise ValueError('Raw size mismatch')
    return {'commands_checked': len(decisions), 'nonzero_commands': moving,
            'minimum_scored_polyline_surface_clearance_m': actual_clearance(folder, case, row),
            'raw_audit_passed': True}


def audit_attempt(folder, case, spec, result, mode, repeat, arm):
    expected = execution_arms(case['id'], repeat, mode, arm)
    if (result.get('status') != 'complete' or result['mode'] != mode or result['repeat'] != repeat or
            result['scheduled_arms'] != expected or [e['arm'] for e in result['episodes']] != expected):
        raise ValueError('A/A process schedule mismatch')
    if any(e['repeat'] != repeat for e in result['episodes']):
        raise ValueError('Wrong repeat')
    return [audit_episode(folder, case, spec, row) for row in result['episodes']]


def compare_value(left, right, tolerance, path=''):
    """Return the first mismatch; exact flags/structure, bounded finite numbers."""
    if isinstance(left, bool) or isinstance(right, bool) or left is None or right is None:
        return None if type(left) is type(right) and left == right else path
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        bound = tolerance['timestamp_abs_s'] if path.split('.')[-1] in ('time_s', 'pose_time_s', 'sample_time_s', 'reset_time_s') else tolerance['numeric_abs']
        return None if isfinite(left) and isfinite(right) and abs(left-right) <= bound else path
    if type(left) is not type(right):
        return path
    if isinstance(left, dict):
        if left.keys() != right.keys():
            return path + '.keys'
        for key in left:
            mismatch = compare_value(left[key], right[key], tolerance, path+'.'+key)
            if mismatch is not None:
                return mismatch
        return None
    if isinstance(left, list):
        if len(left) != len(right):
            return path + '.length'
        for index, (a, b) in enumerate(zip(left, right)):
            mismatch = compare_value(a, b, tolerance, path+f'[{index}]')
            if mismatch is not None:
                return mismatch
        return None
    return None if left == right else path


def profile(folder, row):
    token = row['arm']+str(row['repeat'])
    epoch, start = row['epoch_s'], row['score_start_s']
    samples = read_rows(folder / (token+'-acquisition.jsonl'))
    for sample in samples:
        for key in ('time_s', 'pose_time_s'):
            sample[key] = round(sample[key]-epoch, 9)
        sample['pose']['time_s'] = round(sample['pose']['time_s']-epoch, 9)
    decisions = read_rows(folder / (token+'-decisions.jsonl'))
    for decision in decisions:
        for key in ('time_s', 'pose_time_s', 'sample_time_s'):
            decision[key] = round(decision[key]-start, 9)
        for key in ('cpu_ms', 'wall_ms', 'rss_mib'):
            decision.pop(key)
    measured = dict(row['measured_initial'])
    for key in ('time_s', 'pose_time_s', 'sample_time_s'):
        measured[key] = round(measured[key]-epoch, 9)
    initialization = dict(row['initialization'])
    initialization['reset_time_s'] = round(initialization['reset_time_s']-epoch, 9)
    physics = [p for p in read_rows(folder/'evaluation.jsonl') if p['arm'] == row['arm']]
    for point in physics:
        point.pop('arm')
    return {'initial': {key: row[key] for key in ('initial_position_m', 'initial_velocity_m_s', 'initial_yaw_rad')},
            'measured_initial': measured, 'initialization': initialization,
            'acquisition': samples, 'decisions': decisions, 'physics': physics}


def summarize(rows, cases, spec):
    expected = {(c['id'], mode, repeat, arm) for c in cases for mode in ('warm', 'cold')
                for repeat in (0, 1) for arm in ('reference', 'candidate')}
    keyed = {(r['episode']['case_id'], r['mode'], r['episode']['repeat'], r['episode']['arm']): r for r in rows}
    if len(keyed) != len(rows) or set(keyed) != expected:
        raise ValueError('Incomplete/duplicate A/A matrix')
    cold = []
    warm = []
    for case in cases:
        baseline = keyed[(case['id'], 'cold', 0, 'reference')]
        base = baseline['episode']; first = profile(baseline['folder'], base)
        for repeat, arm in ((0, 'candidate'), (1, 'reference'), (1, 'candidate')):
            other = keyed[(case['id'], 'cold', repeat, arm)]; row = other['episode']
            mismatch = compare_value(first, profile(other['folder'], row), spec['equivalence'])
            outcome_equal = base['outcome'] == row['outcome']
            elapsed = abs(base['elapsed_s']-row['elapsed_s'])
            path = abs(base['path_length_m']-row['path_length_m'])
            cold.append({'case_id': case['id'], 'repeat': repeat, 'arm': arm,
                'first_trace_mismatch': mismatch, 'outcome_equal': outcome_equal,
                'elapsed_delta_s': elapsed, 'path_delta_m': path,
                'met': mismatch is None and outcome_equal and elapsed <= spec['equivalence']['elapsed_abs_s'] and path <= spec['equivalence']['path_abs_m']})
        for repeat in (0, 1):
            a, b = [keyed[(case['id'], 'warm', repeat, arm)]['episode'] for arm in ('reference', 'candidate')]
            warm.append({'case_id': case['id'], 'repeat': repeat,
                'initial_position_delta_m': dist(a['initial_position_m'], b['initial_position_m']),
                'initial_velocity_delta_m_s': dist(a['initial_velocity_m_s'], b['initial_velocity_m_s']),
                'initial_yaw_delta_rad': abs((a['initial_yaw_rad']-b['initial_yaw_rad']+pi)%(2*pi)-pi),
                'reference_outcome': a['outcome'], 'candidate_outcome': b['outcome'],
                'elapsed_delta_s': abs(a['elapsed_s']-b['elapsed_s']),
                'path_delta_m': abs(a['path_length_m']-b['path_length_m'])})
    all_episodes = [r['episode'] for r in rows]
    gates = {'cold_equivalent_all_cases': all(r['met'] for r in cold),
             'collision_zero': not any(e['outcome'] == 'collision' for e in all_episodes),
             'bounds_zero': not any(e['outcome'] == 'out_of_bounds' for e in all_episodes),
             'negative_false_success_zero': not any(not e['feasible'] and e['outcome'] == 'success' for e in all_episodes),
             'all_raw_audits_passed': all(r['audit']['raw_audit_passed'] for r in rows)}
    return {'scope': 'exposed development A/A preflight; no retention treatment or held-out inference',
            'gates': gates, 'met': all(gates.values()), 'cold_comparisons': cold, 'warm_pairs': warm,
            'commands_checked': sum(r['audit']['commands_checked'] for r in rows),
            'by_mode': {mode: {'episodes': sum(r['mode'] == mode for r in rows),
                'outcomes': {outcome: sum(r['mode'] == mode and r['episode']['outcome'] == outcome for r in rows)
                             for outcome in sorted({e['outcome'] for e in all_episodes})}}
                for mode in ('warm', 'cold')}}
