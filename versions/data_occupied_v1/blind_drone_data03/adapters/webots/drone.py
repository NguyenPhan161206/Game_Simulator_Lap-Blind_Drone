"""DATA-03 adapter derived from v4; Robot API only.

Both arms acquire at 32 ms; policy version and full command are logged.
"""
from dataclasses import asdict, replace
import json
from math import isfinite
import os
from pathlib import Path
import traceback
from time import process_time_ns

from blind_drone.contracts.runtime import MotionCommand, VehicleState
from blind_drone.control.stabilizer import Stabilizer
from blind_drone.navigation.cadence import CadenceNavigator
from blind_drone_data03.navigation import OccupiedOnlyNavigator
from blind_drone.navigation.observed import MissionV2
from blind_drone.sensors.acquisition import AcquisitionClock, SampledObservation, encode_packet, acquisition_summary, cpu_summary


def rss_mib():
    return int(Path('/proc/self/statm').read_text().split()[1]) * os.sysconf('SC_PAGE_SIZE') / 1024**2


def main():
    from controller import Robot
    robot = Robot()
    config = json.loads(robot.getCustomData())
    step_ms = int(robot.getBasicTimeStep())
    if step_ms != 16: raise ValueError('V4 requires 16 ms physics')
    output = Path(os.environ['BLIND_DRONE_OUTPUT'])
    gps, imu, gyro = [robot.getDevice(n) for n in ('gps','imu','gyro')]
    pose_devices = (gps, imu, gyro)
    ranges = {n:robot.getDevice(n) for n in config['sensor_names']}
    receiver, emitter = [robot.getDevice(n) for n in ('operator','telemetry')]
    receiver.enable(step_ms)
    motors = [robot.getDevice(f'motor_{i}') for i in range(4)]
    for motor in motors: motor.setPosition(float('inf')); motor.setVelocity(0)
    names = [robot.getDeviceByIndex(i).getName() for i in range(robot.getNumberOfDevices())]
    if any('camera' in n.lower() for n in names): raise ValueError('Image device forbidden')
    files = []
    token = None
    navigator = state = sample = None
    clock = pose_clock = None
    records, decisions = [], []
    previous_pose = None
    velocity = (0.,0.,0.)
    stabilizer = Stabilizer(config)
    last_read = None
    def send(packet):
        emitter.send(json.dumps(packet, allow_nan=False, separators=(',',':')).encode())
    try:
        while robot.step(step_ms) != -1:
            now = round(robot.getTime(), 9)
            while receiver.getQueueLength():
                message = json.loads(receiver.getString()); receiver.nextPacket()
                if set(message)=={'kind','period_ms','token'} and message['kind']=='reset':
                    if message['period_ms'] != 32 or message['token'] not in {'reference0','reference1','candidate0','candidate1'}:
                        raise ValueError('Invalid cadence/reset token')
                    for f in files:f.close()
                    token, period = message['token'], message['period_ms']
                    prefix=output/token
                    files=[Path(str(prefix)+suffix).open(mode) for suffix,mode in
                           (('-acquisition.jsonl','w'),('-range.bin','wb'),('-decisions.jsonl','w'))]
                    for d in pose_devices:d.disable();d.enable(32)
                    for d in ranges.values():d.disable();d.enable(period)
                    epoch=now
                    clock,pose_clock=AcquisitionClock(epoch,period),AcquisitionClock(epoch,32)
                    sample=state=previous_pose=navigator=None
                    velocity=(0.,0.,0.)
                    records,decisions=[],[]
                    last_read=None
                    stabilizer.reset()
                elif message.get('kind')=='mission':
                    policy_class = OccupiedOnlyNavigator if token.startswith('candidate') else CadenceNavigator
                    navigator=policy_class(MissionV2.from_packet(message),config)
                elif set(message)=={'kind','score_start_s','end_s'} and message['kind']=='finish':
                    end=message['end_s']; start=message['score_start_s']
                    kept=[r for r in records if r['time_s']<=end+1e-8]
                    scored=[r for r in decisions if start+1e-8<r['time_s']<=end+1e-8]
                    all_scored=[r for r in records if start+1e-8<r['time_s']<=end+1e-8]
                    for f in files:f.flush()
                    diagnostic=navigator.diagnostics() if navigator else {}
                    resources={'rss_peak_mib':max((r['rss_mib'] for r in scored),default=rss_mib()),
                               'peak_cells':diagnostic.get('peak_cells',0),
                               'derived_blocked_cells':diagnostic.get('derived_blocked_cells',0),
                               'peak_persistent_occupied_cells':diagnostic.get('peak_persistent_occupied_cells',0),
                               'peak_ephemeral_free_cells':diagnostic.get('peak_ephemeral_free_cells',0),
                               'peak_blocked_cells':diagnostic.get('peak_blocked_cells',0),
                               'peak_retained_cells':diagnostic.get('peak_retained_cells',0),
                               'peak_map_entries':diagnostic.get('peak_map_entries',0),
                               'peak_expansions':navigator.grid.peak_expansions if navigator else 0,
                               'budget_exhausted':diagnostic.get('budget_exhausted',False)}
                    send({'kind':'accounting','token':token,
                          'acquisition':acquisition_summary(kept,epoch,end,period,start),
                          'cpu':cpu_summary([r['cpu_ms'] for r in scored]),'resources':resources,
                          'decision_wall':cpu_summary([r['wall_ms'] for r in scored]),
                          'observation':{'policy_reads':len(scored),'reused_reads':sum(r['reused'] for r in scored),
                                         'unique_samples_read':len({r['sample_time_s'] for r in scored}),
                                         'scored_acquisitions':len(all_scored)},
                          'diagnostics':diagnostic,'policy_version':'occupied_only_data03' if token.startswith('candidate') else 'frozen_v3_mapped',
                          'device_periods_ms':{n:d.getSamplingPeriod() for n,d in ranges.items()},
                          'pose_periods_ms':{n:d.getSamplingPeriod() for n,d in zip(('gps','imu','gyro'),pose_devices)},
                          'epoch_s':epoch,'end_s':end,'trailing_packets_outside_window':len(records)-len(kept),
                          'files_bytes':{Path(f.name).name:Path(f.name).stat().st_size for f in files},
                          'metadata_bytes':len(json.dumps({'range_order':sorted(ranges),'frame':'body_FLU',
                              'units':'m,s,rad','provenance':'ideal_Webots_generic_single_ray',
                              'sensor_origins':config['sensors']},separators=(',',':')).encode())})
                    navigator=None
                    for f in files:f.close()
                    files=[]; token=None;clock=None
                else:
                    raise ValueError('Unrecognized v4 public control packet')
            if clock is None:continue
            pose_tick=pose_clock.poll(now)
            if pose_tick:
                position=tuple(gps.getValues());attitude=tuple(imu.getRollPitchYaw());rates=tuple(gyro.getValues())
                if not all(isfinite(v) for v in (*position,*attitude,*rates)):
                    raise ValueError('Invalid ideal pose measurement')
                if previous_pose:
                    elapsed=pose_tick[1]-previous_pose.time_s
                    raw=[(a-b)/elapsed for a,b in zip(position,previous_pose.position_m)]
                    velocity=tuple(.35*a+.65*b for a,b in zip(raw,velocity))
                state=VehicleState(pose_tick[1],position,velocity,attitude,rates)
                previous_pose=state
            tick=clock.poll(now)
            if tick:
                if state is None or abs(state.time_s-tick[1])>1e-8:
                    raise ValueError('Acquisition lacks synchronized measured pose')
                readings={}
                for name,d in ranges.items():
                    value=float(d.getValue())
                    valid=isfinite(value) and 0<=value<=config['sensors']['range_max_m']+1e-6
                    readings[name]={'distance_m':value if valid else None,'valid':valid,
                                    'at_limit':valid and value>=config['sensors']['range_max_m']-1e-6}
                sample={'sample_time_s':tick[1],'frame':'body_FLU','readings':readings,'acquisition_state':state}
                payload=encode_packet(tick[0],sample)
                record={'sequence':tick[0],'time_s':tick[1],'pose_time_s':state.time_s,
                        'payload_bytes':len(payload),'invalid_values':sum(not r['valid'] for r in readings.values())}
                records.append(record)
                files[0].write(json.dumps({**record,'pose':asdict(state),'readings':readings},allow_nan=False)+'\n')
                files[1].write(payload)
            if state is None:continue
            current=replace(state,time_s=now)
            command=MotionCommand()
            if navigator:
                before=navigator.cpu_total_ns
                cpu_start=process_time_ns()
                command=navigator.step(SampledObservation.construct(current,sample))
                cpu_ms=(process_time_ns()-cpu_start)/1e6
                decision={'time_s':now,'pose_time_s':state.time_s,'sample_time_s':sample['sample_time_s'] if sample else None,
                          'reused':sample is not None and last_read==sample['sample_time_s'],
                          'cpu_ms':cpu_ms,'wall_ms':(navigator.cpu_total_ns-before)/1e6,'rss_mib':rss_mib(),
                          'command':asdict(command),'status':navigator.status,
                          'target_m':getattr(navigator,'selected_target',None),
                          'recovery':getattr(navigator,'selected_recovery',False)}
                last_read=decision['sample_time_s'];decisions.append(decision)
                files[2].write(json.dumps(decision)+'\n')
            for motor,speed in zip(motors,stabilizer.step(current,command,step_ms/1000)):
                motor.setVelocity(speed)
            send({'kind':'telemetry','token':token,'time_s':now,'pose_time_s':state.time_s,
                  'sample_time_s':sample['sample_time_s'] if sample else None,
                  'position_m':state.position_m,'attitude_rad':state.attitude_rad,'devices':names,
                  'state':navigator.status if navigator else 'warmup'})
    except Exception as error:
        traceback.print_exc()
        (output/'controller-error.json').write_text(json.dumps({'token':token,'classification':'algorithm_failure',
            'error':str(error),'type':type(error).__name__})+'\n')
        send({'kind':'controller_error','token':token,'error':str(error)})
        raise
    finally:
        for f in files:f.close()


if __name__=='__main__':main()
