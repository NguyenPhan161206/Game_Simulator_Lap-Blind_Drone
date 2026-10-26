"""Versioned candidate/development and frozen fresh-split protocol for v2."""
import hashlib
import json
import tomllib

from blind_drone.experiments.protocol import verify_lock as verify_v1
from blind_drone.world.geometry import path_certificate
from blind_drone.world.minimal_lab import ROOT, controller_config, load_config, proto_text, world_text
from blind_drone.world.scenarios import MANIFEST as V1_MANIFEST, digest, generate_case

CONFIG = ROOT/"configs/navigation_v2.toml"
MANIFEST = ROOT/"configs/scenarios/observed_v2.json"
LOCK = ROOT/"configs/scenarios/protocol_v2.lock.json"
FILES = ("configs/navigation_v2.toml","configs/scenarios/observed_v2.json",
         "src/blind_drone/observation/range_grid.py","src/blind_drone/navigation/observed.py",
         "src/blind_drone/adapters/webots/drone_v2.py","src/blind_drone/adapters/webots/lab_v2.py",
         "src/blind_drone/experiments/protocol_v2.py","tools/run_navigation_v2.py",
         "simulation/webots/protos/BlindDroneV2.proto","simulation/webots/worlds/observed_v2.wbt")


def load_v2_config():
    c=load_config()
    c["navigation_v2"]=tomllib.loads(CONFIG.read_text())["navigation_v2"]
    return c


def build_manifest():
    spec=tomllib.loads(CONFIG.read_text())
    c=load_config()
    cases=[]
    all_seeds=[s for values in spec["splits"].values() for s in values]
    if len(all_seeds)!=len(set(all_seeds)):raise ValueError("v2 split seed overlap")
    v1={x["geometry_sha256"] for x in json.loads(V1_MANIFEST.read_text())["cases"]}
    for split,seeds in spec["splits"].items():
        for seed in seeds:
            for family in spec["families"]:
                case=generate_case(family,seed,split)
                case["certificate"]=path_certificate(case,c["vehicle"]["body_size_m"])
                if split!="development" and case["geometry_sha256"] in v1:
                    raise ValueError("Fresh split overlaps exposed v1 geometry")
                cases.append(case)
    if len({c["geometry_sha256"] for c in cases})!=len(cases):raise ValueError("v2 duplicate geometry")
    return {"schema_version":2,"name":"observed_grid_v2","cases":cases}


def outputs():
    config=load_v2_config()
    public=controller_config(config)
    public["navigation_v2"]=config["navigation_v2"]
    old=json.dumps(json.dumps(controller_config(config),separators=(",",":")))
    new=json.dumps(json.dumps(public,separators=(",",":")))
    proto=proto_text(config).replace("PROTO BlindDrone [","PROTO BlindDroneV2 [").replace('controller "drone_controller"','controller "drone_v2"')
    world=world_text(config).replace('protos/BlindDrone.proto','protos/BlindDroneV2.proto').replace('DEF DRONE BlindDrone {','DEF DRONE BlindDroneV2 {').replace('controller "lab_supervisor"','controller "lab_v2"').replace(old,new)
    return {ROOT/"simulation/webots/protos/BlindDroneV2.proto":proto,
            ROOT/"simulation/webots/worlds/observed_v2.wbt":world,
            MANIFEST:json.dumps(build_manifest(),indent=2)+"\n"}


def candidate_hashes():
    verify_v1()
    return {"v1_protocol":verify_v1(),"files":{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES}}


def verify_v2():
    current=candidate_hashes()
    if not LOCK.exists():raise ValueError("Freeze v2 before fresh validation/test")
    if json.loads(LOCK.read_text())!=current:raise ValueError("Frozen v2 mismatch; version changes instead of replacing the lock")
    return digest(current)


def select_suite_v2(split,requested=None):
    if split not in {"development","validation","test"}:raise ValueError("Invalid split")
    protocol_hash=verify_v2() if LOCK.exists() or split!="development" else digest(candidate_hashes())
    manifest=json.loads(MANIFEST.read_text())
    cases=[c for c in manifest["cases"] if c["split"]==split and (not requested or c["id"]==requested)]
    if not cases:raise ValueError("No selected v2 case")
    return manifest,cases,protocol_hash
