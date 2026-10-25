"""PD stabilization of an ideal symmetric quadrotor; no scene access."""
from math import atan2, cos, isfinite, pi, sin, sqrt

from blind_drone.contracts.runtime import MotionCommand, VehicleState


def clamp(value, lower, upper):
    return max(lower, min(upper, value))


def wrap_angle(value):
    return (value + pi) % (2 * pi) - pi


class Stabilizer:
    def __init__(self, config):
        self.vehicle = config["vehicle"]
        self.gains = config["control"]
        self.gravity = config["world"]["gravity_m_s2"]
        self.target_altitude = None
        self.target_yaw = None

    def reset(self):
        self.target_altitude = self.target_yaw = None

    def step(self, state: VehicleState, command: MotionCommand, dt_s: float):
        numbers = (*state.position_m, *state.velocity_m_s, *state.attitude_rad,
                   *state.angular_velocity_rad_s, dt_s)
        if dt_s <= 0 or not all(isfinite(value) for value in numbers):
            raise ValueError("Invalid state or control period")
        z = state.position_m[2]
        roll, pitch, yaw = state.attitude_rad
        if self.target_altitude is None:
            self.target_altitude, self.target_yaw = z, yaw
        low, high = self.vehicle["altitude_bounds_m"]
        self.target_altitude = clamp(self.target_altitude + command.up_m_s * dt_s, low, high)
        self.target_yaw = wrap_angle(self.target_yaw + command.yaw_rate_rad_s * dt_s)
        vx, vy, vz = state.velocity_m_s
        body_vx = cos(yaw) * vx + sin(yaw) * vy
        body_vy = -sin(yaw) * vx + cos(yaw) * vy
        gains = self.gains
        accel_limit = gains["acceleration_limit_m_s2"]
        ax = clamp(gains["velocity_gain_s_inv"] * (command.forward_m_s - body_vx), -accel_limit, accel_limit)
        ay = clamp(gains["velocity_gain_s_inv"] * (command.left_m_s - body_vy), -accel_limit, accel_limit)
        tilt_limit = gains["tilt_limit_rad"]
        desired_roll = clamp(-atan2(ay, self.gravity), -tilt_limit, tilt_limit)
        desired_pitch = clamp(atan2(ax, self.gravity), -tilt_limit, tilt_limit)
        wx, wy, wz = state.angular_velocity_rad_s
        tx = gains["attitude_p_nm_rad"] * (desired_roll - roll) - gains["attitude_d_nm_s_rad"] * wx
        ty = gains["attitude_p_nm_rad"] * (desired_pitch - pitch) - gains["attitude_d_nm_s_rad"] * wy
        tz = gains["yaw_p_nm_rad"] * wrap_angle(self.target_yaw - yaw) + gains["yaw_d_nm_s_rad"] * (command.yaw_rate_rad_s - wz)
        az = gains["altitude_p_s_inv2"] * (self.target_altitude - z) + gains["altitude_d_s_inv"] * (command.up_m_s - vz)
        thrust = self.vehicle["mass_kg"] * max(0.0, self.gravity + az) / max(0.5, cos(roll) * cos(pitch))
        arm = self.vehicle["arm_offset_m"]
        ratio = self.vehicle["torque_to_thrust_m"]
        coefficient = self.vehicle["thrust_coefficient_n_s2"]
        max_speed = self.vehicle["motor_max_rad_s"]
        motors = []
        for xsign, ysign, spin in ((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)):
            force = thrust / 4 + ysign * tx / (4 * arm) - xsign * ty / (4 * arm) + spin * tz / (4 * ratio)
            motors.append(clamp(sqrt(max(0.0, force) / coefficient), 0.0, max_speed))
        return tuple(motors)
