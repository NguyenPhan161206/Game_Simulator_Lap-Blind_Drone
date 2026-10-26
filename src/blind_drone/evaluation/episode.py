"""Privileged scoring only; this module is never imported by navigation."""
from math import dist, isfinite, sqrt


class EpisodeEvaluator:
    def __init__(self, goal_m, config):
        self.goal = tuple(goal_m)
        self.config = config
        self.previous_position = None
        self.previous_time = None
        self.dwell_start = None
        self.path_length_m = 0.0
        self.min_goal_distance_m = float("inf")
        self.result = None

    def update(self, time_s, position_m, velocity_m_s, contact_count):
        if self.result is not None:
            return self.result
        if not all(isfinite(value) for value in (time_s, *position_m, *velocity_m_s)) or time_s < 0:
            raise ValueError("Non-finite/negative evaluation sample")
        if self.previous_time is not None and time_s <= self.previous_time:
            raise ValueError("Evaluation time must increase")
        if self.previous_position is not None:
            self.path_length_m += dist(position_m, self.previous_position)
        self.previous_position, self.previous_time = tuple(position_m), time_s
        distance = dist(position_m, self.goal)
        self.min_goal_distance_m = min(self.min_goal_distance_m, distance)
        speed = sqrt(sum(value * value for value in velocity_m_s))
        c = self.config
        inside = distance <= c["goal_radius_m"] and speed <= c["stop_speed_m_s"]
        self.dwell_start = (time_s if self.dwell_start is None else self.dwell_start) if inside else None
        reason = None
        if contact_count:
            reason = "collision"
        elif any(value < low or value > high for value, low, high in zip(position_m, c["position_bounds_min_m"], c["position_bounds_max_m"])):
            reason = "out_of_bounds"
        elif self.dwell_start is not None and time_s - self.dwell_start >= c["dwell_s"] and time_s <= c["timeout_s"]:
            reason = "success"
        elif time_s >= c["timeout_s"]:
            reason = "timeout"
        if reason:
            self.result = {"outcome": reason, "elapsed_s": time_s, "path_length_m": self.path_length_m,
                           "final_distance_m": distance, "min_goal_distance_m": self.min_goal_distance_m,
                           "final_speed_m_s": speed, "contact_count": contact_count}
        return self.result


def summarize(episodes):
    """Report all failures; separate impossible negative controls from feasible cases."""
    groups = {}
    for policy in sorted({episode["policy"] for episode in episodes}):
        groups[policy] = {}
        for feasible in (True, False):
            subset = [e for e in episodes if e["policy"] == policy and e["feasible"] == feasible]
            successes = [e for e in subset if e["outcome"] == "success"]
            groups[policy]["feasible" if feasible else "negative_control"] = {
                "episodes": len(subset), "successes": len(successes),
                "success_rate": len(successes) / len(subset) if subset else None,
                "outcomes": {reason: sum(e["outcome"] == reason for e in subset)
                             for reason in ("success", "collision", "out_of_bounds", "timeout")},
                "success_only_mean_time_s": sum(e["elapsed_s"] for e in successes) / len(successes) if successes else None,
                "success_only_mean_path_m": sum(e["path_length_m"] for e in successes) / len(successes) if successes else None,
            }
    return groups
