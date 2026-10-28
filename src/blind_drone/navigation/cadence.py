"""V3 measurement-time projection around the unchanged mapped v2 planner.

The plan method is the v2 algorithm with expansion counters only; no new routing
parameters or privileged inputs. Current pose is still used for commands/guard.
"""
from heapq import heappop, heappush
from math import hypot

from blind_drone.navigation.observed import ObservedNavigator
from blind_drone.observation.range_grid import RangeGrid


class AcquisitionGrid(RangeGrid):
    def __init__(self, *args):
        super().__init__(*args)
        self.last_expansions = self.peak_expansions = 0

    def update(self, observation):
        super().update(observation.at_acquisition())

    def plan(self, start, goal):
        self.last_expansions = 0
        first,last = self.cell(start),self.cell(goal)
        key=(first,last,self.occupied_version)
        if self.no_path_key==key:return []
        if not self.inside(first) or not self.inside(last) or last in self.blocked:
            return []
        frontier = [(hypot(last[0]-first[0],last[1]-first[1]),0,first)]
        costs,parents = {first:0},{first:None}
        expansions = 0
        while frontier and expansions<self.params["max_expansions"]:
            _,cost,cell = heappop(frontier)
            if cost!=costs[cell]:
                continue
            if cell==last:
                cells=[]
                while cell is not None:
                    cells.append(cell);cell=parents[cell]
                return [start,*[self.center(c) for c in reversed(cells[0:-1])],goal[:2]]
            expansions+=1
            self.last_expansions = expansions
            self.peak_expansions = max(self.peak_expansions, expansions)
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                nxt=cell[0]+dx,cell[1]+dy
                if not self.inside(nxt) or nxt in self.blocked:
                    continue
                if dx and dy and ((cell[0]+dx,cell[1]) in self.blocked or (cell[0],cell[1]+dy) in self.blocked):
                    continue
                step=hypot(dx,dy)*(1 if nxt in self.free else self.params["unknown_cost"])
                new=cost+step
                if new<costs.get(nxt,float("inf")):
                    costs[nxt],parents[nxt]=new,cell
                    heappush(frontier,(new+hypot(last[0]-nxt[0],last[1]-nxt[1]),new,nxt))
        if not frontier:self.no_path_key=key
        return []


class CadenceNavigator(ObservedNavigator):
    def __init__(self, mission, config):
        if mission.policy != "mapped":
            raise ValueError("V3 fixes the mapped policy")
        super().__init__(mission, config)
        self.grid = AcquisitionGrid(self.params, config["vehicle"]["body_size_m"],
                                    config["sensors"]["horizontal_origin_radius_m"])
