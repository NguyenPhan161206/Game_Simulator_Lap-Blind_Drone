"""Independent replay of raw v3 acquisition/binary/decision/physics evidence."""
import json
from pathlib import Path

from blind_drone.contracts.runtime import VehicleState
from blind_drone.evaluation.cadence import CadenceEvaluator, pair_order
from blind_drone.evaluation.cadence import aggregate
from blind_drone.sensors.acquisition import acquisition_summary, cpu_summary, encode_packet


def audit_pair(directory, case, spec, result):
    directory=Path(directory)
    if result.get('status')!='complete' or len(result['episodes'])!=2:
        raise ValueError('Incomplete pair')
    if [e['arm'] for e in result['episodes']]!=list(pair_order(case['id'],result['repeat'])):
        raise ValueError('Pair order mismatch')
    trace=[json.loads(line) for line in (directory/'evaluation.jsonl').read_text().splitlines()]
    for row in result['episodes']:
        arm=row['arm'];period=spec[arm+'_period_ms'];token=arm+str(row['repeat'])
        if row['case_id']!=case['id'] or row['geometry_sha256']!=case['geometry_sha256']:
            raise ValueError('Wrong case provenance')
        if set(row['device_periods_ms'].values())!={period} or set(row['pose_periods_ms'].values())!={32}:
            raise ValueError('Device cadence differs from protocol')
        samples=[json.loads(line) for line in (directory/(token+'-acquisition.jsonl')).read_text().splitlines()]
        binary=(directory/(token+'-range.bin')).read_bytes()
        if len(binary)!=96*len(samples):raise ValueError('Binary acquisition count mismatch')
        for i,s in enumerate(samples):
            pose=VehicleState(**{k:tuple(v) if isinstance(v,list) else v for k,v in s['pose'].items()})
            packet={'sample_time_s':s['time_s'],'readings':s['readings'],'acquisition_state':pose}
            if pose.time_s!=s['time_s'] or encode_packet(s['sequence'],packet)!=binary[i*96:(i+1)*96]:
                raise ValueError('Acquisition pose/binary mismatch')
        kept=[s for s in samples if s['time_s']<=row['end_s']+1e-8]
        summary=acquisition_summary(kept,row['epoch_s'],row['end_s'],period,row['score_start_s'])
        if summary!=row['acquisition'] or not summary['schedule_complete']:
            raise ValueError('Acquisition accounting mismatch')
        decisions=[json.loads(line) for line in (directory/(token+'-decisions.jsonl')).read_text().splitlines()]
        decisions=[d for d in decisions if row['score_start_s']+1e-8<d['time_s']<=row['end_s']+1e-8]
        if cpu_summary([d['cpu_ms'] for d in decisions])!=row['cpu']:
            raise ValueError('CPU accounting mismatch')
        if cpu_summary([d['wall_ms'] for d in decisions])!=row['decision_wall']:
            raise ValueError('Wall decision accounting mismatch')
        for i,d in enumerate(decisions):
            if i and abs(d['time_s']-decisions[i-1]['time_s']-.016)>1e-8:
                raise ValueError('Missing control decision')
            if not 0<=d['time_s']-d['sample_time_s']<=spec['range_max_age_s']:
                raise ValueError('Stale/future observation used')
            if not 0<=d['time_s']-d['pose_time_s']<.032+1e-8:
                raise ValueError('Current pose sampling mismatch')
            if d['reused'] != (i>0 and d['sample_time_s']==decisions[i-1]['sample_time_s']):
                raise ValueError('Observation reuse mismatch')
        if len(decisions)!=round((row['end_s']-row['score_start_s'])/.016):
            raise ValueError('Incomplete policy read accounting')
        expected_reads={'policy_reads':len(decisions),'reused_reads':sum(d['reused'] for d in decisions),
                        'unique_samples_read':len({d['sample_time_s'] for d in decisions}),
                        'scored_acquisitions':summary['scored']['packets']}
        if row['observation']!=expected_reads:raise ValueError('Observation accounting mismatch')
        evaluator=CadenceEvaluator(case['goal_m'],spec['quality'])
        evaluator.update(0,row['initial_position_m'],row['initial_velocity_m_s'],0)
        ticks=[t for t in trace if t['arm']==arm]
        scored=None
        for i,t in enumerate(ticks,1):
            if abs(t['time_s']-i*.016)>1e-8:raise ValueError('Missing physics evaluation tick')
            scored=evaluator.update(t['time_s'],t['position_m'],t['velocity_m_s'],t['contact_count'])
            if scored and i!=len(ticks):raise ValueError('Scoring continued beyond outcome')
        if not scored or any(row[k]!=v for k,v in scored.items()):
            raise ValueError('Physics tick replay outcome/path mismatch')
        for name,size in row['files_bytes'].items():
            if (directory/name).stat().st_size!=size:raise ValueError('Raw file size mismatch')
    return True


def audit_study(report, cases, spec):
    """Recompute gates and raw pairs; never trust an uploaded `met` flag alone."""
    if report.get('status')!='complete' or not report.get('complete_split'):
        raise ValueError('A complete split is required')
    if aggregate(report['episodes'],cases,spec)!=report.get('gate'):
        raise ValueError('Study gate replay mismatch')
    index={c['id']:c for c in cases}
    valid=[]
    attempts={}
    for attempt in report['attempts']:
        key=(attempt['case_id'],attempt['repeat'])
        attempts.setdefault(key,[]).append(attempt)
        if attempt['classification']=='valid':
            audit_pair(attempt['output'],index[attempt['case_id']],spec,attempt['result'])
            valid.extend(attempt['result']['episodes'])
        elif attempt['classification']!='infrastructure':
            raise ValueError('Unresolved attempt cannot qualify a study')
    for group in attempts.values():
        if len(group)>2 or [a['attempt'] for a in group]!=list(range(len(group))) or group[-1]['classification']!='valid':
            raise ValueError('Invalid retry history')
    if valid!=report['episodes']:raise ValueError('Study episodes do not match raw paired attempts')
    return True
