"""Open the lab or run real-Webots smoke checks; missing Webots is an error."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def find_webots(explicit=None):
    candidates = [explicit, os.environ.get("WEBOTS_EXECUTABLE"),
                  str(ROOT / ".local/webots-R2025a/webots/webots"), shutil.which("webots")]
    return next((str(Path(value).resolve()) for value in candidates if value and Path(value).is_file()), None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--webots")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--software-rendering", action="store_true")
    args = parser.parse_args()
    executable = find_webots(args.webots)
    if not executable:
        print("Webots R2025a not found. Run python3 tools/install_webots.py or specify --webots.", file=sys.stderr)
        return 2
    check = subprocess.run([sys.executable, str(ROOT / "tools/build_lab.py"), "--check"], cwd=ROOT)
    if check.returncode:
        return check.returncode
    mode = "smoke" if args.smoke else "manual"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = (args.output or ROOT / "artifacts" / f"webots-{mode}-{stamp}").resolve()
    if (output / "result.json").exists():
        print("Use a fresh output directory; an old result must not be mistaken for this run.", file=sys.stderr)
        return 2
    output.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({"BLIND_DRONE_MODE": mode, "BLIND_DRONE_OUTPUT": str(output),
                "XDG_CONFIG_HOME": str(ROOT / ".local/webots-user/config"),
                "XDG_CACHE_HOME": str(ROOT / ".local/webots-user/cache"),
                "PYTHONUNBUFFERED": "1"})
    if args.software_rendering:
        env["LIBGL_ALWAYS_SOFTWARE"] = "1"
    for variable in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
        Path(env[variable]).mkdir(parents=True, exist_ok=True)
    command = [executable, "--batch", "--stdout", "--stderr", "--mode=" + ("fast" if args.smoke else "realtime")]
    command.append(str(ROOT / "simulation/webots/worlds/minimal_lab.wbt"))
    print("Output:", output, flush=True)
    print("Launching:", " ".join(command), flush=True)
    if not args.smoke:
        return subprocess.call(command, cwd=ROOT, env=env)
    with (output / "console.log").open("w", encoding="utf-8") as log:
        try:
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            returncode = process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            print("Webots exceeded wall-clock deadline; see console.log.", file=sys.stderr)
            return 1
    print((output / "console.log").read_text(encoding="utf-8", errors="replace"))
    result_file = output / "result.json"
    if returncode or not result_file.exists():
        print("Webots exit code:", returncode, "; output files:", sorted(path.name for path in output.iterdir()), file=sys.stderr)
        print("Webots failed or produced no result; simulation checks have not passed.", file=sys.stderr)
        return 1
    result = json.loads(result_file.read_text())
    if result.get("status") != "passed" or not result.get("checks") or not all(item["passed"] for item in result["checks"].values()):
        print("Simulator checks failed:", result, file=sys.stderr)
        return 1
    print("PASS: real Webots smoke checks:", ", ".join(result["checks"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
