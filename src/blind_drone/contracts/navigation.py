"""Public observations and a strictly limited mission protocol; metres/seconds/radians."""
from dataclasses import dataclass
from math import isfinite

from blind_drone.contracts.runtime import VehicleState


@dataclass(frozen=True)
class RangeReading:
    name: str
    distance_m: float | None
    valid: bool
    at_limit: bool


@dataclass(frozen=True)
class NavigationObservation:
    state: VehicleState
    sample_time_s: float
    frame: str
    ranges: tuple[RangeReading, ...]

    @classmethod
    def from_devices(cls, state, packet):
        # Explicit construction: telemetry, ground truth and arbitrary extra fields
        # are never forwarded to navigation.
        if packet is None:
            return cls(state, -1.0, "body_FLU", ())
        return cls(state, packet["sample_time_s"], packet["frame"], tuple(
            RangeReading(name, value["distance_m"], value["valid"], value["at_limit"])
            for name, value in sorted(packet["readings"].items())))

    def usable(self, max_age_s, range_max_m):
        state = self.state
        numbers = (state.time_s, self.sample_time_s, *state.position_m,
                   *state.velocity_m_s, *state.attitude_rad, *state.angular_velocity_rad_s)
        expected = {f"range_{angle:03d}" for angle in range(0, 360, 45)} | {"range_up", "range_down"}
        return (all(isfinite(value) for value in numbers)
                and self.frame == "body_FLU"
                and 0 <= state.time_s - self.sample_time_s <= max_age_s
                and len(self.ranges) == len(expected)
                and {value.name for value in self.ranges} == expected
                and all(value.valid and value.distance_m is not None
                        and isfinite(value.distance_m) and 0 <= value.distance_m <= range_max_m + 1e-6
                        and (not value.at_limit or value.distance_m >= range_max_m - 1e-6)
                        for value in self.ranges))


@dataclass(frozen=True)
class NavigationMission:
    goal_m: tuple[float, float, float]
    policy: str

    @classmethod
    def from_packet(cls, packet):
        if not isinstance(packet, dict) or set(packet) != {"kind", "goal_m", "policy"} or packet["kind"] != "mission":
            raise ValueError("Invalid mission fields")
        if packet["policy"] not in {"direct", "reactive"}:
            raise ValueError("Unknown baseline")
        goal = packet["goal_m"]
        if not isinstance(goal, (list, tuple)) or len(goal) != 3:
            raise ValueError("Goal must be a three-dimensional ENU coordinate")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) for value in goal):
            raise ValueError("Goal must contain finite coordinates")
        return cls(tuple(float(value) for value in goal), packet["policy"])
