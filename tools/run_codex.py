"""Launch Codex with portable, non-permission project options."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_KEYS = {"project_doc_max_bytes", "project_root_markers"}


def main() -> int:
    arguments = sys.argv[1:]
    dry_run = "--dry-run" in arguments
    if dry_run:
        arguments.remove("--dry-run")
    if arguments[:1] == ["--"]:
        arguments = arguments[1:]
    options = tomllib.loads((ROOT / "configs/agents/codex.toml").read_text(encoding="utf-8"))
    unexpected = set(options) - ALLOWED_KEYS
    if unexpected:
        raise SystemExit(f"Unsupported project option(s): {sorted(unexpected)}")
    command = ["codex", "--cd", str(ROOT)]
    for key, value in options.items():
        command.extend(["--config", f"{key}={json.dumps(value, ensure_ascii=False)}"])
    command.extend(arguments)
    if dry_run:
        print(shlex.join(command))
        return 0
    if shutil.which("codex") is None:
        raise SystemExit("Codex CLI is not installed. AGENTS.md remains usable by other agents.")
    os.execvp(command[0], command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
