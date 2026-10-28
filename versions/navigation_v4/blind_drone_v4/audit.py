"""Offline public-command and privileged outcome/clearance review, never policy."""
from collections import Counter
import json
from math import cos, hypot, sin, sqrt
from pathlib import Path

from blind_drone.contracts.runtime import VehicleState
from blind_drone.evaluation.cadence_audit import audit_pair
from blind_drone.experiments.protocol_v2 import load_v2_config
from blind_drone.navigation.cadence import AcquisitionGrid
from blind_drone.sensors.acquisition import SampledObservation
from blind_drone.world.geometry import segment_clear
from blind_drone_v4.navigation import observed_segment

REGRESSIONS = {'development-empty-s3200020','development-empty-s3200034','development-empty-s3200041',
               'development-narrow_gap-s3200004','development-narrow_gap-s3200029'}


def command_audit(folder, row):
    """Rebuild the observed grid from logged 32 ms public measurements only."""
    config=load_v2_config()
    grid=AcquisitionGrid(config['navigation_v2'],config['vehicle']['body_size_m'],config['sensors']['horizontal_origin_radius_m'])
    prefix='candidate'+str(row['repeat'])
    samples={}
    for line in (folder/(prefix+'-acquisition.jsonl')).read_text().splitlines():
        item=json.loads(line)
        pose=VehicleState(**{k:tuple(v) if isinstance(v,list) else v for k,v in item['pose'].items()})
        samples[item['time_s']]={'sample_time_s':item['time_s'],'frame':'body_FLU',
                                'readings':item['readings'],'acquisition_state':pose}
    from dataclasses import replace
    checked=moving=detours=0
    for line in (folder/(prefix+'-decisions.jsonl')).read_text().splitlines():
        d=json.loads(line)
        pose=replace(samples[d['pose_time_s']]['acquisition_state'],time_s=d['time_s'])
        obs=SampledObservation.construct(pose,samples[d['sample_time_s']])
        command=d['command']
        if not obs.usable(config['navigation']['range_max_age_s'],config['sensors']['range_max_m']):
            if hypot(command['forward_m_s'],command['left_m_s'])>1e-9:
                raise ValueError('Movement on invalid observation')
            continue
        grid.update(obs)
        if d['target_m'] is not None and not observed_segment(grid,pose.position_m,d['target_m'],d['recovery']):
            raise ValueError('Unobserved/insufficient-clearance selected target')
        forward,left=command['forward_m_s'],command['left_m_s'];yaw=pose.attitude_rad[2]
        vx,vy=cos(yaw)*forward-sin(yaw)*left,sin(yaw)*forward+cos(yaw)*left
        if hypot(vx,vy)>.4+1e-8:
            raise ValueError('V4 horizontal speed exceeds fixed comparison')
        if hypot(vx,vy)>1e-9:
            moving+=1
            if d['target_m'] is None or not observed_segment(grid,pose.position_m,
                    (pose.position_m[0]+vx*.016,pose.position_m[1]+vy*.016),d['recovery']):
                raise ValueError('Unobserved/insufficient-clearance final command')
        detours+=d['status'].startswith('follow_observed_detour')
        checked+=1
    return {'decisions_checked':checked,'nonzero_horizontal_commands':moving,'detour_decisions':detours,
            'observed_target_and_command_checks_passed':True}


def segment_rectangle_distance(start,end,rectangle):
    if not segment_clear(start,end,[rectangle]):
        return 0.
    xmin,xmax,ymin,ymax=rectangle
    def point_distance(p):
        return hypot(max(xmin-p[0],0.,p[0]-xmax),max(ymin-p[1],0.,p[1]-ymax))
    dx,dy=end[0]-start[0],end[1]-start[1];length2=dx*dx+dy*dy
    values=[point_distance(start),point_distance(end)]
    for x,y in ((xmin,ymin),(xmin,ymax),(xmax,ymin),(xmax,ymax)):
        t=max(0.,min(1.,((x-start[0])*dx+(y-start[1])*dy)/length2)) if length2 else 0.
        values.append(hypot(x-start[0]-t*dx,y-start[1]-t*dy))
    return min(values)


