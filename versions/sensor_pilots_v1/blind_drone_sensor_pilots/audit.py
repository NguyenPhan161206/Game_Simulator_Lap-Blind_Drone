"""Offline Retention evidence audit. Privileged physics is used only for scoring."""
from dataclasses import replace
import json
from math import cos, dist, hypot, isfinite, pi, sin

from blind_drone.contracts.runtime import VehicleState
from blind_drone.evaluation.cadence import CadenceEvaluator
from blind_drone.experiments.protocol_v2 import load_v2_config
from blind_drone.navigation.cadence import AcquisitionGrid
from blind_drone.sensors.acquisition import cpu_summary
from blind_drone_sensor_pilots.sampling import acquisition_summary, encode_packet, names_for, observation_class
from blind_drone_v4.audit import actual_clearance
from blind_drone_v4.navigation import observed_segment
from blind_drone_sensor_pilots.protocol import execution_arms, profile_for
from blind_drone_retention.navigation import RetentionGrid
from blind_drone_aa.audit import compare_value


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def audit_episode(folder, case, spec, row):
    if (row['case_id'] != case['id'] or row['geometry_sha256'] != case['geometry_sha256'] or
            row['policy_version'] != 'sensor_pilots_v1' or row['period_ms'] != 32):
        raise ValueError('Retention case/policy identity mismatch')
    token = row['arm'] + str(row['repeat'])
    profile = profile_for(spec['study'], row['arm'])
    if row['sensor_profile'] != profile:
        raise ValueError('Wrong public sensor profile')
    packet_size = 16+8*len(names_for(profile))
    samples = read_rows(folder / (token + '-acquisition.jsonl'))
    binary = (folder / (token + '-range.bin')).read_bytes()
    if len(binary) != len(samples)*packet_size:
        raise ValueError('Acquisition binary length mismatch')
    by_time = {}
    for index, sample in enumerate(samples):
        if set(sample['readings']) != set(names_for(profile)):
            raise ValueError('Enabled sensor vocabulary mismatch')
        pose = VehicleState(**{k: tuple(v) if isinstance(v, list) else v for k, v in sample['pose'].items()})
        packet = {'sample_time_s': sample['time_s'], 'frame': 'body_FLU',
                  'readings': sample['readings'], 'acquisition_state': pose}
        if (sample['time_s'] in by_time or pose.time_s != sample['time_s'] or
                encode_packet(sample['sequence'], packet) != binary[index*packet_size:(index+1)*packet_size]):
            raise ValueError('Acquisition sequence/pose/binary mismatch')
        by_time[sample['time_s']] = packet
    kept = [s for s in samples if s['time_s'] <= row['end_s']+1e-8]
    summary = acquisition_summary(kept, row['epoch_s'], row['end_s'], profile, row['score_start_s'])
    if summary != row['acquisition'] or not summary['schedule_complete']:
        raise ValueError('Acquisition schedule/accounting mismatch')
    if not set(row['device_periods_ms'].values()).issubset({32, 64}) or set(row['pose_periods_ms'].values()) != {32}:
        raise ValueError('Wrong effective device cadence')
    if json.loads((folder / (token + '-initialization.json')).read_text()) != row['initialization']:
        raise ValueError('Initialization metadata mismatch')
    all_decisions = read_rows(folder / (token + '-decisions.jsonl'))
    decisions = [d for d in all_decisions if row['score_start_s']+1e-8 < d['time_s'] <= row['end_s']+1e-8]
    if len(decisions) != round((row['end_s']-row['score_start_s'])/.016):
        raise ValueError('Incomplete decision trace')
    if cpu_summary([d['cpu_ms'] for d in decisions]) != row['cpu'] or cpu_summary([d['wall_ms'] for d in decisions]) != row['decision_wall']:
        raise ValueError('CPU/wall accounting mismatch')
    if cpu_summary([d['control_cpu_ms'] for d in decisions]) != row['control_cpu']:
        raise ValueError('Control CPU accounting mismatch')
    pose_rows = read_rows(folder/(token+'-pose.jsonl'))
    poses = {}
    for index, point in enumerate(pose_rows, 1):
        if abs(point['time_s']-row['epoch_s']-index*.032) > 1e-8:
            raise ValueError('Missing pose acquisition tick')
        poses[point['time_s']] = VehicleState(**{k: tuple(v) if isinstance(v, list) else v for k, v in point.items()})
    if any(packet['acquisition_state'] != poses.get(time) for time, packet in by_time.items()):
        raise ValueError('Range acquisition pose differs from measured pose log')
    previous = None
    position = 0
    for sample in samples:
        while position < len(all_decisions) and all_decisions[position]['time_s'] < sample['time_s']-1e-8:
            previous = all_decisions[position]
            position += 1
        expected_status = (previous['status'] if previous else 'waiting_for_sensors') if sample['time_s'] > row['score_start_s']+1e-8 else None
        if sample['scheduler_status'] != expected_status:
            raise ValueError('Scheduler did not use preceding public navigator status')
    config = load_v2_config()
    grid = RetentionGrid(config['navigation_v2'], config['vehicle']['body_size_m'], config['sensors']['horizontal_origin_radius_m'], None)
    snapshots = []
    moving = 0
    for index, decision in enumerate(all_decisions):
        if index and abs(decision['time_s']-all_decisions[index-1]['time_s']-.016) > 1e-8:
            raise ValueError('Missing decision tick')
        if (not 0 <= decision['time_s']-decision['sample_time_s'] <= spec['range_max_age_s'] or
                not 0 <= decision['time_s']-decision['pose_time_s'] < .032+1e-8 or
                decision['reused'] != (index > 0 and decision['sample_time_s'] == all_decisions[index-1]['sample_time_s'])):
            raise ValueError('Observation timing/reuse mismatch')
        pose = replace(poses[decision['pose_time_s']], time_s=decision['time_s'])
        observation = observation_class(profile).construct(pose, by_time[decision['sample_time_s']])
        usable = observation.usable(config['navigation']['range_max_age_s'], config['sensors']['range_max_m'])
        if not usable:
            if profile != 'dropout' or any(value != 0 for value in decision['command'].values()) or decision['status'] != 'invalid_or_stale_observation':
                raise ValueError('Missing/invalid input was not stopped conservatively')
        else:
            grid.update(observation)
        if grid.snapshot() != decision['retention']:
            raise ValueError('Retention state differs from raw replay')
        if row['score_start_s']+1e-8 < decision['time_s'] <= row['end_s']+1e-8:
            snapshots.append(grid.snapshot())
        if decision['target_m'] is not None and not observed_segment(grid, pose.position_m, decision['target_m'], decision['recovery']):
            raise ValueError('Unobserved selected target')
        command = decision['command']; yaw = pose.attitude_rad[2]
        vx, vy = cos(yaw)*command['forward_m_s']-sin(yaw)*command['left_m_s'], sin(yaw)*command['forward_m_s']+cos(yaw)*command['left_m_s']
        if hypot(vx, vy) > .4+1e-8:
            raise ValueError('Retention exceeded fixed speed')
        if hypot(vx, vy) > 1e-9:
            moving += 1
            if decision['target_m'] is None or not observed_segment(grid, pose.position_m,
                    (pose.position_m[0]+vx*.016, pose.position_m[1]+vy*.016), decision['recovery']):
                raise ValueError('Unobserved final command')
    if row['diagnostics']['retention'] != grid.snapshot():
        raise ValueError('Final retention accounting mismatch')
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
    return {'mean_free_entries': sum(s['free'] for s in snapshots)/len(snapshots),
            'mean_map_entries': sum(s['entries'] for s in snapshots)/len(snapshots),
            'peak_map_entries': max(s['peak_entries'] for s in snapshots),
            'expired_free': grid.expired_free,
            'budget_exhausted': grid.exhausted,
            'commands_checked': len(all_decisions), 'nonzero_commands': moving,
            'minimum_scored_polyline_surface_clearance_m': actual_clearance(folder, case, row),
            'raw_audit_passed': True}


