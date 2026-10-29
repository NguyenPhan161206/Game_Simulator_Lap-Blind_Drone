"""Independent development replay for the occupied-only candidate."""
from copy import deepcopy
import json
from math import cos, hypot, sin
from pathlib import Path

from blind_drone.contracts.runtime import VehicleState
from blind_drone.experiments.protocol_v2 import load_v2_config
from blind_drone.navigation.cadence import AcquisitionGrid
from blind_drone.sensors.acquisition import SampledObservation
from blind_drone_v4.audit import audit_v4_pair, summarize as summarize_v4
from blind_drone_data03.navigation import OccupiedOnlyAcquisitionGrid


def occupied_only_command_audit(folder, row):
    config = load_v2_config()
    grid = OccupiedOnlyAcquisitionGrid(config['navigation_v2'], config['vehicle']['body_size_m'],
                                       config['sensors']['horizontal_origin_radius_m'])
    prefix = 'candidate' + str(row['repeat'])
    samples = {}
    for line in (folder / (prefix + '-acquisition.jsonl')).read_text().splitlines():
        item = json.loads(line)
        pose = VehicleState(**{k: tuple(v) if isinstance(v, list) else v for k, v in item['pose'].items()})
        samples[item['time_s']] = {'sample_time_s': item['time_s'], 'frame': 'body_FLU',
                                   'readings': item['readings'], 'acquisition_state': pose}
    from dataclasses import replace
    checked = moving = peak_occupied_json_bytes = 0
    for line in (folder / (prefix + '-decisions.jsonl')).read_text().splitlines():
        decision = json.loads(line)
        pose = replace(samples[decision['pose_time_s']]['acquisition_state'], time_s=decision['time_s'])
        obs = SampledObservation.construct(pose, samples[decision['sample_time_s']])
        command = decision['command']
        if not obs.usable(config['navigation']['range_max_age_s'], config['sensors']['range_max_m']):
            if hypot(command['forward_m_s'], command['left_m_s']) > 1e-9:
                raise ValueError('Movement on invalid observation')
            continue
        previous_sample = grid.last_sample
        grid.update(obs)
        if grid.last_sample != previous_sample:
            peak_occupied_json_bytes = max(peak_occupied_json_bytes,
                len(json.dumps(sorted(grid.occupied), separators=(',', ':')).encode()))
        if decision['target_m'] is not None and not __import__('blind_drone_v4.navigation', fromlist=['observed_segment']).observed_segment(
                grid, pose.position_m, decision['target_m'], decision['recovery']):
            raise ValueError('Target depends on expired or unknown free cells')
        forward, left = command['forward_m_s'], command['left_m_s']
        yaw = pose.attitude_rad[2]
        vx, vy = cos(yaw) * forward - sin(yaw) * left, sin(yaw) * forward + cos(yaw) * left
        if hypot(vx, vy) > .4 + 1e-8:
            raise ValueError('DATA-03 candidate exceeded fixed horizontal speed')
        if hypot(vx, vy) > 1e-9:
            moving += 1
            segment = (pose.position_m[0] + vx * .016, pose.position_m[1] + vy * .016)
            observed_segment = __import__('blind_drone_v4.navigation', fromlist=['observed_segment']).observed_segment
            if decision['target_m'] is None or not observed_segment(grid, pose.position_m, segment, decision['recovery']):
                raise ValueError('Final command is not supported by current/retained free evidence')
        checked += 1
    return {'decisions_checked': checked, 'nonzero_horizontal_commands': moving,
            'occupied_only_evidence_checks_passed': True,
            'peak_persistent_occupied_cells': grid.peak_persistent_occupied_cells,
            'peak_ephemeral_free_cells': grid.peak_ephemeral_free_cells,
            'peak_blocked_cells': grid.peak_blocked_cells,
            'peak_retained_cells': grid.peak_retained_cells,
            'peak_map_entries': grid.peak_map_entries,
            'peak_occupied_json_bytes': peak_occupied_json_bytes}


def audit_data03_pair(folder, case, spec, result):
    adapted = deepcopy(result)
    for row in adapted['episodes']:
        if row['arm'] == 'candidate':
            if row['policy_version'] != 'occupied_only_data03':
                raise ValueError('Wrong DATA-03 candidate policy identity')
            row['policy_version'] = 'observed_detour_v4'
    audits = audit_v4_pair(folder, case, spec, adapted)
    by_repeat = {row['repeat']: row for row in result['episodes'] if row['arm'] == 'candidate'}
    for audit in audits:
        if audit['arm'] == 'candidate':
            audit.update(occupied_only_command_audit(Path(folder), by_repeat[audit['repeat']]))
    return audits


def summarize(episodes, cases, audits):
    comparison = summarize_v4(episodes, cases, audits)
    candidates = [e for e in episodes if e['arm'] == 'candidate']
    evidence = [a for group in audits for a in group if a['arm'] == 'candidate']
    gates = {
        'candidate_collision_zero': comparison['by_arm']['candidate']['outcomes'].get('collision', 0) == 0,
        'candidate_bounds_zero': comparison['by_arm']['candidate']['outcomes'].get('out_of_bounds', 0) == 0,
        'candidate_negative_false_success_zero': comparison['by_arm']['candidate']['negative_false_success'] == 0,
        'all_commands_verified_from_occupied_only_replay': all(a['occupied_only_evidence_checks_passed'] for a in evidence),
        'map_budget_not_exceeded': all(not e['resources'].get('budget_exhausted', False) and
                                      e['resources'].get('peak_map_entries', 0) <= 16000 for e in candidates),
    }
    comparison['scope'] = 'exposed v4 development cases; diagnostic only; no held-out inference'
    comparison['data03'] = {
        'free_cell_retention': 'latest unique acquisition only',
        'occupied_hit_retention': 'persistent within episode',
        'all_development_candidate_decisions_replayed': sum(a['decisions_checked'] for a in evidence),
        'candidate_peak_persistent_occupied_cells': max((a['peak_persistent_occupied_cells'] for a in evidence), default=0),
        'candidate_peak_ephemeral_free_cells': max((a['peak_ephemeral_free_cells'] for a in evidence), default=0),
        'candidate_peak_blocked_cells': max((a['peak_blocked_cells'] for a in evidence), default=0),
        'candidate_peak_retained_cells': max((a['peak_retained_cells'] for a in evidence), default=0),
        'candidate_peak_map_entries': max((a['peak_map_entries'] for a in evidence), default=0),
        'candidate_peak_canonical_occupied_json_bytes': max((a['peak_occupied_json_bytes'] for a in evidence), default=0),
        'gates': gates,
        'engineering_targets_met': all(gates.values()),
        'interpretation': 'Canonical JSON bytes describe an encoding; RSS is the measured process-memory signal.',
    }
    return comparison
