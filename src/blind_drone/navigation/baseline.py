"""Original engineering baselines using local range rays, not a complete map.

Reactive uses a left-tangent latch to break head-on symmetry. Sparse rays do
not certify free space, and concave obstacles can trap this heuristic.
"""
from math import cos, hypot, pi, sin, sqrt

from blind_drone.contracts.runtime import MotionCommand


class BaselineNavigator:
    def __init__(self, mission, config):
        self.mission = mission
        self.params = config["navigation"]
        self.range_max = config["sensors"]["range_max_m"]
        self.vehicle = config["vehicle"]
        self.following = False
        self.hit_distance = None
        self.status = "waiting_for_sensors"

    def step(self, observation):
        p = self.params
        if not observation.usable(p["range_max_age_s"], self.range_max):
            self.status = "invalid_or_stale_observation"
            return MotionCommand()
        state = observation.state
        dx, dy, dz = (a - b for a, b in zip(self.mission.goal_m, state.position_m))
        yaw = state.attitude_rad[2]
        gx, gy = cos(yaw) * dx + sin(yaw) * dy, -sin(yaw) * dx + cos(yaw) * dy
        distance = hypot(gx, gy)
        ux, uy = (gx / distance, gy / distance) if distance > 1e-8 else (0.0, 0.0)
        speed = min(p["speed_m_s"], self.vehicle["horizontal_speed_m_s"], p["goal_gain_s_inv"] * distance)
        vx, vy = ux * speed, uy * speed
        horizontal = []
        for reading in observation.ranges:
            if reading.name in {"range_up", "range_down"}:
                continue
            angle = int(reading.name.removeprefix("range_")) * pi / 180
            horizontal.append((reading.distance_m, cos(angle), sin(angle)))
        self.status = "direct_to_goal"
        if self.mission.policy == "reactive" and distance > 0.25:
            goal_rays = [r for r, nx, ny in horizontal if nx * ux + ny * uy >= cos(pi / 4 + 1e-6)]
            blocked = min(goal_rays, default=self.range_max) < min(p["avoid_distance_m"], distance)
            if not self.following and blocked:
                self.following, self.hit_distance = True, distance
            if self.following and not blocked and distance < self.hit_distance - p["leave_progress_m"]:
                self.following = False
            if self.following:
                r, nx, ny = min(horizontal)
                # Tangent counterclockwise about the nearest observed surface.
                # A radial correction regulates distance without object labels.
                correction = max(-0.8, min(0.8, (r - p["follow_distance_m"]) * 0.8))
                tx, ty = -ny + correction * nx + 0.12 * ux, nx + correction * ny + 0.12 * uy
                length = hypot(tx, ty)
                vx, vy = speed * tx / length, speed * ty / length
                self.status = "follow_left_tangent"
            # Project requested velocity onto range-based braking half-planes.
            # This is a heuristic for these rays, not a swept-hull guarantee.
            for _ in range(2):
                for r, nx, ny in horizontal:
                    cap = sqrt(2 * p["brake_acceleration_m_s2"] * max(0.0, r - p["brake_margin_m"]))
                    excess = vx * nx + vy * ny - cap
                    if excess > 0:
                        vx, vy = vx - excess * nx, vy - excess * ny
        vz = max(-self.vehicle["vertical_speed_m_s"], min(self.vehicle["vertical_speed_m_s"], 0.8 * dz))
        readings = {r.name: r.distance_m for r in observation.ranges}
        if self.mission.policy == "reactive" and readings["range_up" if vz > 0 else "range_down"] < p["brake_margin_m"]:
            vz = 0.0
        return MotionCommand(vx, vy, vz, 0.0)