def audit_attempt(folder, case, spec, result, mode, repeat, arm):
    if arm not in spec['arms']:
        raise ValueError('Arm does not belong to sensor study')
    expected = execution_arms(case['id'], repeat, mode, arm)
    if (result.get('status') != 'complete' or result['mode'] != mode or result['repeat'] != repeat or
            result['scheduled_arms'] != expected or [e['arm'] for e in result['episodes']] != expected):
        raise ValueError('Retention process schedule mismatch')
    if any(e['repeat'] != repeat for e in result['episodes']):
        raise ValueError('Wrong repeat')
    return [audit_episode(folder, case, spec, row) for row in result['episodes']]


def mean(values):
    return sum(values)/len(values) if values else None


def ratio(left, right):
    return left/right if left is not None and right is not None and right > 0 else None


def frontier(points):
    """Finite observed Pareto set within ONE paired experiment, never a minimum."""
    keys = ('payload_rate_mean_B_s', 'cpu_mean_ms', 'rss_peak_mean_mib')
    def dominates(a, b):
        return (a['feasible_case_success'] >= b['feasible_case_success'] and
                all(a[k] <= b[k] for k in keys) and
                (a['feasible_case_success'] > b['feasible_case_success'] or any(a[k] < b[k] for k in keys)))
    return [label for label, point in points.items()
            if not any(other != label and dominates(value, point) for other, value in points.items())]


