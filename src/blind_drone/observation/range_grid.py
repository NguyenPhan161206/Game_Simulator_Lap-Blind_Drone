"""Bounded grid built only from measured pose and geometric range rays.

Occupied cells persist in this static/ideal-sensor experiment. Unknown is
distinct from observed free. This is not the simulator's authoritative world.
"""
from heapq import heappop, heappush
from math import ceil, cos, floor, hypot, pi, sin, sqrt


def rotate_rpy(vector, attitude):
    x,y,z = vector
    roll,pitch,yaw = attitude
    y,z = cos(roll)*y-sin(roll)*z,sin(roll)*y+cos(roll)*z
    x,z = cos(pitch)*x+sin(pitch)*z,-sin(pitch)*x+cos(pitch)*z
    return cos(yaw)*x-sin(yaw)*y,sin(yaw)*x+cos(yaw)*y,z


class RangeGrid:
    def __init__(self, params, body_size_m, origin_radius_m):
        self.params = params
        self.cell_m = params["cell_m"]
        self.hull_radius = sqrt(sum(v*v for v in body_size_m))/2
        self.guard_radius = self.hull_radius+params["margin_m"]+self.cell_m/sqrt(2)
        self.plan_radius = self.guard_radius+params["planning_margin_m"]
        self.origin_radius = origin_radius_m
        self.free, self.occupied = set(),set()
        self.blocked = set()
        self.origin = None
        self.last_sample = None
        self.updates = self.peak_cells = 0
        self.exhausted = False
        self.occupied_version=0
        self.no_path_key=None
        count = ceil(self.plan_radius/self.cell_m)+1
        self.offsets = [(dx,dy) for dx in range(-count,count+1) for dy in range(-count,count+1)
                        if hypot(dx,dy)*self.cell_m <= self.plan_radius+self.cell_m/sqrt(2)]

    def cell(self,point):
        return floor(point[0]/self.cell_m),floor(point[1]/self.cell_m)

    def center(self,cell):
        return (cell[0]+.5)*self.cell_m,(cell[1]+.5)*self.cell_m

    def inside(self,cell):
        return self.origin is not None and all(abs(a-b)<=self.params["map_radius_m"] for a,b in zip(self.center(cell),self.origin))

    def retain(self,cell,hit):
        if not self.inside(cell):
            return
        if cell not in self.free and cell not in self.occupied and len(self.free)+len(self.occupied)>=self.params["max_cells"]:
            self.exhausted = True
            return
        if hit and cell not in self.occupied:
            self.occupied_version+=1
            self.occupied.add(cell)
            self.free.discard(cell)
            self.blocked.update((cell[0]+dx,cell[1]+dy) for dx,dy in self.offsets)
        elif not hit and cell not in self.occupied:
            self.free.add(cell)

    def update(self, observation):
        if self.last_sample==observation.sample_time_s:
            return
        self.last_sample = observation.sample_time_s
        self.updates += 1
        position,attitude = observation.state.position_m,observation.state.attitude_rad
        if self.origin is None:
            self.origin = position[:2]
        self.retain(self.cell(position),False)
        for reading in observation.ranges:
            if reading.name in {"range_up","range_down"}:
                continue
            angle = int(reading.name[6:])*pi/180
            direction = rotate_rpy((cos(angle),sin(angle),0),attitude)
            start = [position[i]+self.origin_radius*direction[i] for i in range(3)]
            endpoint = [start[i]+reading.distance_m*direction[i] for i in range(3)]
            free_distance = max(0,reading.distance_m-self.cell_m*.75)
            steps = max(1,ceil(free_distance/(self.cell_m*.5)))
            for index in range(steps+1):
                point = [start[i]+direction[i]*free_distance*index/steps for i in range(2)]
                self.retain(self.cell(point),False)
            if not reading.at_limit:
                self.retain(self.cell(endpoint),True)
        self.peak_cells = max(self.peak_cells,len(self.free)+len(self.occupied))

    def segment_ok(self,start,end,require_free=False):
        steps = max(1,ceil(hypot(end[0]-start[0],end[1]-start[1])/(self.cell_m*.3)))
        for i in range(steps+1):
            cell = self.cell((start[0]+(end[0]-start[0])*i/steps,start[1]+(end[1]-start[1])*i/steps))
            if not self.inside(cell) or cell in self.blocked or (require_free and cell not in self.free):
                return False
        return True

    def plan(self,start,goal):
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

    def guard(self,position,vx,vy):
        original=(vx,vy)
        nearby=[]
        for cell in self.occupied:
            x,y=self.center(cell)
            dx,dy=x-position[0],y-position[1]
            distance=hypot(dx,dy)
            if 1e-9<distance<3:
                nearby.append((dx/distance,dy/distance,max(0,distance-self.guard_radius)/self.params["guard_horizon_s"]))
        nearby.sort()
        for _ in range(4):
            for nx,ny,cap in nearby:
                excess=vx*nx+vy*ny-cap
                if excess>0:
                    vx,vy=vx-excess*nx,vy-excess*ny
        return vx,vy,hypot(vx-original[0],vy-original[1])>1e-6
