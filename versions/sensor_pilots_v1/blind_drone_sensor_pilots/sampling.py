"""Causal hardware scheduling, explicit sparse schema and binary accounting."""
from math import isfinite
import struct

from blind_drone.sensors.acquisition import RANGE_NAMES, SampledObservation

SPARSE_NAMES = tuple(sorted(('range_000', 'range_090', 'range_180', 'range_270', 'range_up', 'range_down')))
PROFILES = ('full', 'adaptive', 'dropout', 'sparse')


def names_for(profile):
    if profile not in PROFILES:
        raise ValueError('Unknown public sensor profile')
    return SPARSE_NAMES if profile in ('dropout', 'sparse') else RANGE_NAMES


def choose_period(profile, readings, status):
    names_for(profile)
    if profile != 'adaptive':
        return 32, 'fixed'
    if status not in ('follow_observed_path', 'follow_observed_detour', 'recover_observed_clearance'):
        return 32, 'not_following_observed_route'
    horizontal = [r for name, r in readings.items() if name not in ('range_up', 'range_down')]
    if set(readings) != set(RANGE_NAMES) or any(not r['valid'] or r['distance_m'] is None or
            not isfinite(r['distance_m']) or r['distance_m'] < 2. for r in horizontal):
        return 32, 'near_or_invalid_range'
    return 64, 'observed_route_and_clear_ranges'


class SensorClock:
    def __init__(self, epoch_s):
        if not isfinite(epoch_s):
            raise ValueError('Finite acquisition epoch required')
        self.next_s = round(epoch_s+.032, 9)
        self.period_ms = 32
        self.sequence = 0
        self.pending = False

    def poll(self, now):
        if self.pending:
            raise ValueError('Previous acquisition has no next-period decision')
        if now < self.next_s-1e-8:
            return None
        if not isfinite(now) or abs(now-self.next_s) > 1e-8:
            raise ValueError('Missed acquisition; cannot invent samples')
        self.pending = True
        self.sequence += 1
        return self.sequence, self.next_s

    def complete(self, now, next_period_ms):
        if not self.pending or next_period_ms not in (32, 64) or abs(now-self.next_s) > 1e-8:
            raise ValueError('Invalid next acquisition schedule')
        self.pending = False
        self.period_ms = next_period_ms
        self.next_s = round(now+next_period_ms/1000, 9)


def encode_packet(sequence, sample):
    names = tuple(sorted(sample['readings']))
    if names not in (RANGE_NAMES, SPARSE_NAMES):
        raise ValueError('Unregistered sensor vocabulary')
    valid = limit = 0
    values = []
    for i, name in enumerate(names):
        reading = sample['readings'][name]
        valid |= int(reading['valid']) << i
        limit |= int(reading['at_limit']) << i
        values.append(reading['distance_m'] if reading['valid'] else float('nan'))
    return struct.pack('<dIHH'+str(len(names))+'d', sample['sample_time_s'], sequence, valid, limit, *values)


class SparseObservation(SampledObservation):
    """Six required real devices; absent diagonals remain unknown in the grid."""
    def usable(self, max_age_s, range_max_m):
        pose = self.acquisition_state
        if pose is None:
            return False
        numbers = (self.state.time_s, self.sample_time_s, pose.time_s,
                   *self.state.position_m, *self.state.velocity_m_s, *self.state.attitude_rad,
                   *self.state.angular_velocity_rad_s, *pose.position_m, *pose.velocity_m_s,
                   *pose.attitude_rad, *pose.angular_velocity_rad_s)
        return (all(isfinite(value) for value in numbers) and self.frame == 'body_FLU'
            and abs(pose.time_s-self.sample_time_s) < 1e-8
            and 0 <= self.state.time_s-self.sample_time_s <= max_age_s
            and len(self.ranges) == len(SPARSE_NAMES) and {r.name for r in self.ranges} == set(SPARSE_NAMES)
            and all(r.valid and r.distance_m is not None and isfinite(r.distance_m)
                    and 0 <= r.distance_m <= range_max_m+1e-6
                    and (not r.at_limit or r.distance_m >= range_max_m-1e-6) for r in self.ranges))


def observation_class(profile):
    names_for(profile)
    return SparseObservation if profile == 'sparse' else SampledObservation


def acquisition_summary(records, epoch_s, end_s, profile, score_start_s):
    names = names_for(profile)
    size = 16+8*len(names)
    next_s, used_period = round(epoch_s+.032, 9), 32
    complete = True
    for seq, record in enumerate(records, 1):
        complete &= (record['sequence'] == seq and abs(record['time_s']-next_s) < 1e-8
            and record['pose_time_s'] == record['time_s'] and record['period_ms'] == used_period
            and record['payload_bytes'] == size and set(record['device_periods_ms'].values()) == {used_period}
            and set(record['device_periods_ms']) == set(names))
        complete &= (set(record['all_device_periods_ms']) == set(RANGE_NAMES) and
            all(value == (used_period if name in names else 0)
                for name, value in record['all_device_periods_ms'].items()))
        expected, reason = choose_period(profile, record['readings'], record['scheduler_status'])
        complete &= record['next_period_ms'] == expected and record['schedule_reason'] == reason
        used_period = record['next_period_ms']
        next_s = round(record['time_s']+used_period/1000, 9)
    complete &= next_s > end_s+1e-8
    def describe(items, duration):
        return {'packets': len(items), 'values': len(names)*len(items), 'payload_bytes': size*len(items),
                'invalid_values': sum(r['invalid_values'] for r in items),
                'payload_bytes_per_s': size*len(items)/duration if duration > 0 else None,
                'values_per_s': len(names)*len(items)/duration if duration > 0 else None}
    scored = [r for r in records if score_start_s+1e-8 < r['time_s'] <= end_s+1e-8]
    warmup = [r for r in records if r['time_s'] <= score_start_s+1e-8]
    return {'schedule_complete': bool(complete), 'expected_packets': len(records) if complete else None,
            'all': describe(records, end_s-epoch_s), 'warmup': describe(warmup, score_start_s-epoch_s),
            'scored': describe(scored, end_s-score_start_s)}