def summarize(rows, cases, spec):
    expected = {(c['id'], 'cold', repeat, arm) for c in cases
                for repeat in (0, 1) for arm in spec['arms']}
    keyed = {(r['episode']['case_id'], r['mode'], r['episode']['repeat'], r['episode']['arm']): r for r in rows}
    if len(keyed) != len(rows) or set(keyed) != expected:
        raise ValueError('Incomplete/duplicate sensor pilot matrix')
    by_arm = {}
    successes = {}
    initialization = []
    for case in cases:
        baseline = keyed[(case['id'], 'cold', 0, 'reference')]['episode']
        for repeat, arm in [(rep, label) for rep in (0, 1) for label in spec['arms'] if (rep, label) != (0, 'reference')]:
            other = keyed[(case['id'], 'cold', repeat, arm)]['episode']
            initial_keys = ('initial_position_m', 'initial_velocity_m_s', 'initial_yaw_rad',
                            'measured_initial', 'initialization', 'epoch_s', 'score_start_s')
            mismatch = compare_value({k: baseline[k] for k in initial_keys},
                                     {k: other[k] for k in initial_keys}, spec['equivalence'])
            initialization.append({'case_id': case['id'], 'repeat': repeat, 'arm': arm,
                                   'first_mismatch': mismatch, 'met': mismatch is None})
    for arm in spec['arms']:
        group = [r for r in rows if r['episode']['arm'] == arm]
        episodes = [r['episode'] for r in group]
        successes[arm] = {c['id'] for c in cases if c['feasible'] and all(
            keyed[(c['id'], 'cold', repeat, arm)]['episode']['outcome'] == 'success' for repeat in (0, 1))}
        cpu_count = sum(e['cpu']['decisions'] for e in episodes)
        by_arm[arm] = {
            'episodes': len(episodes), 'feasible_cases': sum(c['feasible'] for c in cases),
            'feasible_case_success': len(successes[arm]),
            'failed_feasible_case_ids': [c['id'] for c in cases if c['feasible'] and c['id'] not in successes[arm]],
            'outcomes': {outcome: sum(e['outcome'] == outcome for e in episodes)
                         for outcome in sorted({e['outcome'] for e in episodes})},
            'mean_free_entries': mean([r['audit']['mean_free_entries'] for r in group]),
            'mean_map_entries': mean([r['audit']['mean_map_entries'] for r in group]),
            'peak_map_entries': max(r['audit']['peak_map_entries'] for r in group),
            'expired_free': sum(r['audit']['expired_free'] for r in group),
            'cpu_mean_ms': mean([e['cpu']['mean_ms'] for e in episodes]),
            'cpu_max_ms': max(e['cpu']['max_ms'] for e in episodes),
            'control_cpu_mean_ms': mean([e['control_cpu']['mean_ms'] for e in episodes]),
            'control_cpu_p95_episode_mean_ms': mean([e['control_cpu']['p95_ms'] for e in episodes]),
            'control_cpu_max_ms': max(e['control_cpu']['max_ms'] for e in episodes),
            'control_cpu_over_16_ms': sum(e['control_cpu']['over_16_ms'] for e in episodes),
            'cpu_p95_episode_mean_ms': mean([e['cpu']['p95_ms'] for e in episodes]),
            'cpu_over_16_ms': sum(e['cpu']['over_16_ms'] for e in episodes),
            'cpu_over_16_fraction': sum(e['cpu']['over_16_ms'] for e in episodes)/cpu_count,
            'rss_peak_mean_mib': mean([e['resources']['rss_peak_mib'] for e in episodes]),
            'rss_peak_max_mib': max(e['resources']['rss_peak_mib'] for e in episodes),
            'all_outcome_elapsed_mean_s': mean([e['elapsed_s'] for e in episodes]),
            'all_outcome_path_mean_m': mean([e['path_length_m'] for e in episodes]),
            'payload_rate_mean_B_s': mean([e['acquisition']['scored']['payload_bytes_per_s'] for e in episodes]),
            'acquisition_payload_B_s': sorted({e['acquisition']['scored']['payload_bytes_per_s'] for e in episodes}),
            'raw_log_bytes': sum(sum(e['files_bytes'].values()) for e in episodes),
        }
    candidate = spec['candidate_arm']
    common = successes['reference'] & successes[candidate]
    paired = {}
    for metric in ('elapsed_s', 'path_length_m'):
        paired[metric+'_ratio'] = mean([ratio(
            mean([keyed[(cid, 'cold', rep, candidate)]['episode'][metric] for rep in (0, 1)]),
            mean([keyed[(cid, 'cold', rep, 'reference')]['episode'][metric] for rep in (0, 1)]))
            for cid in sorted(common)])
    ref, cand = by_arm['reference'], by_arm[candidate]
    comparisons = {name: ratio(cand[key], ref[key]) for name, key in (
        ('payload_rate_ratio', 'payload_rate_mean_B_s'), ('cpu_mean_ratio', 'cpu_mean_ms'),
        ('rss_mean_peak_ratio', 'rss_peak_mean_mib'))}
    comparisons.update(paired)
    gates_spec = spec['gates']
    episodes = [r['episode'] for r in rows]
    gates = {
        'reference_task_quality': ref['feasible_case_success']/ref['feasible_cases'] >= gates_spec['minimum_case_success'],
        'candidate_task_quality': cand['feasible_case_success']/cand['feasible_cases'] >= gates_spec['minimum_case_success'],
        'no_lost_reference_cases': len(successes['reference']-successes[candidate]) <= gates_spec['maximum_lost_cases'],
        'collision_zero': all(e['outcome'] != 'collision' for e in episodes),
        'bounds_zero': all(e['outcome'] != 'out_of_bounds' for e in episodes),
        'negative_false_success_zero': all(e['feasible'] or e['outcome'] != 'success' for e in episodes),
        'initialization_equivalent': all(pair['met'] for pair in initialization),
        'all_raw_audits_passed': all(r['audit']['raw_audit_passed'] for r in rows),
        'map_budget_not_exceeded': all(not r['audit']['budget_exhausted'] and
            r['audit']['peak_map_entries'] <= 16000 for r in rows),
    }
    for key, limit in [('payload_rate_ratio', 'maximum_payload_rate_ratio'), ('cpu_mean_ratio', 'maximum_cpu_mean_ratio'),
                       ('rss_mean_peak_ratio', 'maximum_rss_mean_peak_ratio'), ('elapsed_s_ratio', 'maximum_elapsed_mean_ratio'),
                       ('path_length_m_ratio', 'maximum_path_mean_ratio')]:
        gates[key] = comparisons[key] is not None and comparisons[key] <= gates_spec[limit]
    return {'scope': '12 exposed sensor pilot cases; no held-out or absolute minimum/privacy inference', 'study': spec['study'],
            'met': all(gates.values()), 'gates': gates, 'by_arm': by_arm, 'ratios': comparisons,
            'common_success_cases': len(common), 'lost_reference_case_ids': sorted(successes['reference']-successes[candidate]),
            'initialization_comparisons': initialization, 'observed_pareto_arms': frontier({arm: metrics for arm, metrics in by_arm.items() if arm != 'dropout'}),
            'diagnostic_only_arms': ['dropout'] if spec['study'] == 'sparse' else [],
            'commands_checked': sum(r['audit']['commands_checked'] for r in rows)}
