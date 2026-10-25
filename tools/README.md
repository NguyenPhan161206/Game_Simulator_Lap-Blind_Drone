# Development tools

- `python3 tools/check_scaffold.py`: validate layout, TOML, declared information restrictions and local Markdown links.
- `python3 tools/run_codex.py --dry-run`: preview the portable Codex invocation.
- `python3 tools/run_codex.py`: start Codex with repository options and the existing user/host permissions.
- `bash tools/git.sh status --short --branch`: normal Git or the already-created local metadata fallback.

These tools do not install Webots, train a model, alter global agent settings or automatically publish changes.
