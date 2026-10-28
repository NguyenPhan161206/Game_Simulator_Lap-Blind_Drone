"""Offline development-only diagnosis around the unchanged frozen v3 navigator.

No simulator launch, command substitution, grid repair, or held-out evaluation.
The synthetic sweep examines representation coverage, not physical safety.
"""
import argparse
from collections import Counter
from dataclasses import replace
import json
from math import ceil, cos, hypot, pi, sin
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tools'))
from blind_drone.contracts.runtime import VehicleState
from blind_drone.experiments.protocol_v2 import load_v2_config
from blind_drone.navigation.cadence import CadenceNavigator
from blind_drone.navigation.observed import MissionV2
from blind_drone.observation.range_grid import RangeGrid, rotate_rpy
from blind_drone.sensors.acquisition import SampledObservation
from review_research_v3 import checked_path, review, sha256_file


# These five traces were selected by the earlier public-observation replay,
# before this diagnostic was implemented. They are not all development failures.
TRACE_SELECTION = (
    ('development-empty-s3200020', 0),
    ('development-empty-s3200034', 0),
    ('development-empty-s3200041', 0),
    ('development-narrow_gap-s3200004', 0),
    ('development-narrow_gap-s3200029', 1),
)


def explain_segment(grid, start, end, require_free=True):
    """Read-only first violation, with the frozen segment_ok sampling/precedence."""
    steps = max(1, ceil(hypot(end[0]-start[0], end[1]-start[1]) / (grid.cell_m*.3)))
    for index in range(steps+1):
        point = (start[0]+(end[0]-start[0])*index/steps,
                 start[1]+(end[1]-start[1])*index/steps)
        cell = grid.cell(point)
        reason = ('outside' if not grid.inside(cell) else
                  'blocked' if cell in grid.blocked else
                  'unknown' if require_free and cell not in grid.free else None)
        if reason:
            return {'ok': False, 'reason': reason, 'cell': list(cell),
                    'point_m': list(point), 'sample_index': index, 'steps': steps,
                    'distance_from_start_m': hypot(point[0]-start[0], point[1]-start[1])}
    return {'ok': True, 'reason': None, 'steps': steps}


class SegmentProbe:
    """Observe real predicate calls; always return the original predicate result."""
    def __init__(self, grid):
        self.grid = grid
        self.original = grid.segment_ok
        self.calls = 0
        self.rejections = []

    def __call__(self, start, end, require_free=False):
        accepted = self.original(start, end, require_free)
        detail = explain_segment(self.grid, start, end, require_free)
        if detail['ok'] != accepted:
            raise ValueError('Diagnostic predicate diverged from frozen segment_ok')
        self.calls += 1
        if not accepted:
            detail.update(start_m=list(start), end_m=list(end), require_free=require_free,
                          allowed_without_free=self.original(start, end, False),
                          start_cell_free=self.grid.cell(start) in self.grid.free,
                          start_cell_blocked=self.grid.cell(start) in self.grid.blocked)
            self.rejections.append(detail)
        return accepted


def read_jsonl(path):
    with Path(path).open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def reference_samples(rows, period_ms):
    if type(period_ms) is not int or period_ms != 32:
        raise ValueError('Only reference 32 ms logs retain every required pose')
    samples = {}
    previous = None
    for row in rows:
        time = row['time_s']
        if time in samples or (previous is not None and abs(time-previous-.032) > 1e-8):
            raise ValueError('Duplicate, missing or unordered reference acquisition')
        pose = VehicleState(**{k: tuple(v) if isinstance(v, list) else v
                               for k, v in row['pose'].items()})
        if abs(pose.time_s-time) > 1e-8 or row['pose_time_s'] != time:
            raise ValueError('Acquisition pose timestamp mismatch')
        samples[time] = {'sample_time_s': time, 'frame': 'body_FLU',
                         'readings': row['readings'], 'acquisition_state': pose}
        previous = time
    if not samples:
        raise ValueError('Missing reference acquisitions')
    return samples


