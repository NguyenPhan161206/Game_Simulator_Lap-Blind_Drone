"""First-stall development snapshot decisions; not counterfactual physics."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'versions/navigation_v4'),str(ROOT/'tools')]
from blind_drone.experiments.protocol_v2 import load_v2_config
from blind_drone.navigation.cadence import CadenceNavigator
from blind_drone.navigation.observed import MissionV2
from blind_drone_v4.navigation import ObservedDetourNavigator,observed_segment
from diagnose_navigation_start import TRACE_SELECTION,read_jsonl,reference_samples,replay_observation
from review_research_v3 import review,sha256_file


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('--expected-source',required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():parser.error('Fresh output required')
    verified=review(args.directory,'development',args.expected_source)
    rows=[]
    for case_id,repeat in TRACE_SELECTION:
        folder=args.directory/f'{case_id}-r{repeat}-a0'
        goal=json.loads((folder/'case.json').read_text())['goal_m']
        mission=MissionV2(tuple(goal),'mapped');config=load_v2_config()
        old=CadenceNavigator(mission,config);new=ObservedDetourNavigator(mission,config)
        samples=reference_samples(read_jsonl(folder/f'reference{repeat}-acquisition.jsonl'),32)
        for decision in read_jsonl(folder/f'reference{repeat}-decisions.jsonl'):
            obs=replay_observation(decision,samples)
            old_command=old.step(obs);new_command=new.step(obs)
            if old.status=='scan_unknown_or_blocked':
                rows.append({'case_id':case_id,'repeat':repeat,'time_s':decision['time_s'],
                             'reference_status':old.status,'reference_command':asdict(old_command),
                             'v4_status':new.status,'v4_command':asdict(new_command),
                             'target_m':new.selected_target,'measured_swept_clearance_m':new.selected_clearance_m,
                             'target_segment_observed':new.selected_target is not None and observed_segment(new.grid,obs.state.position_m,new.selected_target),
                             'detour_points':len(new.detour_path),'search_expansions':new.route_search.expansions,
                             'grid_free_unchanged_from_reference':new.grid.free==old.grid.free,
                             'grid_occupied_unchanged_from_reference':new.grid.occupied==old.grid.occupied})
                break
    value={'kind':'first_stall_snapshot_only','raw_result_sha256':verified['raw_result_sha256'],
           'v4_navigation_sha256':sha256_file(ROOT/'versions/navigation_v4/blind_drone_v4/navigation.py'),
           'traces':rows,'physical_escape_verified':False}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print('V4_SNAPSHOT',len(rows),'traces; no physical escape claim')
    return 0


if __name__=='__main__':raise SystemExit(main())
