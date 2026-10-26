"""Run v2 candidate development or frozen evaluation in real Webots."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from blind_drone.experiments.protocol_v2 import select_suite_v2
from run_webots import find_webots


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--split",choices=("development","validation","test"),default="development")
    p.add_argument("--policy",choices=("all","reactive","guarded","mapped"),default="all")
    p.add_argument("--case");p.add_argument("--output",type=Path);p.add_argument("--webots")
    p.add_argument("--timeout",type=float,default=900);p.add_argument("--realtime",action="store_true")
    p.add_argument("--software-rendering",action="store_true")
    args=p.parse_args()
    try:select_suite_v2(args.split,args.case)
    except (ValueError,OSError) as error:print(error,file=sys.stderr);return 2
    executable=find_webots(args.webots)
    if not executable:print("Webots missing; run python3 tools/install_webots.py",file=sys.stderr);return 2
    if subprocess.call([sys.executable,str(ROOT/"tools/build_navigation_v2.py"),"--check"],cwd=ROOT):return 2
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output=(args.output or ROOT/f"artifacts/navigation-v2-{args.split}-{stamp}").resolve()
    if output.exists():print("Use a fresh output directory",file=sys.stderr);return 2
    output.mkdir(parents=True)
    env=os.environ.copy()
    env.update({"BLIND_DRONE_MODE":"navigation","BLIND_DRONE_OUTPUT":str(output),"BLIND_DRONE_POLICY":args.policy,
                "BLIND_DRONE_SPLIT":args.split,"PYTHONUNBUFFERED":"1",
                "XDG_CONFIG_HOME":str(ROOT/".local/webots-v2/config"),"XDG_CACHE_HOME":str(ROOT/".local/webots-v2/cache")})
    for key in ("XDG_CONFIG_HOME","XDG_CACHE_HOME"):Path(env[key]).mkdir(parents=True,exist_ok=True)
    env.pop("BLIND_DRONE_CASE",None)
    if args.case:env["BLIND_DRONE_CASE"]=args.case
    for command,key in ((["rev-parse","HEAD"],"BLIND_DRONE_SOURCE_COMMIT"),(["status","--porcelain"],"BLIND_DRONE_DIRTY")):
        r=subprocess.run(["bash",str(ROOT/"tools/git.sh"),*command],cwd=ROOT,capture_output=True,text=True)
        env[key]=(r.stdout.strip() if r.returncode==0 else "unknown") if key.endswith("COMMIT") else str(bool(r.returncode or r.stdout.strip())).lower()
    if args.software_rendering:env["LIBGL_ALWAYS_SOFTWARE"]="1"
    # Direct executable avoids the upstream shell wrapper creating desktop files
    # outside the workspace. Reproduce its library/X11 setup explicitly.
    home=Path(executable).parent
    binary=home/"bin/webots-bin"
    if binary.exists():
        executable=str(binary);env["WEBOTS_HOME"]=str(home)
        env["LD_LIBRARY_PATH"]=str(home/"lib/webots")+(":"+env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
        env["QT_QPA_PLATFORM"]="xcb"
    command=[executable,"--batch","--stdout","--stderr","--mode="+("realtime" if args.realtime else "fast"),str(ROOT/"simulation/webots/worlds/observed_v2.wbt")]
    print("Output:",output,flush=True)
    with (output/"console.log").open("w") as log:
        proc=subprocess.Popen(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:code=proc.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGTERM)
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
            print("Webots timeout; inspect console.log",file=sys.stderr);return 1
    print((output/"console.log").read_text(errors="replace"))
    result_path=output/"result.json"
    if code or not result_path.exists():print("No valid simulator result; exit",code,file=sys.stderr);return 1
    result=json.loads(result_path.read_text())
    if result.get("status")!="passed" or not result.get("checks") or not all(c["passed"] for c in result["checks"].values()):return 1
    print("PASS: v2 integration; all navigation outcomes retained")
    return 0


if __name__=="__main__":raise SystemExit(main())
