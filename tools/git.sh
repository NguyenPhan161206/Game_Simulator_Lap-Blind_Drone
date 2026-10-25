#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$project_root/.local/git/HEAD" ]]; then
    cd -- "$project_root"
    exec git --git-dir="$project_root/.local/git" --work-tree="$project_root" "$@"
fi
if git -C "$project_root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    exec git -C "$project_root" "$@"
fi
printf '%s\n' "No Git repository found. Use a normal clone, or initialize an allowed local metadata directory explicitly." >&2
exit 1
