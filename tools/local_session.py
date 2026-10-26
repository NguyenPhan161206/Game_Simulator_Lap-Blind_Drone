"""Collect desktop Webots evidence without changing the frozen v1/v2 runtime."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from math import dist, isfinite
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from blind_drone.experiments.protocol_v2 import select_suite_v2, verify_v2
from run_webots import find_webots

CASE = "development-u_trap-s21001"
REFERENCE = ROOT / "docs/research/2026-10-26-navigation-v2.json"
KEYS = ("W", "S", "A", "D", "T", "G", "Q", "E", "SPACE", "release", "R")


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def git(*args):
    r = subprocess.run(["bash", str(ROOT / "tools/git.sh"), *args], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or "Cannot record source revision")
    return r.stdout.strip()


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def desktop_environment(executable, software):
    home = Path(executable).parent
    binary = home / "bin/webots-bin"
    if not binary.is_file():
        raise ValueError("Specify the R2025a webots wrapper path with --webots; bin/webots-bin must exist")
    version_file = home / "resources/version.txt"
    if not version_file.is_file() or version_file.read_text().strip() != "R2025a":
        raise ValueError("This acceptance run requires Webots R2025a (resources/version.txt)")
    env = os.environ.copy()
    # A desktop run must not inherit experiment/CI identities from another run.
    for key in list(env):
        if key.startswith("BLIND_DRONE_") or key in {"GITHUB_SHA", "GITHUB_RUN_ID"}:
            env.pop(key)
    env.update(WEBOTS_HOME=str(home), QT_QPA_PLATFORM="xcb", PYTHONUNBUFFERED="1",
               LD_LIBRARY_PATH=str(home / "lib/webots") +
               (":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else ""))
    if software:
        env["LIBGL_ALWAYS_SOFTWARE"] = "1"
    return str(binary), env


def compare_mapped(report, session, reference):
    """Strict identity gate, then diagnostic deltas; this is not a new protocol."""
    baseline = next(r for r in reference["reports"] if r["split"] == "development")
    if not isinstance(report, dict):
        return {"identity_valid": False, "errors": ["result must be an object"], "classification": "invalid_evidence"}
    checks = report.get("checks")
    checks_valid = (isinstance(checks, dict) and bool(checks) and
                    all(isinstance(c, dict) and c.get("passed") is True for c in checks.values()))
    errors = []
    if session.get("exit_code") != 0 or session.get("status") != "process_exited":
        errors.append("process failed, interrupted or timed out")
    if report.get("status") != "passed" or not checks_valid:
        errors.append("result/checks did not pass")
    for key in ("protocol_sha256", "manifest_sha256", "webots_version", "algorithm_version"):
        if report.get(key) != baseline[key]:
            errors.append("mismatch: " + key)
    if report.get("protocol_sha256") != session.get("protocol_sha256"):
        errors.append("session/result protocol mismatch")
    if report.get("source_commit") != session.get("source_commit"):
        errors.append("session/result source mismatch")
    if report.get("working_tree_dirty") != session.get("working_tree_dirty"):
        errors.append("session/result dirty-state mismatch")
    if report.get("split") != "development" or report.get("protocol_frozen") is not True:
        errors.append("wrong split or unfrozen protocol")
    episodes = report.get("episodes", [])
    if not isinstance(episodes, list) or any(not isinstance(e, dict) for e in episodes):
        return {"identity_valid": False, "errors": ["malformed episodes"], "classification": "invalid_evidence"}
    target = [e for e in episodes if e.get("case_id") == CASE and e.get("policy") == "mapped"]
    if len(episodes) != 1 or len(target) != 1:
        errors.append("expected exactly one mapped development U episode")
    if errors:
        return {"identity_valid": False, "errors": errors, "classification": "invalid_evidence"}
    local = target[0]
    expected = next(e for e in baseline["episodes"] if e["case_id"] == CASE and e["policy"] == "mapped")
    if local.get("geometry_sha256") != expected["geometry_sha256"]:
        return {"identity_valid": False, "errors": ["geometry mismatch"], "classification": "invalid_evidence"}
    scalar = ("elapsed_s", "path_length_m", "final_distance_m", "final_speed_m_s", "contact_count")
    try:
        deltas = {k: float(local[k]) - float(expected[k]) for k in scalar}
        deltas["final_position_distance_m"] = dist(local["final_position_m"], expected["final_position_m"])
        deltas["initial_position_distance_m"] = dist(local["initial_position_m"], expected["initial_position_m"])
        deltas["initial_yaw_rad"] = float(local["initial_yaw_rad"]) - float(expected["initial_yaw_rad"])
        if not all(isfinite(v) for v in deltas.values()):
            raise ValueError("non-finite delta")
    except (KeyError, TypeError, ValueError) as error:
        return {"identity_valid": False, "errors": [str(error)], "classification": "invalid_evidence"}
    same = local.get("outcome") == expected["outcome"]
    return {"identity_valid": True, "ci_url": reference["ci_url"], "ci_source": reference["source_commit"],
            "local_outcome": local.get("outcome"), "ci_outcome": expected["outcome"],
            "same_outcome": same, "local": {k: local[k] for k in scalar},
            "ci": {k: expected[k] for k in scalar}, "local_minus_ci": deltas,
            "classification": "outcome_mismatch" if not same else
            "numerically_close" if all(abs(v) <= 1e-6 for v in deltas.values()) else "numeric_difference_review_required",
            "note": "1e-6 is a diagnostic label, not a research acceptance threshold; no cause inferred",
            "policy_cpu": local.get("diagnostics", {})}


def review(directory):
    session = json.loads((directory / "session.json").read_text())
    run = directory / "run"
    report_path = run / "result.json"
    result = {"mode": session["mode"], "process_exit_code": session.get("exit_code"),
              "wall_s_including_startup_shutdown": session.get("wall_s"),
              "gui_verified_automatically": False,
              "operator_record_present": (directory / "operator.json").is_file()}
    if session["mode"] == "mapped":
        if report_path.is_file():
            try:
                report = json.loads(report_path.read_text())
                result["comparison"] = compare_mapped(report, session, json.loads(REFERENCE.read_text()))
            except (ValueError, TypeError) as error:
                report = None
                result["comparison"] = {"identity_valid": False, "classification": "invalid_evidence", "errors": [str(error)]}
            # Includes warmup, startup/shutdown and possible user pauses. Not an FPS measurement.
            episodes = report.get("episodes", []) if isinstance(report, dict) else []
            if result["comparison"].get("identity_valid") and len(episodes) == 1 and session.get("wall_s", 0) > 0:
                simulated = episodes[0].get("elapsed_s", 0) + report.get("specification", {}).get("evaluation", {}).get("warmup_s", 0)
                result["sim_s_over_total_wall_s"] = simulated / session["wall_s"]
        else:
            result["comparison"] = {"identity_valid": False, "classification": "missing_result"}
    telemetry = run / "telemetry.jsonl"
    if telemetry.is_file():
        count = invalid = 0
        signs = {k: set() for k in ("forward_m_s", "left_m_s", "up_m_s", "yaw_rate_rad_s")}
        first = last = None
        with telemetry.open() as stream:
            for line in stream:
                try:
                    packet = json.loads(line)
                    first = packet["time_s"] if first is None else first
                    last = packet["time_s"]
                    for key, value in packet.get("navigation", {}).get("command", {}).items():
                        if key in signs and abs(value) > 1e-8:
                            signs[key].add("positive" if value > 0 else "negative")
                    count += 1
                except (ValueError, KeyError, TypeError):
                    invalid += 1
        result["telemetry"] = {"packets": count, "invalid_lines": invalid, "first_sim_s": first,
                               "last_sim_s": last, "command_signs": {k: sorted(v) for k, v in signs.items()},
                               "note": "Commands support motion evidence; they do not prove physical key presses/reset or GUI responsiveness"}
    if session["mode"] == "manual" and result["operator_record_present"]:
        operator = json.loads((directory / "operator.json").read_text())
        signs = result.get("telemetry", {}).get("command_signs", {})
        requirements = {"W": ("forward_m_s", "positive"), "S": ("forward_m_s", "negative"),
                        "A": ("left_m_s", "positive"), "D": ("left_m_s", "negative"),
                        "T": ("up_m_s", "positive"), "G": ("up_m_s", "negative"),
                        "Q": ("yaw_rate_rad_s", "positive"), "E": ("yaw_rate_rad_s", "negative")}
        result["manual_evidence_warnings"] = [
            "Operator reports " + key + " passed, but no matching sampled command; check focus/run identity or brief key presses"
            for key, (axis, sign) in requirements.items()
            if operator.get("answers", {}).get("key_" + key) == "yes" and sign not in signs.get(axis, [])]
        if operator.get("responsiveness_notes", "").strip().lower() in {"", "y", "yes", "n", "no"}:
            result["manual_evidence_warnings"].append("Responsiveness note does not describe lag, pauses or speed changes")
    result["files_sha256"] = {str(p.relative_to(directory)): sha(p) for p in sorted(directory.rglob("*"))
                              if p.is_file() and p.name not in {"review.json", "review.md"}}
    write_json(directory / "review.json", result)
    (directory / "review.md").write_text("# Local session review\n\n"
        "GUI/keys require the separate operator record. See session.json, console.log and run/.\n\n"
        "The sim/wall ratio includes startup, shutdown and pauses; it does not establish FPS or hardware realtime.\n\n"
        "```json\n" + json.dumps(result, indent=2, ensure_ascii=False) + "\n```\n")
    print("Review:", directory / "review.md")
    for warning in result.get("manual_evidence_warnings", []):
        print("REVIEW REQUIRED:", warning)
    return result


def attest(directory):
    if (directory / "operator.json").exists():
        raise ValueError("operator.json already exists; preserve the original operator record")
    session = json.loads((directory / "session.json").read_text())
    prompts = {"gui_opened": "Đã nhìn thấy cửa sổ Webots?",
               "correct_world_controllers": "Đã kiểm tra đúng world/controller ghi trong session.json?"}
    if session["mode"] == "manual":
        prompts.update({"key_" + key: "Đã trực tiếp thử và quan sát đúng tác dụng của " + key + "?" for key in KEYS})
    else:
        prompts.update(motion_seen="Đã quan sát drone chuyển động?", completion_seen="Đã thấy kết thúc ca mapped?")
    record = {"recorded_utc": datetime.now(timezone.utc).isoformat(), "kind": "operator_self_report", "answers": {}}
    print("Chỉ ghi việc bạn đã thực sự làm trong lượt này. y=đạt, n=không đạt, Enter=chưa thử.")
    for key, prompt in prompts.items():
        while True:
            answer = input(prompt + " [y/n/Enter]: ").strip().lower()
            if answer in {"y", "n", ""}:
                record["answers"][key] = {"y": "yes", "n": "no", "": "untested"}[answer]
                break
    record["responsiveness_notes"] = input("Độ mượt, trễ phím, pause/chỉnh speed trong lượt; chưa quan sát thì ghi rõ: ")
    record["other_notes"] = input("Lỗi/ghi chú khác (có thể để trống): ")
    write_json(directory / "operator.json", record)
    review(directory)


def launch(args):
    protocol = verify_v2()  # Includes the frozen v1 check.
    if args.mode == "mapped":
        select_suite_v2("development", CASE)
    check = "build_navigation_v2.py" if args.mode == "mapped" else "build_lab.py"
    subprocess.run([sys.executable, str(ROOT / "tools" / check), "--check"], cwd=ROOT, check=True)
    executable = find_webots(args.webots)
    if not executable:
        raise ValueError("Webots missing; run python3 tools/install_webots.py")
    binary, env = desktop_environment(executable, args.software_rendering)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory = (args.output or ROOT / "artifacts" / ("local-" + args.mode + "-" + stamp)).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    run = directory / "run"
    run.mkdir()
    world = "observed_v2.wbt" if args.mode == "mapped" else "minimal_lab.wbt"
    session = {"schema_version": 1, "mode": args.mode, "started_utc": datetime.now(timezone.utc).isoformat(),
               "source_commit": git("rev-parse", "HEAD"), "working_tree_dirty": bool(git("status", "--porcelain")),
               "protocol_sha256": protocol, "world": world,
               "controllers": ["drone_v2", "lab_v2"] if args.mode == "mapped" else ["drone_controller", "lab_supervisor"],
               "os": platform.platform(), "distribution": platform.freedesktop_os_release().get("PRETTY_NAME"),
               "launcher_python": platform.python_version(), "architecture": platform.machine(),
               "webots_version_file": "R2025a", "webots_binary_sha256": sha(Path(binary)),
               "logical_cpus": os.cpu_count(), "display": env.get("DISPLAY"),
               "wayland_display": env.get("WAYLAND_DISPLAY"), "qt_platform": "xcb",
               "software_rendering": env.get("LIBGL_ALWAYS_SOFTWARE") == "1", "realtime_requested": True,
               "rendering_enabled": True, "case": CASE if args.mode == "mapped" else None,
               "status": "starting"}
    env.update(BLIND_DRONE_MODE="navigation" if args.mode == "mapped" else "manual",
               BLIND_DRONE_OUTPUT=str(run), BLIND_DRONE_SOURCE_COMMIT=session["source_commit"],
               BLIND_DRONE_DIRTY=str(session["working_tree_dirty"]).lower(),
               XDG_CONFIG_HOME=str(ROOT / ".local/local-session/config"),
               XDG_CACHE_HOME=str(ROOT / ".local/local-session/cache"))
    if args.mode == "mapped":
        env.update(BLIND_DRONE_POLICY="mapped", BLIND_DRONE_SPLIT="development",
                   BLIND_DRONE_CASE=CASE, BLIND_DRONE_RENDERING="true")
    for key in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
        Path(env[key]).mkdir(parents=True, exist_ok=True)
    command = [binary, "--batch", "--stdout", "--stderr", "--mode=realtime",
               str(ROOT / "simulation/webots/worlds" / world)]
    session["command"] = command
    session["helper_sha256"] = sha(Path(__file__))
    write_json(directory / "session.json", session)
    print("Session:", directory, flush=True)
    print("Manual: focus 3D; test W/S A/D T/G Q/E SPACE release R; close Webots when finished." if args.mode == "manual"
          else "Mapped: observe movement/completion; do not press movement/reset or change simulation speed.", flush=True)
    started = time.monotonic()
    with (directory / "console.log").open("w") as log:
        try:
            proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, errors="replace", start_new_session=True)
        except OSError as error:
            session.update(status="launch_error", error=str(error), exit_code=None,
                           wall_s=time.monotonic() - started)
            write_json(directory / "session.json", session)
            log.write(str(error) + "\n")
            raise

        def tee():
            for line in proc.stdout:
                log.write(line)
                log.flush()
                print(line, end="", flush=True)

        reader = threading.Thread(target=tee, daemon=True)
        reader.start()
        try:
            code = proc.wait(timeout=args.timeout)
            session["status"] = "process_exited"
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
            session["status"] = "timeout" if isinstance(error, subprocess.TimeoutExpired) else "interrupted"
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            code = proc.returncode
        reader.join(timeout=5)
    session.update(exit_code=code, wall_s=time.monotonic() - started, ended_utc=datetime.now(timezone.utc).isoformat())
    write_json(directory / "session.json", session)
    result = review(directory)
    if not args.no_interview and sys.stdin.isatty():
        attest(directory)
    if code or session["status"] != "process_exited":
        return 1
    if args.mode == "mapped":
        comparison = result["comparison"]
        return 0 if comparison.get("identity_valid") and comparison.get("same_outcome") else 1
    return 0 if result.get("telemetry", {}).get("packets", 0) > 0 else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ("manual", "mapped"):
        p = sub.add_parser(name)
        p.add_argument("--webots")
        p.add_argument("--output", type=Path)
        p.add_argument("--software-rendering", action="store_true")
        p.add_argument("--timeout", type=float, default=600 if name == "manual" else 180)
        p.add_argument("--no-interview", action="store_true")
    for name in ("review", "attest"):
        sub.add_parser(name).add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "review":
            review(args.directory.resolve())
            return 0
        if args.mode == "attest":
            attest(args.directory.resolve())
            return 0
        if not isfinite(args.timeout) or args.timeout <= 0:
            parser.error("--timeout must be finite and positive")
        return launch(args)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, EOFError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
