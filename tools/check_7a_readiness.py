"""Apply preregistered development selection; this never opens or runs any split."""
import argparse
import hashlib
import json
from math import isfinite
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = {'retention': '2026-11-02-retention-cold.json', 'adaptive': '2026-11-02-adaptive-sensors.json',
         'sparse': '2026-11-02-sparse-sensors.json'}
COUNTS = {'retention': 352, 'adaptive': 48, 'sparse': 72}


def pick_candidate(reviews):
    missing = [key for key in NAMES if key not in reviews]
    for key, report in reviews.items():
        if key not in COUNTS or report['episodes'] != COUNTS[key] or report['complete'] is not True or report['raw_audit_passed'] is not True:
            raise ValueError('Incomplete or unknown registered study')
        source = report['source_commit']
        if len(source) != 40 or any(c not in '0123456789abcdef' for c in source):
            raise ValueError('Full source provenance required')
        summary = report['summary']
        if not summary['gates'] or any(type(v) is not bool for v in summary['gates'].values()) or summary['met'] != all(summary['gates'].values()):
            raise ValueError('Inconsistent development qualification')
    if 'retention' in reviews:
        gates = reviews['retention']['summary']['gates']
        if not gates['reference_task_quality'] or not gates['initialization_equivalent']:
            return {'status': 'baseline_not_ready', 'candidate': None, 'validation_authorized': False,
                    'test_authorized': False, 'reason': 'Investigate cold baseline before any sensor/held-out evaluation'}
    if missing:
        return {'status': 'pending_development', 'missing_reviews': missing, 'candidate': None,
                'validation_authorized': False, 'test_authorized': False}
    acquisition = []
    for name, arm in (('adaptive', 'candidate'), ('sparse', 'sparse')):
        if reviews[name]['summary']['met']:
            payload = reviews[name]['summary']['by_arm'][arm]['payload_rate_mean_B_s']
            if not isinstance(payload, (int, float)) or not isfinite(payload) or payload <= 0:
                raise ValueError('Invalid payload metric for candidate selection')
            acquisition.append((payload, 0 if name == 'sparse' else 1, name))
    chosen = min(acquisition)[2] if acquisition else 'retention' if reviews['retention']['summary']['met'] else None
    return {'status': 'register_fresh_evaluation' if chosen else 'development_not_met', 'candidate': chosen,
            'candidate_source': reviews[chosen]['source_commit'] if chosen else None,
            'validation_authorized': False, 'test_authorized': False,
            'reason': 'Freeze a new protocol/source/dataset under plan 0022 before dispatch' if chosen else
                      'No candidate passed every registered development gate; retain negative evidence'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    reviews = {}; hashes = {}
    for key, name in NAMES.items():
        path = ROOT/'docs/research'/name
        if path.exists():
            reviews[key] = json.loads(path.read_text())
            hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    result = pick_candidate(reviews) | {'source_reviews_sha256': hashes}
    if args.output:
        with args.output.open('x') as stream:
            stream.write(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
