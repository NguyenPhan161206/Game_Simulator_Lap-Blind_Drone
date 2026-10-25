"""Simulator-independent data passed to the stabilizer; ENU world, FLU body."""
from dataclasses import dataclass


@dataclass(frozen=True)
class VehicleState:
    time_s: float
    position_m: tuple[float, float, float]
    velocity_m_s: tuple[float, float, float]
    attitude_rad: tuple[float, float, float]
    angular_velocity_rad_s: tuple[float, float, float]


@dataclass(frozen=True)
class MotionCommand:
    forward_m_s: float = 0.0
    left_m_s: float = 0.0
    up_m_s: float = 0.0
    yaw_rate_rad_s: float = 0.0

    @classmethod
    def from_operator(cls, packet, limits):
        """Accept a fixed command vocabulary; reject extra/privileged fields."""
        if set(packet) != {"kind", "forward_m_s", "left_m_s", "up_m_s", "yaw_rate_rad_s"}:
            raise ValueError("Invalid operator command fields")
        if packet["kind"] != "motion":
            raise ValueError("Invalid command kind")
        from math import hypot, isfinite
        values = [float(packet[name]) for name in
                  ("forward_m_s", "left_m_s", "up_m_s", "yaw_rate_rad_s")]
        if not all(isfinite(value) for value in values):
            raise ValueError("Non-finite command")
        caps = [limits["horizontal_speed_m_s"], limits["horizontal_speed_m_s"],
                limits["vertical_speed_m_s"], limits["yaw_rate_rad_s"]]
        values = [max(-cap, min(cap, value)) for cap, value in zip(caps, values)]
        horizontal = hypot(values[0], values[1])
        if horizontal > limits["horizontal_speed_m_s"]:
            scale = limits["horizontal_speed_m_s"] / horizontal
            values[0] *= scale
            values[1] *= scale
        return cls(*values)
