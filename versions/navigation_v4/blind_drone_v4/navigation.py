"""V4 navigation: public measured grid only; no world/evaluator/adapter access."""
from heapq import heappop, heappush
from math import cos, floor, hypot, sin

from blind_drone.contracts.runtime import MotionCommand
from blind_drone.navigation.cadence import CadenceNavigator


def touches_cell(start, end, cell, size):
    """Closed segment/AABB intersection: conservatively include corner contacts."""
    enter, leave = 0., 1.
    for axis in (0, 1):
        low, high = cell[axis]*size, (cell[axis]+1)*size
        delta = end[axis]-start[axis]
        if abs(delta) < 1e-12:
            if start[axis] < low-1e-12 or start[axis] > high+1e-12:
                return False
        else:
            first, last = sorted(((low-start[axis])/delta, (high-start[axis])/delta))
            enter, leave = max(enter, first), min(leave, last)
            if enter > leave+1e-12:
                return False
    return True


def segment_cells(start, end, size):
    bounds = [(floor(min(start[i], end[i])/size)-1, floor(max(start[i], end[i])/size)) for i in (0, 1)]
    return {(x, y) for x in range(bounds[0][0], bounds[0][1]+1)
            for y in range(bounds[1][0], bounds[1][1]+1) if touches_cell(start, end, (x, y), size)}


def swept_clearance(grid, start, end):
    dx, dy = end[0]-start[0], end[1]-start[1]
    length2 = dx*dx+dy*dy
    nearest = None
    for cell in grid.occupied:
        x, y = grid.center(cell)
        t = max(0., min(1., ((x-start[0])*dx+(y-start[1])*dy)/length2)) if length2 else 0.
        distance = hypot(x-start[0]-t*dx, y-start[1]-t*dy)
        nearest = distance if nearest is None else min(nearest, distance)
    return nearest


def observed_segment(grid, start, end, recovery=False):
    cells = segment_cells(start, end, grid.cell_m)
    if any(not grid.inside(c) or c not in grid.free or (not recovery and c in grid.blocked) for c in cells):
        return False
    clearance = swept_clearance(grid, start, end)
    return clearance is None or clearance >= grid.guard_radius


class FreeRoute:
    """Bounded search of the observed component, rooted at the actual pose."""
    def __init__(self, grid):
        self.grid = grid
        self.expansions = 0
        self.reached_goal = False

    def plan(self, start, goal):
        g = self.grid
        self.expansions = 0
        self.reached_goal = False
        first, last = g.cell(start), g.cell(goal)
        if first not in g.free or first in g.blocked or not g.inside(first):
            return []
        valid = {c for c in g.free if c not in g.blocked and g.inside(c)}
        costs, parents, frontier = {}, {}, []
        # Multiple verified connections avoid assuming the robot is at cell center.
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                cell = first[0]+dx, first[1]+dy
                if cell in valid and observed_segment(g, start, g.center(cell)):
                    cost = hypot(g.center(cell)[0]-start[0], g.center(cell)[1]-start[1])
                    costs[cell], parents[cell] = cost, None
                    heappush(frontier, (cost+hypot(g.center(cell)[0]-goal[0], g.center(cell)[1]-goal[1]), cost, cell))
        best = None
        while frontier and self.expansions < g.params['max_expansions']:
            _, cost, cell = heappop(frontier)
            if cost != costs[cell]:
                continue
            self.expansions += 1
            distance = hypot(g.center(cell)[0]-goal[0], g.center(cell)[1]-goal[1])
            if best is None or (distance, cost, cell) < best:
                best = distance, cost, cell
            if cell == last and observed_segment(g, g.center(cell), goal):
                self.reached_goal = True
                best = distance, cost, cell
                break
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                nxt = cell[0]+dx, cell[1]+dy
                if nxt not in valid:
                    continue
                if dx and dy and ((cell[0]+dx, cell[1]) not in valid or (cell[0], cell[1]+dy) not in valid):
                    continue
                new = cost+hypot(dx, dy)*g.cell_m
                if new < costs.get(nxt, float('inf')):
                    costs[nxt], parents[nxt] = new, cell
                    heuristic = hypot(g.center(nxt)[0]-goal[0], g.center(nxt)[1]-goal[1])
                    heappush(frontier, (new+heuristic, new, nxt))
        if best is None or (not self.reached_goal and best[0] >= hypot(start[0]-goal[0], start[1]-goal[1])-.25):
            return []
        cells, cursor = [], best[2]
        while cursor is not None:
            cells.append(cursor)
            cursor = parents[cursor]
        route = [tuple(start[:2]), *[g.center(c) for c in reversed(cells)]]
        if self.reached_goal:
            route.append(tuple(goal[:2]))
        return route


