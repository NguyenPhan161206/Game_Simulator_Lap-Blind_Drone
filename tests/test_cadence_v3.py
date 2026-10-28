"""Behavior checks for the additive v3 runtime; no fake simulator smoke."""
import ast
from copy import deepcopy
from dataclasses import replace
import inspect
import json
from math import pi
from pathlib import Path
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from blind_drone.contracts.runtime import VehicleState
from blind_drone.evaluation.cadence import CadenceEvaluator, aggregate, classify_attempt, pair_order
from blind_drone.experiments.protocol_v2 import load_v2_config
from blind_drone.experiments.protocol_v3 import load_spec, verify_design
from blind_drone.experiments.runtime_v3 import select_cases, verify_runtime
from blind_drone.navigation.cadence import AcquisitionGrid
from blind_drone.observation.range_grid import RangeGrid
from blind_drone.sensors.acquisition import (AcquisitionClock, RANGE_NAMES, SampledObservation,
    encode_packet, acquisition_summary, cpu_summary)


def state(t=0,position=(0.,0.,1.5),yaw=0):
    return VehicleState(t,position,(0.,0.,0.),(0.,0.,yaw),(0.,0.,0.))


def sample(t=0):
    return {'sample_time_s':t,'frame':'body_FLU','acquisition_state':state(t),
            'readings':{n:{'distance_m':8.,'valid':True,'at_limit':True} for n in RANGE_NAMES}}


class AcquisitionTests(unittest.TestCase):
    def test_device_clock_does_not_retimestamp_reuse(self):
        c=AcquisitionClock(1.,64)
        self.assertIsNone(c.poll(1.016));self.assertIsNone(c.poll(1.032))
        self.assertEqual(c.poll(1.064),(1,1.064))
        self.assertIsNone(c.poll(1.080))
        sequence,time=c.poll(1.128)
        self.assertEqual(sequence,2);self.assertAlmostEqual(time,1.128)

    def test_missed_acquisition_cannot_be_fabricated(self):
        with self.assertRaisesRegex(ValueError,'Missed'):AcquisitionClock(0,32).poll(.048)

    def test_decimal_tick_does_not_make_a_fresh_sample_future_dated(self):
        c=AcquisitionClock(.048,64)
        for i in range(1,101):
            now=round(.048+i*.064,9)
            sequence,t=c.poll(now)
            self.assertEqual(t,now)
            self.assertTrue(SampledObservation.construct(state(now),sample(t)).usable(.12,8))

    def test_encoding_includes_invalid_and_metadata(self):
        s=sample();s['readings']['range_000']={'distance_m':None,'valid':False,'at_limit':False}
        self.assertEqual(len(encode_packet(1,s)),96)

    def test_sample_pose_kept_during_translation_rotation(self):
        s=sample(.064)
        current=state(.080,(1.,2.,1.5),pi/2)
        obs=SampledObservation.construct(current,s)
        self.assertTrue(obs.usable(.12,8))
        self.assertEqual(obs.at_acquisition().state,s['acquisition_state'])
        self.assertEqual(obs.state,current)

    def test_wrong_pose_time_future_stale_invalid_stop(self):
        s=sample(.064)
        for bad in (state(.048),state(.200)):
            self.assertFalse(SampledObservation.construct(bad,s).usable(.12,8))
        s['acquisition_state']=state(.032)
        self.assertFalse(SampledObservation.construct(state(.08),s).usable(.12,8))
        s=sample(.064);s['readings']['range_000']['valid']=False
        self.assertFalse(SampledObservation.construct(state(.08),s).usable(.12,8))

    def test_grid_projects_sample_pose_not_current_pose(self):
        c=load_v2_config();args=(c['navigation_v2'],c['vehicle']['body_size_m'],c['sensors']['horizontal_origin_radius_m'])
        expected=RangeGrid(*args);actual=AcquisitionGrid(*args)
        s=sample(.064);s['readings']['range_000']={'distance_m':2.,'valid':True,'at_limit':False}
        obs=SampledObservation.construct(state(.08,(3.,0.,1.5),pi/2),s)
        expected.update(obs.at_acquisition());actual.update(obs)
        self.assertEqual(expected.occupied,actual.occupied)
        self.assertEqual(expected.free,actual.free)
        actual.update(replace(obs,state=state(.096,(4.,0.,1.5),pi)))
        self.assertEqual(actual.updates,1)

    def test_instrumented_planner_matches_frozen_plan(self):
        # Remove counter-only assignments and compare the actual algorithms as AST.
        old=ast.parse(textwrap.dedent(inspect.getsource(RangeGrid.plan)))
        new=ast.parse(textwrap.dedent(inspect.getsource(AcquisitionGrid.plan)))
        class Counters(ast.NodeTransformer):
            def visit_Assign(self,node):
                if any(isinstance(t,ast.Attribute) and t.attr in ('last_expansions','peak_expansions') for t in node.targets):return None
                return node
        self.assertEqual(ast.dump(old,include_attributes=False),ast.dump(Counters().visit(new),include_attributes=False))

    def test_schedule_audits_every_sample_warmup_and_rate(self):
        rows=[{'sequence':i,'time_s':i*.032,'pose_time_s':i*.032,'payload_bytes':96,'invalid_values':0} for i in range(1,101)]
        result=acquisition_summary(rows,0,3.2,32,2.)
        self.assertTrue(result['schedule_complete'])
        self.assertEqual(result['all']['packets'],100)
        self.assertAlmostEqual(result['scored']['payload_bytes_per_s'],3000)
        self.assertEqual(result['warmup']['packets'],62)
        rows.pop(40)
        self.assertFalse(acquisition_summary(rows,0,3.2,32,2.)['schedule_complete'])

    def test_cpu_nearest_rank_and_deadline(self):
        result=cpu_summary(list(range(1,21)))
        self.assertEqual(result['p95_ms'],19)
        self.assertEqual(result['over_16_ms'],4)


