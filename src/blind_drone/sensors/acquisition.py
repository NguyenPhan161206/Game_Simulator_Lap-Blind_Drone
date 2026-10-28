"""Acquisition clock and canonical range accounting; seconds, ENU pose, FLU rays.

No scene access. A repeated read never creates a new sensor acquisition.
"""
from dataclasses import dataclass, replace
from math import ceil, isfinite
import struct

from blind_drone.contracts.navigation import NavigationObservation

RANGE_NAMES = tuple(sorted([f"range_{a:03d}" for a in range(0, 360, 45)] + ["range_up", "range_down"]))
PACKET = struct.Struct("<dIHH10d")


def cpu_summary(samples):
    if not samples or any(not isfinite(x) or x < 0 for x in samples):
        raise ValueError("Missing/invalid decision CPU measurements")
    values = sorted(samples)
    return {"decisions":len(values),"mean_ms":sum(values)/len(values),
            "p95_ms":values[ceil(.95*len(values))-1],"max_ms":values[-1],
            "over_16_ms":sum(x>16 for x in values)}


class AcquisitionClock:
    def __init__(self, epoch_s, period_ms):
        if period_ms not in (32, 64) or not isfinite(epoch_s):
            raise ValueError("Invalid acquisition epoch/period")
        self.epoch_s, self.period_s = epoch_s, period_ms / 1000
        self.sequence = 0

    def poll(self, now_s):
        expected = round(self.epoch_s + (self.sequence + 1) * self.period_s, 9)
        if now_s < expected - 1e-8:
            return None
        if abs(now_s - expected) > 1e-8:
            raise ValueError("Missed acquisition tick; cannot invent samples")
        self.sequence += 1
        return self.sequence, expected


@dataclass(frozen=True)
class SampledObservation(NavigationObservation):
    acquisition_state: object

    @classmethod
    def construct(cls, current_state, sample):
        if sample is None:
            return cls(current_state, -1., "body_FLU", (), None)
        obs = NavigationObservation.from_devices(current_state, sample)
        return cls(obs.state, obs.sample_time_s, obs.frame, obs.ranges, sample["acquisition_state"])

    def usable(self, max_age_s, range_max_m):
        pose = self.acquisition_state
        return (pose is not None and abs(pose.time_s - self.sample_time_s) < 1e-8
                and super().usable(max_age_s, range_max_m)
                and NavigationObservation(pose, self.sample_time_s, self.frame, self.ranges).usable(max_age_s, range_max_m))

    def at_acquisition(self):
        return replace(self, state=self.acquisition_state)


def encode_packet(sequence, sample):
    readings = sample["readings"]
    if set(readings) != set(RANGE_NAMES):
        raise ValueError("Incomplete range vocabulary")
    valid = limit = 0
    values = []
    for i, name in enumerate(RANGE_NAMES):
        item = readings[name]
        valid |= int(item["valid"]) << i
        limit |= int(item["at_limit"]) << i
        values.append(item["distance_m"] if item["valid"] else float("nan"))
    return PACKET.pack(sample["sample_time_s"], sequence, valid, limit, *values)


def acquisition_summary(records, epoch_s, end_s, period_ms, score_start_s):
    """Audit every expected timestamp, sequence and byte, including invalid/warmup."""
    period = period_ms / 1000
    count = int((end_s - epoch_s + 1e-8) // period)
    complete = len(records) == count
    for i, item in enumerate(records, 1):
        complete &= item["sequence"] == i and abs(item["time_s"] - epoch_s - i * period) < 1e-8
        complete &= item["payload_bytes"] == PACKET.size and item["pose_time_s"] == item["time_s"]
    scored = [r for r in records if score_start_s + 1e-8 < r["time_s"] <= end_s + 1e-8]
    warmup = [r for r in records if r["time_s"] <= score_start_s + 1e-8]
    def describe(items):
        dt = items[-1]["time_s"] - items[0]["time_s"] if len(items) >= 2 else 0
        return {"packets": len(items), "values": 10 * len(items), "payload_bytes": PACKET.size * len(items),
                "invalid_values": sum(r["invalid_values"] for r in items),
                "first_s": items[0]["time_s"] if items else None,
                "last_s": items[-1]["time_s"] if items else None,
                "values_per_s": 10 * (len(items)-1) / dt if dt else None,
                "payload_bytes_per_s": PACKET.size * (len(items)-1) / dt if dt else None}
    return {"schedule_complete": bool(complete), "expected_packets": count,
            "all": describe(records), "warmup": describe(warmup), "scored": describe(scored)}
