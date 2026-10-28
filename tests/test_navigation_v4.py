"""Behavioral geometry, measured-only routing and version boundaries for v4."""
import ast
from copy import deepcopy
from dataclasses import asdict, replace
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'versions/navigation_v4')]
from blind_drone.contracts.runtime import VehicleState
from blind_drone.experiments.protocol_v2 import load_v2_config
from blind_drone.experiments.runtime_v3 import inventory as old_inventory
from blind_drone.navigation.cadence import AcquisitionGrid
from blind_drone.navigation.observed import MissionV2
from blind_drone.sensors.acquisition import RANGE_NAMES, SampledObservation
from blind_drone_v4.navigation import FreeRoute, ObservedDetourNavigator, observed_segment, segment_cells, swept_clearance
from blind_drone_v4.protocol import select_cases
from blind_drone_v4.audit import REGRESSIONS,command_audit,segment_rectangle_distance,summarize


def grid():
    config = load_v2_config()
    result = AcquisitionGrid(config['navigation_v2'], config['vehicle']['body_size_m'], .33)
    result.origin = (0., 0.)
    return result


def observation(time=0.):
    pose = VehicleState(time, (.125,.025,1.5), (0.,0.,0.), (0.,0.,0.), (0.,0.,0.))
    sample = {'sample_time_s':time, 'frame':'body_FLU', 'acquisition_state':pose,
              'readings':{n:{'distance_m':8.,'valid':True,'at_limit':True} for n in RANGE_NAMES}}
    return SampledObservation.construct(pose, sample)


class SweptSegmentTests(unittest.TestCase):
    def test_supercover_includes_diagonal_side_cells_and_negative_boundary(self):
        self.assertEqual(segment_cells((.125,.125),(.375,.375),.25), {(0,0),(0,1),(1,0),(1,1)})
        self.assertEqual(segment_cells((0.,.125),(0.,.375),.25), {(-1,0),(-1,1),(0,0),(0,1)})

    def test_stationary_known_endpoint_does_not_invent_free_neighbours(self):
        self.assertEqual(segment_cells((0.,0.),(0.,0.),.25),{(0,0)})
        g=grid();g.free={(0,0)}
        self.assertTrue(observed_segment(g,(0.,0.),(0.,0.)))
        self.assertEqual(g.free,{(0,0)})

    def test_thin_unknown_crossing_missed_by_sampled_predicate_is_rejected(self):
        g=grid();start,end=(.249,.05),(.251,.451)
        cells=segment_cells(start,end,.25)
        g.free=cells-{(0,1)}
        self.assertTrue(g.segment_ok(start,end,True))
        self.assertFalse(observed_segment(g,start,end))

    def test_unknown_and_blocked_are_rejected_without_mutating_grid(self):
        g=grid();g.free={(0,0),(1,0)}
        before=deepcopy(g.__dict__)
        self.assertTrue(observed_segment(g,(.125,.125),(.375,.125)))
        self.assertFalse(observed_segment(g,(.125,.125),(.625,.125)))
        self.assertEqual(g.__dict__,before)
        g.blocked.add((1,0))
        self.assertFalse(observed_segment(g,(.125,.125),(.375,.125)))

    def test_swept_clearance_uses_segment_interior_not_only_endpoint(self):
        g=grid();g.occupied={(2,2)}
        self.assertAlmostEqual(swept_clearance(g,(.125,.125),(1.125,.125)),.5)
        g.free={(x,0) for x in range(5)}
        self.assertFalse(observed_segment(g,(.125,.125),(1.125,.125)))

    def test_recovery_cannot_bypass_unknown_or_measured_hull_clearance(self):
        g=grid();g.free={(0,0),(1,0)};g.blocked={(0,0)}
        self.assertTrue(observed_segment(g,(.125,.125),(.375,.125),True))
        self.assertFalse(observed_segment(g,(.125,.125),(.625,.125),True))
        g.occupied={(0,1)}
        self.assertFalse(observed_segment(g,(.125,.125),(.375,.125),True))


