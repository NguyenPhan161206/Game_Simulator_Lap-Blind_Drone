"""Privileged geometry checks/witness paths. Never an input to navigation.

An inflated AABB is a conservative approximation for a spherical hull. Grid
failure is not a proof of infeasibility. Only a found, checked path is certified.
"""
from collections import deque
from math import dist, isfinite, sqrt


def inflated_rectangles(obstacles, radius_m):
    return [(o["center_m"][0] - o["size_m"][0]/2 - radius_m,
             o["center_m"][0] + o["size_m"][0]/2 + radius_m,
             o["center_m"][1] - o["size_m"][1]/2 - radius_m,
             o["center_m"][1] + o["size_m"][1]/2 + radius_m) for o in obstacles]


def segment_clear(start, end, rectangles):
    for xmin, xmax, ymin, ymax in rectangles:
        enter, leave = 0.0, 1.0
        for a, b, low, high in ((start[0], end[0], xmin, xmax), (start[1], end[1], ymin, ymax)):
            delta = b - a
            if abs(delta) < 1e-12:
                if not low <= a <= high:
                    enter, leave = 1.0, 0.0
                    break
            else:
                t1, t2 = sorted(((low-a)/delta, (high-a)/delta))
                enter, leave = max(enter, t1), min(leave, t2)
        if enter <= leave:
            return False
    return True


def validate_geometry(case):
    for key in ("start_m", "goal_m"):
        values = case[key]
        if len(values) != 3 or not all(isfinite(v) for v in values) or not all(abs(v) < 8 for v in values[:2]):
            raise ValueError("Invalid start/goal")
    if case["start_m"][2] != 1.5 or case["goal_m"][2] != 1.5:
        raise ValueError("Suite v1 certifies a fixed 1.5 m altitude only")
    if not isfinite(case["start_yaw_rad"]) or len(case["obstacles"]) > 3:
        raise ValueError("Invalid yaw or block capacity")
    for obstacle in case["obstacles"]:
        c, s = obstacle["center_m"], obstacle["size_m"]
        if len(c) != 3 or len(s) != 3 or not all(isfinite(v) for v in (*c,*s)) or min(s) <= 0:
            raise ValueError("Invalid obstacle geometry")
        if any(abs(c[i]) + s[i]/2 >= 9.4 for i in (0,1)) or c[2] != 1.5 or s[2] != 3.0:
            raise ValueError("Obstacle outside certified suite domain")


def path_certificate(case, body_size_m, step_m=0.25, margin_m=0.12, bounds=(-9,9)):
    validate_geometry(case)
    if step_m <= 0 or margin_m < 0 or bounds[0] >= bounds[1]:
        raise ValueError("Invalid witness grid")
    radius = sqrt(sum(s*s for s in body_size_m))/2 + margin_m
    rectangles = inflated_rectangles(case["obstacles"],radius)
    start, goal = case["start_m"][:2], case["goal_m"][:2]
    if not segment_clear(start,start,rectangles):
        raise ValueError("Start overlaps conservative hull obstacle")
    if not case["feasible"]:
        # A negative label requires a geometric proof stronger than BFS failure.
        inside = any(all(abs(case["goal_m"][i]-o["center_m"][i]) < o["size_m"][i]/2 for i in range(3)) for o in case["obstacles"])
        if not inside:
            raise ValueError("Negative case lacks a goal-inside-solid proof")
        return {"kind":"goal_inside_solid", "radius_m":radius, "waypoints_m":[]}
    if not segment_clear(goal,goal,rectangles):
        raise ValueError("Feasible goal overlaps conservative hull obstacle")
    low, high = bounds
    count = round((high-low)/step_m)
    def point(cell):
        return [low + cell[0]*step_m, low + cell[1]*step_m]
    def free(cell):
        return all(0 <= v <= count for v in cell) and segment_clear(point(cell),point(cell),rectangles)
    def nearest(p):
        candidates = [(round((p[0]-low)/step_m)+dx, round((p[1]-low)/step_m)+dy) for dx in range(-2,3) for dy in range(-2,3)]
        for cell in sorted(candidates,key=lambda c:dist(p,point(c))):
            if free(cell) and segment_clear(p,point(cell),rectangles):
                return cell
        raise ValueError("No local grid connection")
    first, last = nearest(start), nearest(goal)
    queue, parents = deque([first]), {first:None}
    while queue and last not in parents:
        cell = queue.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            nxt = cell[0]+dx,cell[1]+dy
            if nxt not in parents and free(nxt) and segment_clear(point(cell),point(nxt),rectangles):
                parents[nxt] = cell
                queue.append(nxt)
    if last not in parents:
        raise ValueError("No certified grid path; cannot label case feasible")
    cells, cursor = [], last
    while cursor is not None:
        cells.append(cursor)
        cursor = parents[cursor]
    points = [start,*[point(c) for c in reversed(cells)],goal]
    # Greedy line-of-sight compression; every retained segment is checked again.
    route, index = [points[0]], 0
    while index < len(points)-1:
        farthest = next(j for j in range(len(points)-1,index,-1) if segment_clear(points[index],points[j],rectangles))
        route.append(points[farthest])
        index = farthest
    return {"kind":"conservative_horizontal_grid_witness", "radius_m":radius, "grid_step_m":step_m,
            "waypoints_m":[[*p,1.5] for p in route], "length_m":sum(dist(a,b) for a,b in zip(route,route[1:]))}