class EvaluationTests(unittest.TestCase):
    def setUp(self):self.q=load_spec()['quality']

    def test_tick_path_is_full_3d(self):
        e=CadenceEvaluator((8,8,1.5),self.q)
        e.update(0,(0,0,1.5),(0,0,0),0)
        e.update(.016,(0,0,2.5),(0,0,0),0)
        e.update(.032,(1,0,2.5),(0,0,0),0)
        self.assertEqual(e.path_length_m,2.)

    def test_deadline_dwell_and_priority(self):
        for contact,pos,outcome in ((1,(0,0,1.5),'collision'),(0,(10,0,1.5),'out_of_bounds'),(0,(0,0,1.5),'success')):
            e=CadenceEvaluator((0,0,1.5),self.q)
            e.update(89,(0,0,1.5),(0,0,0),0)
            self.assertEqual(e.update(90,pos,(0,0,0),contact)['outcome'],outcome)
        e=CadenceEvaluator((0,0,1.5),self.q)
        e.update(89.008,(0,0,1.5),(0,0,0),0)
        self.assertEqual(e.update(90.016,(0,0,1.5),(0,0,0),0)['outcome'],'timeout')

    def test_retry_classification_is_conservative(self):
        self.assertEqual(classify_attempt(None,'could not connect to display'),'infrastructure')
        self.assertEqual(classify_attempt(None,'watchdog',True),'unresolved')
        self.assertEqual(classify_attempt({'status':'incomplete'},'MemoryError'),'unresolved')
        self.assertEqual(classify_attempt({'status':'complete'},''),'valid')

    def test_pair_order_is_reversed_and_deterministic(self):
        self.assertEqual(pair_order('case',0),tuple(reversed(pair_order('case',1))))
        self.assertEqual(pair_order('case',0),pair_order('case',0))

    def synthetic(self):
        cases=[{'id':str(i),'family':'empty','feasible':True} for i in range(100)]
        rows=[]
        for c in cases:
            for a in ('reference','candidate'):
                for r in (0,1):
                    rows.append({'case_id':c['id'],'arm':a,'repeat':r,'outcome':'success','elapsed_s':10.,'path_length_m':5.,
                        'cpu':{'p95_ms':1.},'resources':{'peak_cells':100,'peak_expansions':10,'budget_exhausted':False,'rss_peak_mib':50},
                        'acquisition':{'schedule_complete':True,'all':{'invalid_values':0},
                            'scored':{'payload_bytes_per_s':3000. if a=='reference' else 1500.}}})
        return cases,rows

    def test_gate_complete_paired_and_conservative_repeats(self):
        cases,rows=self.synthetic()
        report=aggregate(rows,cases,load_spec())
        self.assertTrue(report['met'])
        self.assertEqual(report['feasible_cases'],100)
        rows[2]['outcome']='timeout'
        report=aggregate(rows,cases,load_spec())
        self.assertEqual(report['adverse_cases'],1)
        self.assertEqual(report['case_successes']['candidate'],99)
        self.assertEqual(report['collapsed']['0']['candidate']['success'],False)

    def test_missing_duplicate_or_short_acquisition_cannot_pass(self):
        cases,rows=self.synthetic()
        for bad in (rows[:-1],rows+[rows[0]]):
            with self.assertRaises(ValueError):aggregate(bad,cases,load_spec())
        rows[2]['acquisition']['scored']['payload_bytes_per_s']=None
        self.assertFalse(aggregate(rows,cases,load_spec())['gates']['range_reduction'])

    def test_negative_collision_and_resource_never_dropped(self):
        cases,rows=self.synthetic();cases[0]['feasible']=False
        rows[0]['outcome']='collision'
        rows[2]['resources']['rss_peak_mib']=513
        result=aggregate(rows,cases,load_spec())
        self.assertFalse(result['gates']['no_collision_bounds'])
        self.assertFalse(result['gates']['negative_never_success'])
        self.assertFalse(result['gates']['resources'])


class IntegrityTests(unittest.TestCase):
    def test_heldout_requires_runtime_lock_before_reading_fixture(self):
        with patch('blind_drone.experiments.runtime_v3.verify_runtime',side_effect=ValueError('lock missing')):
            for split in ('validation','test'):
                with self.assertRaisesRegex(ValueError,'lock missing'):select_cases(split)

    def test_missing_or_tampered_runtime_lock_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'lock.json'
            path.write_text(json.dumps({'schema_version':3,'design_sha256':verify_design(),'files':{}}))
            with self.assertRaisesRegex(ValueError,'mismatch'):verify_runtime(path)

    def test_runtime_navigation_imports_no_privileged_modules(self):
        for name in ('adapters/webots/drone_v3.py','navigation/cadence.py','sensors/acquisition.py'):
            source=(ROOT/'src/blind_drone'/name).read_text()
            self.assertNotIn('getFromDef',source)
            tree=ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom):
                    self.assertFalse(any(s in (node.module or '') for s in ('evaluation','experiments','world','visualization')))


if __name__=='__main__':unittest.main()
