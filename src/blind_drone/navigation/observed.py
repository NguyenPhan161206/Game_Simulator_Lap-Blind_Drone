"""Reactive/guarded/observed-grid comparators. No privileged scene access."""
from dataclasses import dataclass
from math import cos, hypot, isfinite, sin
from time import perf_counter_ns

from blind_drone.contracts.runtime import MotionCommand
from blind_drone.navigation.baseline import BaselineNavigator
from blind_drone.observation.range_grid import RangeGrid


@dataclass(frozen=True)
class MissionV2:
    goal_m: tuple[float,float,float]
    policy: str

    @classmethod
    def from_packet(cls,packet):
        if not isinstance(packet,dict) or set(packet)!={"kind","goal_m","policy"} or packet["kind"]!="mission":
            raise ValueError("Invalid mission v2 fields")
        goal=packet["goal_m"]
        if packet["policy"] not in {"reactive","guarded","mapped"} or not isinstance(goal,(list,tuple)) or len(goal)!=3:
            raise ValueError("Invalid policy/goal")
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(v) for v in goal):
            raise ValueError("Non-finite goal")
        return cls(tuple(goal),packet["policy"])


class ObservedNavigator:
    def __init__(self,mission,config):
        self.mission,self.config=mission,config
        self.params=config["navigation_v2"]
        self.reactive=BaselineNavigator(MissionV2(mission.goal_m,"reactive"),config)
        self.grid=RangeGrid(self.params,config["vehicle"]["body_size_m"],config["sensors"]["horizontal_origin_radius_m"])
        self.status="waiting_for_sensors"
        self.started=None
        self.next_plan=0
        self.path=[]
        self.decisions=self.guard_events=self.scan_decisions=self.plans=0
        self.cpu_total_ns=self.cpu_max_ns=0
        self.last_range_sample=None
        self.range_samples=0

    def step(self,observation):
        start=perf_counter_ns()
        command=self._step(observation)
        elapsed=perf_counter_ns()-start
        self.decisions+=1;self.cpu_total_ns+=elapsed;self.cpu_max_ns=max(self.cpu_max_ns,elapsed)
        return command

    def _step(self,observation):
        if not observation.usable(self.config["navigation"]["range_max_age_s"],self.config["sensors"]["range_max_m"]):
            self.status="invalid_or_stale_observation"
            return MotionCommand()
        if self.last_range_sample!=observation.sample_time_s:
            self.last_range_sample=observation.sample_time_s
            self.range_samples+=1
        if self.mission.policy=="reactive":
            command=self.reactive.step(observation);self.status=self.reactive.status
            return command
        state=observation.state
        if self.started is None:self.started=state.time_s
        self.grid.update(observation)
        if self.grid.exhausted:
            self.status="memory_budget_exhausted"
            return MotionCommand()
        scan=state.time_s-self.started<self.params["initial_scan_s"]
        yaw=state.attitude_rad[2]
        dx,dy=(self.mission.goal_m[i]-state.position_m[i] for i in (0,1))
        distance=hypot(dx,dy)
        vx=vy=0.0
        if scan:
            self.status="initial_scan"
        elif self.mission.policy=="guarded":
            raw=self.reactive.step(observation)
            vx,vy=cos(yaw)*raw.forward_m_s-sin(yaw)*raw.left_m_s,sin(yaw)*raw.forward_m_s+cos(yaw)*raw.left_m_s
            length=hypot(vx,vy)
            if length>self.params["speed_m_s"]:
                vx,vy=vx*self.params["speed_m_s"]/length,vy*self.params["speed_m_s"]/length
            self.status="guarded_"+self.reactive.status
        else:
            if state.time_s>=self.next_plan:
                self.path=self.grid.plan(state.position_m,self.mission.goal_m)
                self.next_plan=state.time_s+self.params["replan_period_s"]
                self.plans+=1
            target=None
            recovering=False
            for point in self.path[1:]:
                if hypot(point[0]-state.position_m[0],point[1]-state.position_m[1])>self.params["lookahead_m"]:
                    break
                if self.grid.segment_ok(state.position_m,point,require_free=True):target=point;recovering=False
                elif self.grid.escape_ok(state.position_m,point):target=point;recovering=True
                else:break
            if distance<self.params["lookahead_m"] and self.grid.segment_ok(state.position_m,self.mission.goal_m,True):
                target=self.mission.goal_m
            if target is None and self.grid.cell(state.position_m) in self.grid.blocked:
                target=self.grid.escape_target(state.position_m,self.mission.goal_m)
                recovering=target is not None
            if target is None:
                scan=True;self.status="scan_unknown_or_blocked"
            else:
                tx,ty=target[0]-state.position_m[0],target[1]-state.position_m[1]
                length=hypot(tx,ty)
                if length>.03:
                    speed=min(.2 if recovering else self.params["speed_m_s"],.65*distance)
                    vx,vy=speed*tx/length,speed*ty/length
                self.status="recover_observed_clearance" if recovering else "follow_observed_path"
        vx,vy,changed=self.grid.guard(state.position_m,vx,vy)
        self.guard_events+=int(changed);self.scan_decisions+=int(scan)
        if changed:self.status+="_limited"
        # Both v2 comparators sweep yaw while moving to refresh inter-ray gaps.
        yaw_rate=self.params["scan_yaw_rad_s"] if distance>.15 else 0.0
        vz=max(-.4,min(.4,.8*(self.mission.goal_m[2]-state.position_m[2])))
        return MotionCommand(cos(yaw)*vx+sin(yaw)*vy,-sin(yaw)*vx+cos(yaw)*vy,vz,yaw_rate)

    def diagnostics(self):
        return {"decisions":self.decisions,"range_samples":self.range_samples,"range_values":self.range_samples*10,"map_updates":self.grid.updates,
                "free_cells":len(self.grid.free),"occupied_cells":len(self.grid.occupied),"peak_cells":self.grid.peak_cells,
                "derived_blocked_cells":len(self.grid.blocked),
                "budget_exhausted":self.grid.exhausted,"guard_events":self.guard_events,"scan_decisions":self.scan_decisions,
                "plans":self.plans,"cpu_mean_ms":self.cpu_total_ns/max(1,self.decisions)/1e6,"cpu_max_ms":self.cpu_max_ns/1e6}
