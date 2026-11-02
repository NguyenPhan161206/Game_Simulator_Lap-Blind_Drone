"""Causal sampling and sensor dropout must preserve schema and evidence boundaries."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'versions/navigation_v4'), str(ROOT/'versions/initialization_aa_v1'),
               str(ROOT/'versions/retention_cold_v1'), str(ROOT/'versions/sensor_pilots_v1')]
from blind_drone.contracts.runtime import VehicleState
from blind_drone.experiments.protocol_v2 import load_v2_config
from blind_drone.navigation.observed import MissionV2
from blind_drone.sensors.acquisition import SampledObservation
from blind_drone_retention.navigation import RetentionNavigator
from blind_drone_sensor_pilots.protocol import generated_outputs, load_spec, profile_for, schedule, select_cases
from blind_drone_sensor_pilots.sampling import (SensorClock, SparseObservation, acquisition_summary,
    choose_period, encode_packet, names_for, observation_class)


class SensorPilotTests(unittest.TestCase):
    def sample(self, profile, time=0.):
        maximum = load_v2_config()['sensors']['range_max_m']
        state = VehicleState(time, (0., 0., 1.5), (0., 0., 0.), (0., 0., 0.), (0., 0., 0.))
        return {'sample_time_s': time, 'frame': 'body_FLU', 'acquisition_state': state,
                'readings': {name: {'distance_m': maximum, 'valid': True, 'at_limit': True} for name in names_for(profile)}}

    def test_causal_clock_can_switch_without_inventing_or_duplicate_acquisitions(self):
        clock = SensorClock(1.)
        self.assertIsNone(clock.poll(1.016))
        self.assertEqual(clock.poll(1.032), (1, 1.032))
        with self.assertRaises(ValueError): clock.poll(1.032)
        clock.complete(1.032, 64)
        self.assertIsNone(clock.poll(1.064))
        self.assertEqual(clock.poll(1.096), (2, 1.096))
        clock.complete(1.096, 32)
        self.assertEqual(clock.poll(1.128), (3, 1.128))
        clock.complete(1.128, 32)
        with self.assertRaises(ValueError): clock.poll(1.2)
        with self.assertRaises(ValueError): SensorClock(float('nan'))

    def test_adaptive_decision_requires_observed_route_and_clear_measured_ranges(self):
        readings = self.sample('adaptive')['readings']
        self.assertEqual(choose_period('adaptive', readings, 'follow_observed_path')[0], 64)
        for status in (None, 'initial_scan', 'scan_no_observed_route', 'stop_unobserved_command', 'follow_observed_path_limited'):
            self.assertEqual(choose_period('adaptive', readings, status)[0], 32)
        for value, valid in ((1.999, True), (None, False), (float('nan'), True)):
            altered = deepcopy(readings); altered['range_000'].update(distance_m=value, valid=valid)
            self.assertEqual(choose_period('adaptive', altered, 'follow_observed_path')[0], 32)
        self.assertEqual(choose_period('full', readings, 'follow_observed_path'), (32, 'fixed'))

    def test_sparse_packet_has_six_real_values_and_explicit_mask(self):
        for profile, count in (('full', 10), ('dropout', 6), ('sparse', 6)):
            packet = self.sample(profile)
            encoded = encode_packet(7, packet)
            self.assertEqual(len(encoded), 16+8*count)
            timestamp, seq, valid, limit = struct.unpack('<dIHH', encoded[:16])
            self.assertEqual((timestamp, seq, valid, limit), (0., 7, (1<<count)-1, (1<<count)-1))
        packet = self.sample('sparse'); packet['readings'].pop('range_000')
        with self.assertRaises(ValueError): encode_packet(1, packet)

    def test_dropout_is_rejected_but_designed_sparse_contract_accepts_same_six_values(self):
        packet = self.sample('sparse'); state = packet['acquisition_state']
        original = SampledObservation.construct(state, packet)
        designed = SparseObservation.construct(state, packet)
        self.assertFalse(original.usable(.12, load_v2_config()['sensors']['range_max_m']))
        self.assertTrue(designed.usable(.12, load_v2_config()['sensors']['range_max_m']))
        self.assertIs(observation_class('dropout'), SampledObservation)
        self.assertIs(observation_class('sparse'), SparseObservation)

    def test_sparse_contract_still_rejects_invalid_stale_and_mismatched_pose(self):
        packet = self.sample('sparse'); state = packet['acquisition_state']
        maximum = load_v2_config()['sensors']['range_max_m']
        obs = SparseObservation.construct(state, packet)
        self.assertFalse(replace(obs, state=replace(state, time_s=.121)).usable(.12, maximum))
        self.assertFalse(replace(obs, acquisition_state=replace(state, time_s=.032)).usable(.12, maximum))
        self.assertFalse(replace(obs, frame='world_ENU').usable(.12, maximum))
        for change in ({'valid': False}, {'distance_m': maximum+1}, {'distance_m': 1., 'at_limit': True}):
            other = deepcopy(packet); other['readings']['range_000'].update(change)
            self.assertFalse(SparseObservation.construct(state, other).usable(.12, maximum))

    def test_sparse_design_never_fills_unobserved_diagonal_cells(self):
        navs = {}
        for profile in ('full', 'dropout', 'sparse'):
            nav = RetentionNavigator(MissionV2((5., 0., 1.5), 'mapped'), load_v2_config(), None)
            packet = self.sample(profile)
            command = nav.step(observation_class(profile).construct(packet['acquisition_state'], packet))
            navs[profile] = nav
            if profile == 'dropout':
                self.assertEqual(command.forward_m_s, 0.)
                self.assertEqual(command.yaw_rate_rad_s, 0.)
                self.assertEqual(nav.status, 'invalid_or_stale_observation')
        cell = navs['full'].grid.cell((2., 2.))
        self.assertIn(cell, navs['full'].grid.free)
        self.assertNotIn(cell, navs['sparse'].grid.free)
        self.assertFalse(navs['dropout'].grid.free)

    def test_schedule_audit_rejects_missing_samples_and_ineffective_device_changes(self):
        records = []
        for sequence, (stamp, used) in enumerate(((.032, 32), (.096, 64)), 1):
            sample = self.sample('adaptive', stamp)
            records.append({'sequence': sequence, 'time_s': stamp, 'pose_time_s': stamp,
                'payload_bytes': 96, 'invalid_values': 0, 'period_ms': used,
                'device_periods_ms': {name: used for name in names_for('adaptive')},
                'all_device_periods_ms': {name: used for name in names_for('adaptive')},
                'scheduler_status': 'follow_observed_path', 'readings': sample['readings'],
                'next_period_ms': 64, 'schedule_reason': 'observed_route_and_clear_ranges'})
        self.assertTrue(acquisition_summary(records, 0., .128, 'adaptive', .032)['schedule_complete'])
        self.assertFalse(acquisition_summary(records[:1], 0., .128, 'adaptive', .032)['schedule_complete'])
        tampered = deepcopy(records); tampered[1]['device_periods_ms']['range_000'] = 32
        self.assertFalse(acquisition_summary(tampered, 0., .128, 'adaptive', .032)['schedule_complete'])
        tampered = deepcopy(records); tampered[0]['next_period_ms'] = 32
        self.assertFalse(acquisition_summary(tampered, 0., .128, 'adaptive', .032)['schedule_complete'])

    def test_fixed_pilot_membership_arm_order_and_no_heldout(self):
        _, cases = generated_outputs()
        for study, total in (('adaptive', 48), ('sparse', 72)):
            spec = load_spec(study); rows = list(schedule(cases, spec))
            self.assertEqual(len(rows), total)
            for case in cases:
                order = [arm for item, _, rep, arm in rows if item['id'] == case['id']]
                size = len(spec['arms'])
                self.assertEqual(order[:size], order[size:][::-1])
            for split in ('validation', 'test'):
                with self.assertRaisesRegex(ValueError, 'development only'):
                    select_cases(split, study=study)
        with self.assertRaises(ValueError): profile_for('adaptive', 'sparse')


if __name__ == '__main__':
    unittest.main()