def replay_observation(decision, samples):
    try:
        current = samples[decision['pose_time_s']]['acquisition_state']
        sample = samples[decision['sample_time_s']]
    except KeyError as error:
        raise ValueError('Missing recorded pose/sample; interpolation is forbidden') from error
    if current.time_s > decision['time_s'] or sample['sample_time_s'] > decision['time_s']:
        raise ValueError('Future observation in decision')
    return SampledObservation.construct(replace(current, time_s=decision['time_s']), sample)


def cell_coverage_geometry(grid, cell, observations):
    """Sufficient geometric proof for an unvisited cell wholly inside the ray ring.

    With nonnegative ranges, all projected ray samples start at the sensor
    origin and move outward. A cell whose farthest corner is closer than every
    ray origin, at every consumed acquisition, cannot receive those free rays.
    This does NOT prove the unknown cell is physically empty or safe to enter.
    """
    corners = [(grid.cell_m*(cell[0]+x), grid.cell_m*(cell[1]+y))
               for x in (0, 1) for y in (0, 1)]
    center_retains = 0
    wholly_inside = 0
    largest_corner = 0.
    smallest_origin = float('inf')
    max_corner_minus_origin = -float('inf')
    for obs in observations:
        pose = obs.acquisition_state
        center_retains += grid.cell(pose.position_m) == cell
        farthest = max(hypot(x-pose.position_m[0], y-pose.position_m[1]) for x, y in corners)
        origin = min(grid.origin_radius * hypot(*rotate_rpy((cos(a*pi/180), sin(a*pi/180), 0),
                                                           pose.attitude_rad)[:2])
                     for a in range(0, 360, 45))
        wholly_inside += farthest < origin
        largest_corner = max(largest_corner, farthest)
        smallest_origin = min(smallest_origin, origin)
        max_corner_minus_origin = max(max_corner_minus_origin, farthest-origin)
    return {'cell': list(cell), 'consumed_acquisitions': len(observations),
            'center_retains': center_retains, 'wholly_inside_ring_acquisitions': wholly_inside,
            'max_corner_distance_m': largest_corner, 'min_projected_origin_radius_m': smallest_origin,
            'max_corner_minus_origin_m': max_corner_minus_origin,
            'ray_unreachable_for_entire_trace': bool(observations) and wholly_inside == len(observations)
                                              and center_retains == 0,
            'final_free': cell in grid.free, 'final_blocked': cell in grid.blocked}


