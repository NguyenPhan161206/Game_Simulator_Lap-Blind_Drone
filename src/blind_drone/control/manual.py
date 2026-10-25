"""Keyboard commands share the same MotionCommand path as smoke operator input."""
from blind_drone.contracts.runtime import MotionCommand


def keyboard_command(keys, limits):
    if ord(" ") in keys:
        return MotionCommand()
    axis = lambda positive, negative: int(ord(positive) in keys) - int(ord(negative) in keys)
    return MotionCommand.from_operator({
        "kind": "motion",
        "forward_m_s": axis("W", "S") * limits["horizontal_speed_m_s"],
        "left_m_s": axis("A", "D") * limits["horizontal_speed_m_s"],
        "up_m_s": axis("T", "G") * limits["vertical_speed_m_s"],
        "yaw_rate_rad_s": axis("Q", "E") * limits["yaw_rate_rad_s"],
    }, limits)