def actual_clearance(folder,case,row):
    """Ground-truth metric on scored 16 ms polyline; never sent to controller."""
    rectangles=[(o['center_m'][0]-o['size_m'][0]/2,o['center_m'][0]+o['size_m'][0]/2,
                 o['center_m'][1]-o['size_m'][1]/2,o['center_m'][1]+o['size_m'][1]/2) for o in case['obstacles']]
    points=[row['initial_position_m']]
    points += [t['position_m'] for t in map(json.loads,(folder/'evaluation.jsonl').read_text().splitlines()) if t['arm']==row['arm']]
    minimum=min(9.9-max(abs(p[0]),abs(p[1])) for p in points)
    for start,end in zip(points,points[1:]):
        for rectangle in rectangles:
            minimum=min(minimum,segment_rectangle_distance(start,end,rectangle))
    return minimum


def audit_v4_pair(folder,case,spec,result):
    folder=Path(folder)
    audit_pair(folder,case,spec,result)
    output=[]
    for row in result['episodes']:
        expected='observed_detour_v4' if row['arm']=='candidate' else 'frozen_v3_mapped'
        if row['policy_version']!=expected or row['period_ms']!=32:
            raise ValueError('Wrong policy/cadence comparison')
        evidence={'arm':row['arm'],'repeat':row['repeat'],
                  'minimum_scored_polyline_surface_clearance_m':actual_clearance(folder,case,row)}
        if row['arm']=='candidate':
            evidence.update(command_audit(folder,row))
        output.append(evidence)
    return output


