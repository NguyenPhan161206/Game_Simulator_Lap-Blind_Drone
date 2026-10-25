"""Validate the foundation only; this does not execute a simulator."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys
import tomllib
from urllib.parse import unquote

EXCLUDED = {".git", ".codex", ".agents", ".aws", ".local", ".venv", "venv",
            "__pycache__", "node_modules", "build", "dist", ".pytest_cache"}
EXPECTED_MODULES = {"contracts", "world", "vehicle", "sensors", "observation",
                    "navigation", "control", "evaluation", "experiments",
                    "visualization", "webots_adapter", "training"}
REQUIRED = [
    "README.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md", "THIRD_PARTY.md",
    "agents/README.md", "configs/agents/codex.toml",
    "docs/architecture/system.md", "docs/architecture/data-contracts.md",
    "docs/architecture/repository.md", "docs/decisions/0001-foundation.md",
    "docs/01-y-tuong-va-quyet-dinh.md", "docs/02-du-thao-thi-nghiem-muc-b.md",
    "simulation/webots/README.md", ".github/workflows/scaffold.yml",
    "src/blind_drone/__init__.py", "tools/run_codex.py", "tools/git.sh",
]
PRESETS = [
    "configs/environments/level_b.toml", "configs/vehicles/drone.toml",
    "configs/sensors/local_ranges.toml", "configs/experiments/level_b.toml",
]


def source_files(root: Path):
    for directory, subdirs, names in os.walk(root):
        subdirs[:] = [name for name in subdirs if name not in EXCLUDED]
        for name in names:
            yield Path(directory) / name


def validate(root: Path) -> tuple[list[str], int]:
    errors: list[str] = []
    def require(condition: bool, message: str):
        if not condition:
            errors.append(message)

    for relative in REQUIRED:
        require((root / relative).is_file(), f"Missing required file: {relative}")

    parsed = {}
    files = list(source_files(root))
    for path in files:
        if path.suffix not in {".md", ".toml", ".py", ".sh", ".yml"}:
            continue
        relative = path.relative_to(root)
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeError as error:
            errors.append(f"{relative}: invalid UTF-8: {error}")
            continue
        require(content.endswith("\n"), f"{relative}: missing final newline")
        if path.suffix == ".toml":
            try:
                parsed[str(relative)] = tomllib.loads(content)
            except tomllib.TOMLDecodeError as error:
                errors.append(f"{relative}: invalid TOML: {error}")
        if path.suffix == ".md":
            for target in re.findall(r"\]\(([^)]+)\)", content):
                if target.startswith(("https://", "http://", "mailto:", "#")):
                    continue
                target = unquote(target.split("#", 1)[0])
                destination = (path.parent / target).resolve()
                require(destination.is_relative_to(root),
                        f"{relative}: link escapes project: {target}")
                require(destination.exists(), f"{relative}: broken local link: {target}")

    project = parsed.get("configs/project.toml", {})
    require(project.get("task_level") == "B", "Foundation must declare task level B")
    require(project.get("vehicle_count") == 1, "Foundation must declare one vehicle")
    require(project.get("runtime_camera_enabled") is False, "Runtime camera must be disabled")
    require(project.get("runtime_privileged_state_enabled") is False,
            "Runtime privileged state must be disabled")
    modules = project.get("modules", {})
    require(set(modules) == EXPECTED_MODULES, "Module manifest does not match architecture")
    for name, relative in modules.items():
        destination = (root / relative).resolve()
        require(destination.is_relative_to(root), f"Module {name} escapes the project")
        require((destination / "README.md").is_file(), f"Module {name} lacks a responsibility README")

    for relative in PRESETS:
        preset = parsed.get(relative, {})
        require(preset.get("status") == "draft", f"{relative}: expected draft status")
        require(preset.get("runtime_ready") is False, f"{relative}: scaffold preset cannot be runnable")
        require(bool(preset.get("pending")), f"{relative}: record unresolved parameters")
    sensors = parsed.get("configs/sensors/local_ranges.toml", {})
    require(sensors.get("camera_enabled") is False, "Sensor preset must exclude cameras")
    require(sensors.get("privileged_state_enabled") is False, "Sensor preset must exclude privileged state")
    require(sensors.get("physical_radar_claim") is False, "Geometric sensor cannot claim physical radar")
    experiment = parsed.get("configs/experiments/level_b.toml", {})
    require(experiment.get("runtime_camera_enabled") is False, "Experiment runtime camera must be disabled")
    require(experiment.get("runtime_privileged_state_enabled") is False,
            "Experiment must exclude runtime privileged state")
    codex = parsed.get("configs/agents/codex.toml", {})
    require(set(codex) == {"project_doc_max_bytes", "project_root_markers"},
            "Portable Codex config must contain only supported project discovery options")
    require(type(codex.get("project_doc_max_bytes")) is int and
            codex.get("project_doc_max_bytes", 0) >= (root / "AGENTS.md").stat().st_size
            if (root / "AGENTS.md").exists() else False,
            "AGENTS.md must fit within the Codex document budget")
    return errors, len(parsed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    errors, count = validate(root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: foundation layout, {count} TOML files, declared information boundaries and local links")
    print("Scope: scaffold validation only; simulator execution requires the separate Webots smoke check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
