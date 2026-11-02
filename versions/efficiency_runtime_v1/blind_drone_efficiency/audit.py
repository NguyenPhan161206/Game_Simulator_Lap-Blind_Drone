"""Reuse measured-command audit; add case-level held-out confidence and port checks."""
from pathlib import Path
import json

from blind_drone_sensor_pilots.audit import audit_attempt, summarize as sensor_summary
from blind_drone_aa.audit import profile, compare_value
from efficiency_design import success_lower_bound
from blind_drone_efficiency.protocol import ROOT, sha


def summarize(rows, cases, spec):
    result = sensor_summary(rows, cases, spec)
    split = spec['split']
    result.update(scope='exposed equivalence preflight' if split == 'development' else
                  'fresh '+split+'; static ideal generator only', split=split,
                  study='fixed_sparse_efficiency_v1', diagnostic_only_arms=[])
    by_family = {}
    for family in sorted({c['family'] for c in cases if c['feasible']}):
        members = [c for c in cases if c['feasible'] and c['family'] == family]
        by_family[family] = {arm: {'cases': len(members), 'case_successes': sum(all(
            r['episode']['outcome'] == 'success' for r in rows if r['episode']['case_id'] == c['id']
            and r['episode']['arm'] == arm) for c in members)} for arm in ('reference', 'sparse')}
    result['by_family'] = by_family
    result['success_lower_bound_one_sided_95'] = {
        arm: success_lower_bound(metrics['feasible_case_success'], metrics['feasible_cases'])
        for arm, metrics in result['by_arm'].items()}
    if split != 'development':
        if len(cases) != 72 or sum(c['feasible'] for c in cases) != 60:
            raise ValueError('Held-out case denominator differs from registered design')
        for arm, bound in result['success_lower_bound_one_sided_95'].items():
            result['gates'][arm+'_success_lower_bound'] = bound >= .95
    result['met'] = all(result['gates'].values())
    return result


def trace_profile(folder, row):
    value = profile(folder, row)
    for decision in value['decisions']:
        decision.pop('control_cpu_ms')
    return value


def compare_preflight(rows, new_run, prior_run, spec):
    prior_run = Path(prior_run)
    manifest = json.loads((prior_run/'result.json').read_text())
    evidence = json.loads((ROOT/'docs/research/2026-11-02-sparse-sensors.json').read_text())
    if sha(prior_run/'result.json') != evidence['raw_result_sha256']:
        raise ValueError('Prior raw manifest differs from the bound qualified review')
    if (manifest['status'] != 'complete' or not manifest['integrity_passed']
            or not manifest['complete_split'] or manifest['study'] != 'sparse'
            or manifest['source_commit'] != '9d1e39031c4560b0889c43046f41e8481cb59457'):
        raise ValueError('Qualified source-bound sparse pilot required for port comparison')
    previous = {(r['episode']['case_id'], r['episode']['repeat'], r['episode']['arm']): r
                for r in manifest['rows'] if r['episode']['arm'] in ('reference', 'sparse')}
    compared = []
    attempts = {a['output']: a for a in manifest['attempts'] if a['classification'] == 'valid'}
    for row in rows:
        episode = row['episode']; key = episode['case_id'], episode['repeat'], episode['arm']
        old = previous[key]; folder = prior_run/old['folder']
        if Path(old['folder']).name != old['folder'] or not folder.resolve().is_relative_to(prior_run.resolve()):
            raise ValueError('Prior attempt path escapes run')
        for name, expected in attempts[old['folder']]['files_sha256'].items():
            path = folder/name
            if Path(name).name != name or not path.resolve().is_relative_to(folder.resolve()) or sha(path) != expected:
                raise ValueError('Prior raw hash/path mismatch')
        mismatch = compare_value(trace_profile(Path(new_run)/row['folder'], episode),
                                 trace_profile(folder, old['episode']), spec['equivalence'])
        compared.append({'case_id': key[0], 'repeat': key[1], 'arm': key[2],
                         'first_trace_mismatch': mismatch, 'outcome_equal': episode['outcome'] == old['episode']['outcome'],
                         'met': mismatch is None and episode['outcome'] == old['episode']['outcome']})
    if len(compared) != 48 or len(previous) != 48:
        raise ValueError('Incomplete preflight equivalence matrix')
    return {'met': all(r['met'] for r in compared), 'comparisons': compared,
            'prior_source_commit': manifest['source_commit'], 'prior_raw_result_sha256': sha(prior_run/'result.json')}