class FreeRouteTests(unittest.TestCase):
    def test_route_goes_around_unknown_without_relabeling_it(self):
        g=grid();g.free={(x,y) for x in range(-2,7) for y in range(-2,3)}-{(0,-1)}
        start,goal=(.125,.025),(.125,-.375)
        before=deepcopy(g.free)
        planner=FreeRoute(g);route=planner.plan(start,goal)
        self.assertTrue(planner.reached_goal)
        self.assertGreater(len(route),2)
        self.assertTrue(all(observed_segment(g,a,b) for a,b in zip(route,route[1:])))
        self.assertEqual(g.free,before)
        self.assertNotIn((0,-1),g.free)

    def test_disconnected_known_goal_does_not_cross_unknown_bridge(self):
        g=grid();g.free={(0,0),(2,0)}
        self.assertEqual(FreeRoute(g).plan((.125,.125),(.625,.125)),[])

    def test_no_diagonal_corner_cut(self):
        g=grid();g.free={(0,0),(1,1),(2,2)}
        self.assertEqual(FreeRoute(g).plan((.125,.125),(.625,.625)),[])

    def test_boundary_pose_can_depart_into_known_side_without_filling_unknown_side(self):
        g=grid();g.free={(x,0) for x in range(8)}
        before=deepcopy(g.free)
        route=FreeRoute(g).plan((.01,0.),(1.5,.125))
        self.assertTrue(route)
        self.assertTrue(all(observed_segment(g,a,b) for a,b in zip(route,route[1:])))
        self.assertEqual(g.free,before)
        self.assertNotIn((0,-1),g.free)

    def test_start_or_end_floor_cell_remains_required(self):
        g=grid();g.free={(1,0),(2,0)}
        self.assertFalse(observed_segment(g,(.25,.125),(.125,.125)))
        self.assertEqual(FreeRoute(g).plan((.125,.125),(.625,.125)),[])

    def test_bounded_search(self):
        g=grid();g.params=deepcopy(g.params);g.params['max_expansions']=3
        g.free={(x,y) for x in range(12) for y in range(12)}
        planner=FreeRoute(g);planner.plan((.125,.125),(5.,5.))
        self.assertLessEqual(planner.expansions,3)

    def test_new_free_evidence_can_open_route_without_cache_poisoning(self):
        g=grid();g.free={(0,0),(2,0)};planner=FreeRoute(g)
        self.assertFalse(planner.plan((.125,.125),(.625,.125)))
        g.free.add((1,0))
        self.assertTrue(planner.plan((.125,.125),(.625,.125)))


