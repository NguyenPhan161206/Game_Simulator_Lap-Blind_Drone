"""Deterministic, privileged fixture generation; no runtime drone imports."""
import hashlib
import json
from math import pi
from pathlib import Path
import tomllib

from blind_drone.world.geometry import path_certificate
from blind_drone.world.minimal_lab import ROOT, load_config

SPEC = ROOT / "configs/scenario_suite_v1.toml"
MANIFEST = ROOT / "configs/scenarios/seeded_v1.json"


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def generate_case(family, seed, split):
    def sample(name,low,high):
        bits = hashlib.sha256(f"seeded_v1:{family}:{seed}:{name}".encode()).digest()
        return low+(high-low)*int.from_bytes(bits[:8],"big")/(2**64)
    start = [sample("start_x",-5.6,-4.7),sample("start_y",-.2,.2),1.5]
    goal = [sample("goal_x",4.7,5.6),sample("goal_y",-.2,.2),1.5]
    obstacles = []
    def block(x,y,sx,sy):
        return {"center_m":[x,y,1.5],"size_m":[sx,sy,3.0]}
    if family == "single_block":
        obstacles = [block(sample("x",-.5,.5),sample("y",-.3,.3),sample("width",.6,1.1),sample("length",3,4))]
    elif family == "staggered_blocks":
        obstacles = [block(-1.3,sample("y1",-.4,.4),.8,2.5),block(2.0,sample("y2",1.2,1.6),.8,2.7)]
    elif family == "narrow_gap":
        gap = sample("gap",1.4,1.8)
        obstacles = [block(0,sign*(gap/2+2),1,4) for sign in (-1,1)]
    elif family == "u_trap":
        start = [sample("inside_x",-1.7,-1.3),sample("inside_y",-.3,.3),1.5]
        length = sample("u_length",3.8,4.2)
        obstacles = [block(-1,sign*2,length,.5) for sign in (-1,1)] + [block(-1+length/2,0,.5,4.5)]
    elif family == "blocked_goal":
        goal = [0,0,1.5]
        obstacles = [block(0,0,2,2)]
    elif family != "empty":
        raise ValueError("Unknown scenario family")
    quarter = min(3,int(sample("quarter",0,4)))
    mirror = -1 if sample("mirror",0,1) < .5 else 1
    tx,ty = sample("tx",-.7,.7),sample("ty",-.7,.7)
    def transform(p):
        x,y,z = p
        y *= mirror
        for _ in range(quarter):
            x,y = -y,x
        return [round(x+tx,6),round(y+ty,6),z]
    for obstacle in obstacles:
        obstacle["center_m"] = transform(obstacle["center_m"])
        if quarter%2:
            sx,sy,sz = obstacle["size_m"]
            obstacle["size_m"] = [round(sy,6),round(sx,6),sz]
        else:
            obstacle["size_m"] = [round(v,6) for v in obstacle["size_m"]]
    case = {"id":f"{split}-{family}-s{seed}","family":family,"seed":seed,"split":split,
            "feasible":family!="blocked_goal","start_m":transform(start),"goal_m":transform(goal),
            "start_yaw_rad":round(sample("yaw",-pi,pi),8),"obstacles":obstacles}
    case["geometry_sha256"] = digest({k:case[k] for k in ("start_m","goal_m","obstacles")})
    return case


def build_manifest():
    specification = tomllib.loads(SPEC.read_text())
    seeds = [seed for values in specification["splits"].values() for seed in values]
    if len(seeds) != len(set(seeds)):
        raise ValueError("Seed overlap between splits")
    cases = []
    body = load_config()["vehicle"]["body_size_m"]
    for split,values in specification["splits"].items():
        for seed in values:
            for family in specification["families"]:
                case = generate_case(family,seed,split)
                case["certificate"] = path_certificate(case,body,specification["reference_step_m"],specification["reference_margin_m"],specification["reference_bounds_m"])
                cases.append(case)
    if len({c["geometry_sha256"] for c in cases}) != len(cases):
        raise ValueError("Duplicate geometry across suite")
    return {"schema_version":1,"name":specification["name"],"generator_version":specification["generator_version"],
            "specification":specification,"cases":cases}