def replay_trace(folder, episode, event_stream):
    name = f"reference{episode['repeat']}"
    samples = reference_samples(read_jsonl(folder / (name+'-acquisition.jsonl')), episode['period_ms'])
    decisions = read_jsonl(folder / (name+'-decisions.jsonl'))
    # The case is verified by review(); only this whitelisted goal enters policy.
    goal = json.loads((folder / 'case.json').read_text())['goal_m']
    nav = CadenceNavigator(MissionV2(tuple(goal), 'mapped'), load_v2_config())
    probe = SegmentProbe(nav.grid)
    nav.grid.segment_ok = probe
    statuses, reasons, stall_causes, cell_counts = Counter(), Counter(), Counter(), Counter()
    consumed = {}
    nonzero = rejected_decisions = 0
    first = last = None
    first_position = None
    max_displacement = max_pose_separation = max_age = max_pose_age = 0.
    previous = None
    for decision in decisions:
        time = decision['time_s']
        if previous is not None and abs(time-previous-.016) > 1e-8:
            raise ValueError('Missing/unordered policy decision')
        previous = time
        obs = replay_observation(decision, samples)
        probe.rejections = []
        command = nav.step(obs)
        consumed[obs.sample_time_s] = obs
        statuses[nav.status] += 1
        nonzero += hypot(command.forward_m_s, command.left_m_s) > 1e-9
        first_position = first_position or obs.state.position_m
        max_displacement = max(max_displacement, hypot(obs.state.position_m[0]-first_position[0],
                                                     obs.state.position_m[1]-first_position[1]))
        max_pose_separation = max(max_pose_separation, hypot(obs.state.position_m[0]-obs.acquisition_state.position_m[0],
                                                           obs.state.position_m[1]-obs.acquisition_state.position_m[1]))
        max_age = max(max_age, time-obs.sample_time_s)
        max_pose_age = max(max_pose_age, time-decision['pose_time_s'])
        rejected_decisions += bool(probe.rejections)
        for detail in probe.rejections:
            reasons[detail['reason']] += 1
            cell_counts[tuple(detail['cell'])] += 1
        if nav.status == 'scan_unknown_or_blocked':
            cause = ('segment_rejected' if probe.rejections else 'no_path' if not nav.path else
                     'first_waypoint_outside_lookahead' if len(nav.path)>1 and
                     hypot(nav.path[1][0]-obs.state.position_m[0], nav.path[1][1]-obs.state.position_m[1]) > nav.params['lookahead_m']
                     else 'other')
            stall_causes[cause] += 1
        if probe.rejections:
            event = {'case_id': episode['case_id'], 'repeat': episode['repeat'], 'time_s': time,
                     'pose_time_s': decision['pose_time_s'], 'sample_time_s': obs.sample_time_s,
                     'acquisition_position_m': list(obs.acquisition_state.position_m),
                     'status': nav.status, 'path_points': len(nav.path), 'rejections': probe.rejections}
            event_stream.write(json.dumps(event, allow_nan=False)+'\n')
            if first is None:
                first = event
            last = event
    deterministic = {k: v for k, v in nav.diagnostics().items() if not k.startswith('cpu_')}
    expected = {k: v for k, v in episode['diagnostics'].items() if not k.startswith('cpu_')}
    if deterministic != expected:
        raise ValueError('Replay counters differ from original episode: '+episode['case_id'])
    return {'case_id': episode['case_id'], 'repeat': episode['repeat'], 'arm': 'reference',
            'outcome_recorded': episode['outcome'], 'decisions': len(decisions),
            'statuses': dict(statuses), 'nonzero_horizontal_commands': nonzero,
            'predicate_calls_verified': probe.calls, 'rejected_decisions': rejected_decisions,
            'rejection_calls_by_reason': dict(reasons), 'stall_causes': dict(stall_causes),
            'original_deterministic_counters_match': True,
            'deterministic_counters': deterministic,
            'max_horizontal_displacement_m': max_displacement,
            'max_current_acquisition_horizontal_separation_m': max_pose_separation,
            'max_range_age_s': max_age, 'max_pose_age_s': max_pose_age,
            'first_rejection': first, 'last_rejection': last,
            'rejected_cells': [dict(cell_coverage_geometry(nav.grid, cell, list(consumed.values())),
                                    rejection_calls=count)
                               for cell, count in sorted(cell_counts.items())]}


def coverage_sweep():
    """Controlled synthetic map coverage: no obstacles, dynamics or success metric."""
    config = load_v2_config()
    offsets = [i*.025 for i in range(1, 10)]
    output = []
    for origin in (config['sensors']['horizontal_origin_radius_m'], 0.):
        histogram = Counter()
        examples = []
        for x in offsets:
            for y in offsets:
                grid = RangeGrid(config['navigation_v2'], config['vehicle']['body_size_m'], origin)
                for index in range(64):
                    time = index*.032
                    pose = VehicleState(time, (x, y, 1.5), (0., 0., 0.), (0., 0., index*2*pi/64), (0., 0., 0.))
                    # Explicit synthetic 1 m no-return ray, not the runtime 8 m sensor.
                    sample = {'sample_time_s': time, 'frame': 'body_FLU', 'acquisition_state': pose,
                              'readings': {f'range_{a:03d}': {'distance_m': 1., 'valid': True, 'at_limit': True}
                                           for a in range(0, 360, 45)}}
                    grid.update(SampledObservation.construct(pose, sample))
                cell = grid.cell((x, y))
                directions = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
                failed = [list(d) for d in directions if not grid.segment_ok((x, y), grid.center((cell[0]+d[0], cell[1]+d[1])), True)]
                histogram[len(failed)] += 1
                if failed and len(examples) < 3:
                    examples.append({'offset_m': [x, y], 'rejected_adjacent_directions': failed})
        output.append({'origin_radius_m': origin, 'positions': len(offsets)**2,
                       'positions_with_rejected_adjacent_segment': sum(n for k, n in histogram.items() if k),
                       'rejected_segments_per_position_histogram': dict(sorted(histogram.items())),
                       'examples': examples})
    return {'kind': 'synthetic_representation_only', 'cell_m': config['navigation_v2']['cell_m'],
            'offsets_per_axis_m': offsets, 'yaw_samples_full_turn': 64,
            'synthetic_horizontal_range_limit_m': 1., 'obstacle_hits': 0,
            'interpretation': 'origin=0 is a diagnostic control, not an authorized sensor change or safety fix',
            'arms': output}