def summarize(episodes,cases,pair_audits):
    expected={(c['id'],a,r) for c in cases for a in ('reference','candidate') for r in (0,1)}
    keys=[(e['case_id'],e['arm'],e['repeat']) for e in episodes]
    if len(keys)!=len(set(keys)) or set(keys)!=expected:
        raise ValueError('Incomplete/duplicate development pairs')
    if any(e['outcome'] not in {'success','timeout','collision','out_of_bounds','algorithm_failure'} for e in episodes):
        raise ValueError('Unknown algorithm outcome')
    feasible={c['id'] for c in cases if c['feasible']}
    negative={c['id'] for c in cases if not c['feasible']}
    by_arm={}
    for arm in ('reference','candidate'):
        rows=[e for e in episodes if e['arm']==arm]
        success={case_id:all(e['outcome']=='success' for e in rows if e['case_id']==case_id) for case_id in feasible}
        failures=[{'case_id':e['case_id'],'repeat':e['repeat'],'outcome':e['outcome']} for e in rows if e['case_id'] in feasible and e['outcome']!='success']
        by_arm[arm]={'feasible_case_success':sum(success.values()),'feasible_cases':len(feasible),
                     'outcomes':dict(Counter(e['outcome'] for e in rows)),
                     'negative_false_success':sum(e['case_id'] in negative and e['outcome']=='success' for e in rows),
                     'failure_episodes':failures,
                     'deadlock_regressions':{case_id:success[case_id] for case_id in sorted(REGRESSIONS & feasible)},
                     'cpu_mean_ms_weighted':sum(e['cpu']['mean_ms']*e['cpu']['decisions'] for e in rows)/sum(e['cpu']['decisions'] for e in rows),
                     'cpu_max_ms':max(e['cpu']['max_ms'] for e in rows),
                     'max_episode_p95_cpu_ms':max(e['cpu']['p95_ms'] for e in rows),
                     'cpu_over_16_ms':sum(e['cpu']['over_16_ms'] for e in rows),
                     'rss_peak_mib':max(e['resources']['rss_peak_mib'] for e in rows),
                     'peak_cells':max(e['resources']['peak_cells'] for e in rows),
                     'peak_expansions':max(e['resources']['peak_expansions'] for e in rows),
                     'success_only_mean_time_s':sum(e['elapsed_s'] for e in rows if e['outcome']=='success')/max(1,sum(e['outcome']=='success' for e in rows)),
                     'success_only_mean_path_m':sum(e['path_length_m'] for e in rows if e['outcome']=='success')/max(1,sum(e['outcome']=='success' for e in rows)),
                     'case_success_by_family':{family:{'success':sum(success[c['id']] for c in cases if c['feasible'] and c['family']==family),
                                                       'cases':sum(c['feasible'] and c['family']==family for c in cases)}
                                               for family in sorted({c['family'] for c in cases if c['feasible']})}}
    candidate_audits=[a for group in pair_audits for a in group if a['arm']=='candidate']
    minimum=min(a['minimum_scored_polyline_surface_clearance_m'] for a in candidate_audits)
    config=load_v2_config()
    required=sqrt(sum(v*v for v in config['vehicle']['body_size_m']))/2+config['navigation_v2']['margin_m']
    gates={'five_deadlock_regressions_succeed_both_repeats':set(REGRESSIONS)<=feasible and all(by_arm['candidate']['deadlock_regressions'].values()),
           'candidate_collision_zero':by_arm['candidate']['outcomes'].get('collision',0)==0,
           'candidate_bounds_zero':by_arm['candidate']['outcomes'].get('out_of_bounds',0)==0,
           'candidate_negative_false_success_zero':by_arm['candidate']['negative_false_success']==0,
           'candidate_command_checks_passed':all(a['observed_target_and_command_checks_passed'] for a in candidate_audits),
           'candidate_scored_polyline_clearance_target':minimum>=required}
    collapsed={}
    for case_id in feasible:
        collapsed[case_id]={}
        for arm in ('reference','candidate'):
            rows=[e for e in episodes if e['case_id']==case_id and e['arm']==arm]
            collapsed[case_id][arm]={'success':all(e['outcome']=='success' for e in rows),
                                    'time_s':max(e['elapsed_s'] for e in rows),
                                    'path_m':max(e['path_length_m'] for e in rows)}
    common=[value for value in collapsed.values() if all(value[a]['success'] for a in ('reference','candidate'))]
    def paired_ratio(field,penalty,common_only=False):
        totals={}
        for arm in ('reference','candidate'):
            totals[arm]=sum(value[arm][field] if common_only or value[arm]['success'] else
                            penalty for value in (common if common_only else collapsed.values()))
        return totals['candidate']/totals['reference'] if totals['reference'] else None
    # Fixed report penalties inherited from the physical speed cap and deadline.
    time_ratio=paired_ratio('time_s',90.);common_time=paired_ratio('time_s',90.,True)
    path_ratio=paired_ratio('path_m',72.);common_path=paired_ratio('path_m',72.,True)
    return {'scope':'exposed development; no held-out inference','by_arm':by_arm,'engineering_gates':gates,
            'engineering_targets_met':all(gates.values()),'candidate_minimum_scored_polyline_clearance_m':minimum,
            'scored_polyline_clearance_target_m':required,
            'candidate_commands_checked':sum(a['decisions_checked'] for a in candidate_audits),
            'candidate_detour_decisions':sum(a['detour_decisions'] for a in candidate_audits),
            'paired_case_metrics':{'common_success_cases':len(common),'common_success_time_ratio':common_time,
                                   'common_success_path_ratio':common_path,'penalized_time_ratio':time_ratio,
                                   'penalized_path_ratio':path_ratio,'failure_time_penalty_s':90.,'failure_path_penalty_m':72.,
                                   'adverse_cases':sum(v['reference']['success'] and not v['candidate']['success'] for v in collapsed.values()),
                                   'improved_cases':sum(not v['reference']['success'] and v['candidate']['success'] for v in collapsed.values())}}
