"""Collect desktop Webots evidence without changing the frozen v1/v2 runtime."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
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
RESPONSIVENESS = ("smooth", "minor_lag", "major_lag", "not_observed")
CONTROL_CHANGES = ("unchanged", "paused", "changed_speed", "both", "unknown")


@contextmanager
def exclusive_session(path=None):
    """One collector per workspace; keep the inode so stale files are harmless."""
    path = path or ROOT / ".local/local-session/active.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("Another local-session collector is active; finish its Webots window and interview first") from error
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def write_json(path, value, *, exclusive=False):
    content = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    with path.open("x" if exclusive else "w", encoding="utf-8") as stream:
        stream.write(content)


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
               WEBOTS_ORIGINAL_LD_LIBRARY_PATH=env.get("LD_LIBRARY_PATH", ""),
               # Match the official Linux launcher's short temp base. Controller
               # Unix sockets can exceed path limits under long CI workspaces.
               WEBOTS_TMPDIR="/tmp", TMPDIR="/tmp",
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


def review(directory, *, quiet=False):
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
        if operator.get("responsiveness") not in RESPONSIVENESS[:-1] and operator.get("responsiveness_notes", "").strip().lower() in {"", "y", "yes", "n", "no"}:
            result["manual_evidence_warnings"].append("Responsiveness note does not describe lag, pauses or speed changes")
    result["files_sha256"] = {str(p.relative_to(directory)): sha(p) for p in sorted(directory.rglob("*"))
                              if p.is_file() and p.name not in {"review.json", "review.md"}}
    write_json(directory / "review.json", result)
    (directory / "review.md").write_text("# Local session review\n\n"
        "GUI/keys require the separate operator record. See session.json, console.log and run/.\n\n"
        "The sim/wall ratio includes startup, shutdown and pauses; it does not establish FPS or hardware realtime.\n\n"
        "```json\n" + json.dumps(result, indent=2, ensure_ascii=False) + "\n```\n")
    if not quiet:
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
    def choice(prompt, choices, labels):
        print(prompt)
        for i, label in enumerate(labels, 1):
            print(f"  {i}. {label}")
        while True:
            answer = input("Chọn số (Enter = chưa quan sát/không rõ): ").strip()
            if not answer:
                return choices[-1]
            if answer in {str(i) for i in range(1, len(choices) + 1)}:
                return choices[int(answer) - 1]

    record["responsiveness"] = choice("Độ phản hồi bạn thực sự quan sát:", RESPONSIVENESS,
        ("Mượt, phản hồi phù hợp", "Có trễ/giật nhẹ", "Trễ/giật nhiều", "Chưa quan sát"))
    record["simulation_control_changes"] = choice("Trong lượt vừa rồi bạn có pause hoặc đổi tốc độ simulation?", CONTROL_CHANGES,
        ("Không thay đổi", "Có pause", "Có đổi tốc độ", "Cả hai", "Không rõ"))
    record["responsiveness_notes"] = input("Mô tả thêm về giật/trễ (có thể để trống nếu đã chọn rõ ở trên): ")
    record["other_notes"] = input("Lỗi/ghi chú khác (có thể để trống): ")
    write_json(directory / "operator.json", record, exclusive=True)
    review(directory)


def evidence_gaps(session, reviewed, operator):
    """Evidence readiness, not automatic proof that a human pressed a physical key."""
    gaps = []
    mode = session.get("mode")
    if mode not in {"manual", "mapped"}:
        return ["Invalid session mode"]
    if session.get("status") != "process_exited" or session.get("exit_code") != 0:
        gaps.append("Simulator did not finish normally")
    if not session.get("source_commit") or not session.get("protocol_sha256"):
        gaps.append("Missing source/protocol identity")
    if session.get("working_tree_dirty") is not False:
        gaps.append("Dirty or unknown source needs a separate code review")
    telemetry = reviewed.get("telemetry", {})
    if telemetry.get("packets", 0) <= 0 or telemetry.get("invalid_lines", 0):
        gaps.append("Missing or malformed telemetry")
    if operator.get("kind") != "operator_self_report":
        gaps.append("Missing operator record")
    required = ["gui_opened", "correct_world_controllers"]
    required += ["key_" + key for key in KEYS] if mode == "manual" else ["motion_seen", "completion_seen"]
    for key in required:
        if operator.get("answers", {}).get(key) != "yes":
            gaps.append("Not confirmed: " + key)
    if operator.get("responsiveness") not in RESPONSIVENESS[:-1]:
        gaps.append("Responsiveness not explicitly described")
    changes = operator.get("simulation_control_changes")
    if changes not in CONTROL_CHANGES[:-1]:
        gaps.append("Pause/speed changes not explicitly recorded")
    if mode == "mapped" and changes != "unchanged":
        gaps.append("Mapped timing requires a run without pause/speed changes")
    if mode == "manual":
        gaps.extend(reviewed.get("manual_evidence_warnings", []))
    else:
        comparison = reviewed.get("comparison", {})
        if not comparison.get("identity_valid") or not comparison.get("same_outcome"):
            gaps.append("Mapped result did not match the frozen reference outcome/identity")
    return gaps


def audit_batch(directory):
    summary = {"kind": "sequential_local_evidence_review", "sessions": {}, "gaps": [],
               "ready_for_review": False, "project_checklist_modified": False,
               "limits": "Operator self-report plus telemetry; no automatic GUI, key-latency or hardware realtime proof"}
    sessions = {}
    for mode in ("manual", "mapped"):
        folder = directory / mode
        if not folder.exists():
            gap = "Chưa khởi chạy; cần hoàn thành bước manual trước" if mode == "mapped" else "Chưa khởi chạy manual"
            summary["sessions"][mode] = {"state": "not_started", "gaps": [gap]}
            summary["gaps"].append(mode + ": " + gap)
            continue
        try:
            session = json.loads((folder / "session.json").read_text())
            reviewed = review(folder, quiet=True)
            operator_path = folder / "operator.json"
            operator = json.loads(operator_path.read_text()) if operator_path.is_file() else {}
            if session.get("mode") != mode:
                raise ValueError("Session mode does not match directory")
            sessions[mode] = session
            gaps = evidence_gaps(session, reviewed, operator)
            summary["sessions"][mode] = {"source_commit": session.get("source_commit"), "gaps": gaps,
                "responsiveness": operator.get("responsiveness"), "review": str(folder / "review.json")}
            summary["gaps"].extend(mode + ": " + gap for gap in gaps)
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            summary["gaps"].append(mode + ": cannot review evidence: " + str(error))
    if len(sessions) == 2:
        manual, mapped = sessions["manual"], sessions["mapped"]
        for key in ("source_commit", "protocol_sha256", "helper_sha256"):
            if not manual.get(key) or manual.get(key) != mapped.get(key):
                summary["gaps"].append("Different/missing identity across sessions: " + key)
        try:
            times = [datetime.fromisoformat(s[k]) for s in (manual, mapped) for k in ("started_utc", "ended_utc")]
            if any(t.utcoffset() is None for t in times) or not times[0] <= times[1] <= times[2] <= times[3]:
                raise ValueError("Sessions overlap or timestamps are invalid")
        except (KeyError, TypeError, ValueError) as error:
            summary["gaps"].append(str(error))
    summary["ready_for_review"] = not summary["gaps"]
    write_json(directory / "acceptance.json", summary)
    print("Acceptance review:", directory / "acceptance.json")
    for gap in summary["gaps"]:
        print("PENDING:", gap)
    return summary


def accept(args):
    if not sys.stdin.isatty():
        raise ValueError("accept requires an interactive desktop terminal for real operator answers")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory = (args.output or ROOT / "artifacts" / ("local-acceptance-" + stamp)).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    print("Acceptance batch:", directory, flush=True)
    print("Một cửa sổ Webots mỗi lần. Manual: chọn vùng 3D; thử W/S A/D T/G Q/E, SPACE, thả phím; R sau khi đã di chuyển. Đóng cửa sổ bằng nút đóng rồi trả lời phiếu.", flush=True)
    for mode, timeout in (("manual", args.manual_timeout), ("mapped", args.mapped_timeout)):
        run_args = argparse.Namespace(mode=mode, output=directory / mode, webots=args.webots,
            software_rendering=args.software_rendering, timeout=timeout, no_interview=False)
        try:
            code = launch(run_args)
        except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, EOFError, KeyboardInterrupt):
            audit_batch(directory)
            raise
        folder = directory / mode
        operator_path = folder / "operator.json"
        operator = json.loads(operator_path.read_text()) if operator_path.is_file() else {}
        gaps = evidence_gaps(json.loads((folder / "session.json").read_text()), review(folder, quiet=True), operator)
        if code or gaps:
            audit_batch(directory)
            print("Bước này còn thiếu bằng chứng; xem PENDING, không chuyển sang lượt tiếp theo.")
            return 1
    complete = audit_batch(directory)["ready_for_review"]
    if complete:
        print("Đã đủ dữ liệu và phiếu để review checklist; không tự đánh dấu checklist dự án.")
    return 0 if complete else 1


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
    for key in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "WEBOTS_TMPDIR"):
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
    p = sub.add_parser("accept", help="Interactive manual then mapped, with evidence gates")
    p.add_argument("--webots")
    p.add_argument("--output", type=Path)
    p.add_argument("--software-rendering", action="store_true")
    p.add_argument("--manual-timeout", type=float, default=600)
    p.add_argument("--mapped-timeout", type=float, default=180)
    for name in ("review", "attest", "audit-batch"):
        sub.add_parser(name).add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "review":
            review(args.directory.resolve())
            return 0
        if args.mode == "attest":
            attest(args.directory.resolve())
            return 0
        if args.mode == "audit-batch":
            return 0 if audit_batch(args.directory.resolve())["ready_for_review"] else 1
        if args.mode == "accept":
            if any(not isfinite(t) or t <= 0 for t in (args.manual_timeout, args.mapped_timeout)):
                parser.error("timeouts must be finite and positive")
            with exclusive_session():
                return accept(args)
        if not isfinite(args.timeout) or args.timeout <= 0:
            parser.error("--timeout must be finite and positive")
        with exclusive_session():
            return launch(args)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, EOFError, KeyboardInterrupt) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