class ObservedDetourNavigator(CadenceNavigator):
    def __init__(self, mission, config):
        super().__init__(mission, config)
        self.route_search = FreeRoute(self.grid)
        self.detour_path = []
        self.detour_next_plan = 0.
        self.detour_plans = self.detour_decisions = self.detour_peak_expansions = 0
        self.selected_target = None
        self.selected_clearance_m = None
        self.selected_recovery = False

    def target_on_path(self, position, path, recovery=False):
        target = None
        for point in path[1:]:
            if hypot(point[0]-position[0], point[1]-position[1]) > self.params['lookahead_m']:
                break
            if observed_segment(self.grid, position, point, recovery):
                target = point
            else:
                break
        return target

    def _step(self, observation):
        self.selected_target = self.selected_clearance_m = None
        self.selected_recovery = False
        if not observation.usable(self.config['navigation']['range_max_age_s'], self.config['sensors']['range_max_m']):
            self.status = 'invalid_or_stale_observation'
            return MotionCommand()
        if self.last_range_sample != observation.sample_time_s:
            self.last_range_sample = observation.sample_time_s
            self.range_samples += 1
        state = observation.state
        if self.started is None:
            self.started = state.time_s
        self.grid.update(observation)
        if self.grid.exhausted:
            self.status = 'memory_budget_exhausted'
            return MotionCommand()
        scan = state.time_s-self.started < self.params['initial_scan_s']
        position, goal = state.position_m, self.mission.goal_m
        distance = hypot(goal[0]-position[0], goal[1]-position[1])
        target, recovering, detour = None, False, False
        if not scan:
            if state.time_s >= self.next_plan:
                self.path = self.grid.plan(position, goal)
                self.next_plan = state.time_s+self.params['replan_period_s']
                self.plans += 1
            target = self.target_on_path(position, self.path)
            if distance < self.params['lookahead_m'] and observed_segment(self.grid, position, goal):
                target = goal
            if target is None and self.grid.cell(position) in self.grid.blocked:
                candidate = self.grid.escape_target(position, goal)
                if candidate is not None and observed_segment(self.grid, position, candidate, True):
                    target, recovering = candidate, True
            if target is None and self.grid.cell(position) not in self.grid.blocked:
                candidate = self.target_on_path(position, self.detour_path)
                if state.time_s >= self.detour_next_plan or (self.detour_path and candidate is None):
                    self.detour_path = self.route_search.plan(position, goal)
                    self.detour_next_plan = state.time_s+self.params['replan_period_s']
                    self.detour_plans += 1
                    self.detour_peak_expansions = max(self.detour_peak_expansions, self.route_search.expansions)
                    self.grid.peak_expansions = max(self.grid.peak_expansions, self.route_search.expansions)
                    candidate = self.target_on_path(position, self.detour_path)
                target, detour = candidate, candidate is not None
        vx = vy = 0.
        if scan:
            self.status = 'initial_scan'
        elif target is None:
            scan = True
            self.status = 'scan_no_observed_route'
        else:
            tx, ty = target[0]-position[0], target[1]-position[1]
            length = hypot(tx, ty)
            if length > .03:
                speed = min(.2 if recovering else self.params['speed_m_s'], .65*distance)
                vx, vy = speed*tx/length, speed*ty/length
            self.status = 'recover_observed_clearance' if recovering else 'follow_observed_detour' if detour else 'follow_observed_path'
            self.detour_decisions += int(detour)
            self.selected_target = tuple(target[:2])
            self.selected_clearance_m = swept_clearance(self.grid, position, target)
            self.selected_recovery = recovering
        vx, vy, changed = self.grid.guard(position, vx, vy)
        # The guard can change heading: verify the final 16 ms command as well.
        if hypot(vx, vy) > 1e-9 and not observed_segment(
                self.grid, position, (position[0]+vx*.016, position[1]+vy*.016), recovering):
            vx = vy = 0.
            self.status = 'stop_unobserved_command'
        self.guard_events += int(changed)
        self.scan_decisions += int(scan)
        if changed:
            self.status += '_limited'
        yaw = state.attitude_rad[2]
        return MotionCommand(cos(yaw)*vx+sin(yaw)*vy, -sin(yaw)*vx+cos(yaw)*vy,
                             max(-.4, min(.4, .8*(goal[2]-position[2]))),
                             self.params['scan_yaw_rad_s'] if distance > .15 else 0.)

    def diagnostics(self):
        return {**super().diagnostics(), 'detour_plans': self.detour_plans,
                'detour_decisions': self.detour_decisions, 'detour_peak_expansions': self.detour_peak_expansions}