class NavigatorBoundaryTests(unittest.TestCase):
    def test_stale_or_invalid_never_changes_map_or_moves(self):
        nav=ObservedDetourNavigator(MissionV2((5.,0.,1.5),'mapped'),load_v2_config())
        obs=observation()
        for bad in (replace(obs,state=replace(obs.state,time_s=.5)),replace(obs,ranges=())):
            command=nav.step(bad)
            self.assertEqual((command.forward_m_s,command.left_m_s),(0.,0.))
            self.assertEqual(nav.grid.updates,0)
            self.assertEqual(nav.status,'invalid_or_stale_observation')

    def test_no_route_search_is_cached_until_replan_period(self):
        nav=ObservedDetourNavigator(MissionV2((5.,0.,1.5),'mapped'),load_v2_config())
        obs=observation();nav.started=-3.;nav.grid.origin=(.125,.025)
        nav.grid.update=lambda observation:None
        nav.grid.free={(0,0)}
        nav.grid.plan=lambda start,goal:[]
        nav.step(obs);nav.step(replace(obs,state=replace(obs.state,time_s=.016)))
        self.assertEqual(nav.detour_plans,1)
        self.assertEqual(nav.status,'scan_no_observed_route')

    def test_candidate_target_and_command_are_observed(self):
        nav=ObservedDetourNavigator(MissionV2((.125,-2.,1.5),'mapped'),load_v2_config())
        obs=observation();nav.started=-3.
        nav.grid.update=lambda observation:None;nav.grid.origin=(0.,0.)
        nav.grid.free={(x,y) for x in range(-4,5) for y in range(-10,5)}-{(0,-1)}
        command=nav.step(obs)
        self.assertEqual(nav.status,'follow_observed_detour')
        self.assertGreater(abs(command.forward_m_s)+abs(command.left_m_s),0.)
        self.assertTrue(observed_segment(nav.grid,obs.state.position_m,nav.selected_target))

    def test_v4_policy_imports_no_privileged_modules(self):
        tree=ast.parse((ROOT/'versions/navigation_v4/blind_drone_v4/navigation.py').read_text())
        imports=[node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
        self.assertFalse(any(any(part in name for part in ('world','evaluation','adapter','protocol')) for name in imports))

    def test_old_inventory_does_not_include_v4(self):
        self.assertFalse(any('navigation_v4' in name or 'observed_v4' in name or 'drone_v4' in name for name in old_inventory()))

    def test_heldout_rejected_before_fixture_read(self):
        for split in ('validation','test'):
            with self.assertRaisesRegex(ValueError,'development only'):select_cases(split)


class IndependentAuditTests(unittest.TestCase):
    def summary_fixture(self):
        cases=[{'id':name,'feasible':True,'family':'regression'} for name in sorted(REGRESSIONS)]
        cases.append({'id':'negative','feasible':False,'family':'blocked_goal'})
        episodes=[];audits=[]
        for case in cases:
            for repeat in (0,1):
                audits.append([{'arm':'candidate','repeat':repeat,'minimum_scored_polyline_surface_clearance_m':1.,
                                'observed_target_and_command_checks_passed':True,'decisions_checked':100,'detour_decisions':1}])
                for arm in ('reference','candidate'):
                    episodes.append({'case_id':case['id'],'arm':arm,'repeat':repeat,
                                     'outcome':'success' if case['feasible'] else 'timeout',
                                     'elapsed_s':10. if case['feasible'] else 90.,'path_length_m':3.,
                                     'cpu':{'mean_ms':1.,'max_ms':2.,'p95_ms':1.5,'over_16_ms':0,'decisions':100},
                                     'resources':{'rss_peak_mib':20.,'peak_cells':100,'peak_expansions':50}})
        return episodes,cases,audits

    def test_failed_repeat_is_not_hidden_by_other_success(self):
        episodes,cases,audits=self.summary_fixture()
        row=next(e for e in episodes if e['arm']=='candidate' and e['case_id']==cases[0]['id'])
        row['outcome']='collision'
        result=summarize(episodes,cases,audits)
        self.assertEqual(result['by_arm']['candidate']['feasible_case_success'],4)
        self.assertEqual(len(result['by_arm']['candidate']['failure_episodes']),1)
        self.assertFalse(result['engineering_targets_met'])
        self.assertEqual(result['paired_case_metrics']['adverse_cases'],1)

    def test_duplicate_and_missing_episodes_block_summary(self):
        episodes,cases,audits=self.summary_fixture()
        for wrong in (episodes[:-1],episodes+[episodes[0]]):
            with self.assertRaisesRegex(ValueError,'Incomplete/duplicate'):summarize(wrong,cases,audits)

    def test_common_success_and_penalty_include_different_denominators(self):
        episodes,cases,audits=self.summary_fixture()
        for row in episodes:
            if row['arm']=='reference' and row['case_id']==cases[0]['id']:
                row['outcome']='timeout';row['elapsed_s']=90.
        result=summarize(episodes,cases,audits)
        metrics=result['paired_case_metrics']
        self.assertEqual(metrics['improved_cases'],1)
        self.assertEqual(metrics['common_success_cases'],4)
        self.assertEqual(metrics['common_success_time_ratio'],1.)
        self.assertLess(metrics['penalized_time_ratio'],1.)

    def test_rectangle_clearance_checks_entire_segment(self):
        rectangle=(0.,1.,0.,1.)
        self.assertEqual(segment_rectangle_distance((-1.,.5),(2.,.5),rectangle),0.)
        self.assertAlmostEqual(segment_rectangle_distance((-1.,1.5),(2.,1.5),rectangle),.5)
        self.assertAlmostEqual(segment_rectangle_distance((2.,2.),(3.,3.),rectangle),2**.5)

    def test_recorded_unknown_target_is_rejected_independently(self):
        obs=observation()
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            item={'time_s':0.,'pose':asdict(obs.acquisition_state),
                  'readings':{r.name:{'distance_m':r.distance_m,'valid':r.valid,'at_limit':r.at_limit} for r in obs.ranges}}
            (folder/'candidate0-acquisition.jsonl').write_text(json.dumps(item)+'\n')
            decision={'time_s':.016,'pose_time_s':0.,'sample_time_s':0.,'target_m':[.125,-.125],
                      'recovery':False,'status':'follow_observed_detour',
                      'command':{'forward_m_s':0.,'left_m_s':0.,'up_m_s':0.,'yaw_rate_rad_s':.35}}
            path=folder/'candidate0-decisions.jsonl';path.write_text(json.dumps(decision)+'\n')
            with self.assertRaisesRegex(ValueError,'selected target'):command_audit(folder,{'repeat':0})
            decision['target_m']=None
            path.write_text(json.dumps(decision)+'\n')
            self.assertEqual(command_audit(folder,{'repeat':0})['decisions_checked'],1)


if __name__=='__main__':
    unittest.main()