def diagnose(directory, expected_source, output):
    directory, output = Path(directory).resolve(), Path(output).resolve()
    header = json.loads(checked_path(directory, 'result.json').read_text())
    if header.get('split') != 'development':
        raise ValueError('Diagnosis is development-only; validation/test must not be used')
    if output.exists() or output.is_relative_to(directory) or not output.is_relative_to(ROOT / 'artifacts'):
        raise ValueError('Use a fresh output directory under artifacts, outside raw evidence')
    audited = review(directory, 'development', expected_source)
    selected = []
    for case_id, repeat in TRACE_SELECTION:
        matches = [a for a in header['attempts'] if a['case_id'] == case_id and a['repeat'] == repeat
                   and a['classification'] == 'valid']
        if len(matches) != 1:
            raise ValueError('Expected exactly one valid selected trace')
        attempt = matches[0]
        episode = next(e for e in attempt['result']['episodes'] if e['arm'] == 'reference')
        if episode['outcome'] != 'timeout' or not episode['feasible']:
            raise ValueError('Selected trace no longer matches prior replay')
        selected.append((checked_path(directory, f"{case_id}-r{repeat}-a{attempt['attempt']}"), episode))
    output.mkdir(parents=True)
    with (output / 'rejections.jsonl').open('x') as stream:
        traces = [replay_trace(folder, episode, stream) for folder, episode in selected]
    failures = [e for e in header['episodes'] if e['arm'] == 'reference' and e['feasible'] and e['outcome'] != 'success']
    locks = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'configs/scenarios').glob('*.lock.json'))
    result = {'schema_version': 1, 'kind': 'offline_development_start_diagnostics',
              'complete': True, 'runtime_source_commit': header['source_commit'],
              'raw_result_sha256': audited['raw_result_sha256'],
              'design_sha256': audited['design_sha256'], 'runtime_sha256': audited['runtime_sha256'],
              'locks_file_sha256': {p: sha256_file(ROOT / p) for p in locks},
              'tool_sha256': sha256_file(Path(__file__)), 'raw_audit_passed': True,
              'selection': 'five previously replayed reference traces; not all development failures',
              'reference_feasible_failure_episodes_total': len(failures),
              'reference_feasible_failure_cases_total': len({e['case_id'] for e in failures}),
              'selected_traces': len(traces), 'traces': traces, 'coverage_sweep': coverage_sweep(),
              'rejections_sha256': sha256_file(output / 'rejections.jsonl'),
              'limits': ['No new simulator episodes or improved success result',
                         'Reference only; 64 ms range logs lack intermediate 32 ms poses',
                         'Deterministic counters match; no recorded per-tick command equality claim',
                         'No generalization to all validation failures; no free-space safety inference']}
    (output / 'summary.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--expected-source', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = diagnose(args.directory, args.expected_source, args.output)
    except (ValueError, OSError, KeyError, TypeError, StopIteration) as error:
        print('START_DIAGNOSTICS_FAILED:', error, file=sys.stderr)
        return 2
    print('START_DIAGNOSTICS '+json.dumps({'complete': result['complete'],
                                         'traces': result['selected_traces'], 'output': str(args.output)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
