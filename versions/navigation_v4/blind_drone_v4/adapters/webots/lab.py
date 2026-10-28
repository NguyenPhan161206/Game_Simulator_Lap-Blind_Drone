"""V4 development supervisor derived from v3 at 0c75ce2.

Ground truth is for world/evaluation only, never navigation.
"""
import json
from math import dist, pi, sqrt
import os
from pathlib import Path
import traceback

from blind_drone.evaluation.cadence import CadenceEvaluator, pair_order
from blind_drone.experiments.protocol_v2 import load_v2_config
from blind_drone_v4.protocol import load_spec, select_cases


def main():
    from controller import Supervisor
    supervisor=Supervisor()
    output=Path(os.environ['BLIND_DRONE_OUTPUT'])
    spec=load_spec(); lab=load_v2_config()
    split=os.environ['BLIND_DRONE_SPLIT'];case_id=os.environ['BLIND_DRONE_CASE']
    repeat=int(os.environ['BLIND_DRONE_REPEAT'])
    cases,design=select_cases(split,[case_id]);case=cases[0]
    emitter=supervisor.getDevice('operator');receiver=supervisor.getDevice('telemetry');receiver.enable(16)
    drone=supervisor.getFromDef('DRONE')
    blocks=[supervisor.getFromDef(x['id']) for x in lab['world']['obstacles']]
    report={'status':'running','split':split,'case_id':case_id,'repeat':repeat,'development_sha256':design,'schema_version':4,'episodes':[]}
    (output/'case.json').write_text(json.dumps(case,indent=2)+'\n')
    latest=accounting=controller_error=None
    trace=(output/'evaluation.jsonl').open('w')
    def send(packet):emitter.send(json.dumps(packet).encode())
    def step():
        nonlocal latest,accounting,controller_error
        if supervisor.step(16)==-1:raise RuntimeError('Simulator stopped before pair completed')
        while receiver.getQueueLength():
            packet=json.loads(receiver.getString());receiver.nextPacket()
            if packet['kind']=='telemetry':latest=packet
            elif packet['kind']=='accounting':accounting=packet
            elif packet['kind']=='controller_error':controller_error=packet
            else:raise ValueError('Unexpected operator/reset packet')
        return supervisor.getTime()
    try:
        if len(case['obstacles'])>len(blocks):raise ValueError('Insufficient primitive slots')
        for i,node in enumerate(blocks):
            item=case['obstacles'][i] if i<len(case['obstacles']) else {'center_m':[30+i,30,1.5],'size_m':[.5,.5,3.]}
            node.getField('translation').setSFVec3f(item['center_m'])
            node.getField('boundingObject').getSFNode().getField('size').setSFVec3f(item['size_m'])
            node.getField('children').getMFNode(0).getField('geometry').getSFNode().getField('size').setSFVec3f(item['size_m'])
        supervisor.getFromDef('GOAL').getField('translation').setSFVec3f(case['goal_m'])
        # Start Robot/controller processes before the first reset (no device fallback).
        step();step()
        for arm in pair_order(case_id,repeat):
            token=arm+str(repeat)
            period=spec[arm+'_period_ms']
            drone.getField('translation').setSFVec3f(case['start_m'])
            drone.getField('rotation').setSFRotation([0,0,1,case['start_yaw_rad']])
            drone.resetPhysics()
            latest=accounting=controller_error=None
            send({'kind':'reset','period_ms':period,'token':token})
            warmup=supervisor.getTime()
            while supervisor.getTime()-warmup<spec['warmup_s']-1e-8:
                step()
                if controller_error:raise RuntimeError('Controller algorithm exception: '+controller_error['error'])
                if drone.getContactPoints(True):raise RuntimeError('Warmup collision; algorithm/reset failure, not infrastructure')
            if latest is None or latest['token']!=token:raise RuntimeError('No matching controller telemetry')
            if any('camera' in n.lower() for n in latest['devices']):raise ValueError('Image device forbidden')
            initial=list(drone.getPosition());velocity=list(drone.getVelocity()[:3]);initial_velocity=velocity[:]
            yaw=latest['attitude_rad'][2]
            if dist(initial,case['start_m'])>.18 or sqrt(sum(v*v for v in velocity))>.18 or abs((yaw-case['start_yaw_rad']+pi)%(2*pi)-pi)>.1:
                raise RuntimeError('Reset pose did not settle')
            send({'kind':'mission','goal_m':case['goal_m'],'policy':'mapped'})
            start=supervisor.getTime()
            evaluator=CadenceEvaluator(case['goal_m'],spec['quality'])
            evaluator.update(0,initial,velocity,0)
            while True:
                now=step();position=list(drone.getPosition());velocity=list(drone.getVelocity()[:3])
                contacts=len(drone.getContactPoints(True))
                result=evaluator.update(now-start,position,velocity,contacts)
                # Tick trace is authoritative for scoring, never downsampled.
                trace.write(json.dumps({'arm':arm,'time_s':now-start,'position_m':position,'velocity_m_s':velocity,
                                        'contact_count':contacts})+'\n')
                if controller_error:
                    result={'outcome':'algorithm_failure','elapsed_s':round(now-start,9),'path_length_m':evaluator.path_length_m,
                            'contact_count':contacts,'error':controller_error['error']}
                if result:break
            send({'kind':'finish','score_start_s':start,'end_s':now})
            for _ in range(20):
                step()
                if accounting:break
            if accounting is None:
                # Preserve algorithm failure evidence and block incomplete accounting.
                raise RuntimeError('Missing accounting; pair unresolved; no automatic algorithm retry')
            if accounting['token']!=token:raise ValueError('Wrong accounting token')
            if set(accounting['device_periods_ms'].values())!={period} or set(accounting['pose_periods_ms'].values())!={32}:
                raise ValueError('Effective device period mismatch')
            row={'case_id':case_id,'family':case['family'],'feasible':case['feasible'],'seed':case['seed'],
                 'geometry_sha256':case['geometry_sha256'],'arm':arm,'repeat':repeat,'period_ms':period,
                 'initial_position_m':initial,'initial_velocity_m_s':initial_velocity,'initial_yaw_rad':yaw,'final_position_m':position,
                 'score_start_s':start,'score_end_s':now,**result,
                 **{k:v for k,v in accounting.items() if k not in ('kind','token')}}
            report['episodes'].append(row)
            (output/'progress.json').write_text(json.dumps(report,indent=2)+'\n')
            print('V4_EPISODE',case_id,arm,repeat,result['outcome'],result['elapsed_s'],flush=True)
            if controller_error:break
        report['status']='complete' if len(report['episodes'])==2 else 'incomplete'
    except Exception as error:
        traceback.print_exc();report['status']='incomplete';report['error']=str(error)
    finally:
        trace.close()
        (output/'result.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        supervisor.simulationQuit(0 if report['status']=='complete' else 1)
