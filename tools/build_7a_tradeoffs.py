"""Derive finite, within-study tradeoffs from reviewed summaries, never pool hosts."""
import argparse
import hashlib
import json
from math import isfinite
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT/'docs/research/2026-11-02-7a-tradeoffs.json'


def pareto(points, costs):
    if len(points) < 2 or not costs:
        raise ValueError('A paired study and explicit cost dimensions are required')
    for point in points.values():
        values = [point['case_successes'], point['feasible_cases'], *[point[k] for k in costs]]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v) or v < 0 for v in values):
            raise ValueError('Missing/nonfinite/negative tradeoff metric')
        if not 0 <= point['case_successes'] <= point['feasible_cases']:
            raise ValueError('Invalid task denominator')
    if len({p['feasible_cases'] for p in points.values()}) != 1:
        raise ValueError('Different task denominators cannot share a frontier')
    def dominates(a, b):
        return (a['case_successes'] >= b['case_successes'] and all(a[k] <= b[k] for k in costs)
                and (a['case_successes'] > b['case_successes'] or any(a[k] < b[k] for k in costs)))
    return [arm for arm, point in points.items() if not any(
        other != arm and dominates(value, point) for other, value in points.items())]


def build_report():
    sources = {}
    def read(name):
        path = ROOT/'docs/research'/name
        sources[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        return json.loads(path.read_text())
    groups = []
    cadence = read('2026-10-28-cadence-v3-development.json')
    if not cadence['local']['all_attempts_valid_and_raw_audited']:
        raise ValueError('Cadence source is not complete and reviewed')
    points = {}
    for arm, metrics in cadence['local']['metrics'].items():
        points[arm] = {'case_successes': cadence['local']['gate']['case_successes'][arm],
            'feasible_cases': cadence['local']['gate']['feasible_cases'],
            'sensor_payload_B_s': sum(metrics['range_payload_rate_min_max'])/2,
            'cpu_mean_ms': metrics['cpu_weighted_mean_ms'], 'rss_peak_mib': metrics['rss_peak_mib'],
            'cpu_max_ms': metrics['cpu_max_ms'], 'cpu_over_16_ms': metrics['cpu_over_16ms'],
            'feasible_episode_outcomes': metrics['feasible_episode_outcomes'],
            'negative_episode_outcomes': metrics['negative_episode_outcomes'],
            'peak_cells_free_plus_occupied_only': metrics['peak_cells']}
    groups.append({'id': 'cadence_v3_local_development', 'source_commit': cadence['source_commit'],
        'cases': 60, 'episodes': cadence['local']['episodes'], 'cpu_aggregation': 'decision weighted mean',
        'memory_aggregation': 'maximum sampled episode RSS', 'points': points,
        'quality_gate_met': cadence['local']['gate']['met'],
        'notes': '32/64 ms, mapped v3, warm sequential. Payload encoding <dIHH10d, 96 B/packet; excludes pose/log/metadata.'})
    for filename, kind in [('2026-10-28-observed-detour-v4.json', 'navigation_v4'),
                           ('2026-10-29-data03-occupied-only.json', 'occupied_only'),
                           ('2026-10-29-data04-hit-ttl.json', 'occupied_ttl_10s')]:
        report = read(filename)
        reviewed = report.get('local_raw_review', report)
        if not reviewed['complete'] or not reviewed['raw_audit_passed']:
            raise ValueError('Incomplete historical source: '+filename)
        points = {}
        for arm, metrics in report['summary']['by_arm'].items():
            points[arm] = {'case_successes': metrics['feasible_case_success'],
                'feasible_cases': metrics['feasible_cases'], 'sensor_payload_B_s': 3000.,
                'cpu_mean_ms': metrics['cpu_mean_ms_weighted'], 'rss_peak_mib': metrics['rss_peak_mib'],
                'cpu_max_ms': metrics['cpu_max_ms'], 'cpu_over_16_ms': metrics['cpu_over_16_ms'],
                'all_episode_outcomes': metrics['outcomes'], 'negative_false_success': metrics['negative_false_success'],
                'failed_feasible_episodes': metrics['failure_episodes']}
        groups.append({'id': kind, 'source_commit': report.get('source_commit', report.get('runtime_source')),
            'cases': 88, 'episodes': 352, 'cpu_aggregation': 'decision weighted mean',
            'memory_aggregation': 'maximum sampled episode RSS', 'points': points,
            'quality_gate_met': report['summary']['engineering_targets_met'],
            'notes': '32 ms, warm sequential. Entry accounting differs across historical studies; no cross-study cell frontier.'})
    optional = ROOT/'docs/research/2026-11-02-retention-cold.json'
    if optional.exists():
        report = read(optional.name)
        if not report['complete'] or not report['raw_audit_passed'] or report['episodes'] != 352:
            raise ValueError('Retention review incomplete')
        points = {}
        for arm, metrics in report['summary']['by_arm'].items():
            points[arm] = {'case_successes': metrics['feasible_case_success'], 'feasible_cases': metrics['feasible_cases'],
                'sensor_payload_B_s': sum(metrics['acquisition_payload_B_s'])/len(metrics['acquisition_payload_B_s']),
                'mean_free_entries': metrics['mean_free_entries'], 'mean_map_entries': metrics['mean_map_entries'],
                'cpu_mean_ms': metrics['cpu_mean_ms'], 'rss_peak_mib': metrics['rss_peak_mean_mib'],
                'cpu_max_ms': metrics['cpu_max_ms'], 'cpu_over_16_ms': metrics['cpu_over_16_ms'],
                'all_episode_outcomes': metrics['outcomes'], 'failed_feasible_cases': metrics['failed_feasible_case_ids']}
        groups.append({'id': 'retention_cold_2s', 'source_commit': report['source_commit'],
            'cases': 88, 'episodes': 352, 'cpu_aggregation': 'equal episode mean',
            'memory_aggregation': 'mean of episode sampled RSS peaks', 'points': points,
            'quality_gate_met': report['summary']['met'],
            'notes': 'Cold isolated; fair free+occupied+blocked+last-seen entry budget; data axis is retained free history, not acquisition.'})
    for group in groups:
        costs = ['sensor_payload_B_s', 'cpu_mean_ms', 'rss_peak_mib']
        if group['id'] == 'retention_cold_2s':
            costs.append('mean_free_entries')
        group['cost_axes'] = costs
        group['observed_pareto_arms'] = pareto(group['points'], costs)
        group['not_a_configuration_selection'] = True
    return {'schema_version': 1, 'scope': 'finite observed within-study development tradeoffs from reviewed summaries',
        'sources_sha256': sources, 'groups': groups, 'global_frontier': None,
        'limitations': ['Historical summaries are consumed; this tool does not repeat their raw audits.',
            'Do not pool different hosts, initializations, budgets, case sets or CPU aggregations.',
            'Pareto membership does not qualify a task/safety/validation gate or establish causality.',
            'Repeats and geometry/yaw variants are not independent new tasks for inference.',
            'Payload excludes pose/metadata/logging; cell entries and encoded bytes are not process RAM.',
            'No absolute information minimum, semantic privacy, energy, radar or hardware safety inference.',
            'v3 validation was negative; v3 test remains closed.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    value = json.dumps(build_report(), indent=2, ensure_ascii=False, allow_nan=False)+'\n'
    if args.check:
        if not REPORT.exists() or REPORT.read_text() != value:
            raise ValueError('Regenerate the reviewed-summary tradeoff report')
    else:
        REPORT.write_text(value)
    print('7A within-study tradeoffs checked; no new simulator or held-out run')


if __name__ == '__main__':
    main()
