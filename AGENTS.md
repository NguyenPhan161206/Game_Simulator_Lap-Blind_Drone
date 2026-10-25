# Project instructions for all coding agents

## Start here
- Read README.md, docs/architecture/system.md, docs/architecture/data-contracts.md, and docs/decisions/0001-foundation.md before changing architecture.
- Read docs/01-y-tuong-va-quyet-dinh.md for accepted intent. docs/02-du-thao-thi-nghiem-muc-b.md contains proposals, not approved numeric requirements.
- Communicate with the user in Vietnamese. Keep code identifiers and technical interfaces in English.
- Preserve existing work. Inspect Git status and relevant diffs before edits. If normal Git is unavailable here, read docs/development.md.
- Continue authorized work without repeatedly asking for approval. State assumptions and distinguish accepted decisions from proposals.
- Delegate only when the user or a higher-priority instruction explicitly authorizes delegation.

## Project boundaries
- Current milestone: repository foundation, architecture, configuration and development tooling.
- First research task: one simulated drone reaches a supplied goal while avoiding static obstacles (level B).
- Webots is the first simulator to evaluate. Its installation, world, controller and training are not implemented by this scaffold.
- Runtime navigation must use camera-free observations. Training-only camera supervision is optional and must stay outside the deployed observation path.
- Ground truth belongs to world generation, evaluation and observer visualization. Never pass hidden obstacles, object IDs/tags, full-world state or oracle paths into the evaluated navigation/controller.
- Keep sensor output, policy input and stored data volumes separate. Geometric ranges are not automatically physical radar measurements.
- Respect units, coordinate frames, timestamps, validity and sensor provenance in every future interface.
- Keep the simulator adapter separate from simulator-independent algorithms. Reuse Webots physics/devices; do not create a second authoritative world inside the Python core.
- Do not add vehicle fleets, dispatch, real-world flight integration or image reconstruction as incidental scope.

## Evidence and research
- Never invent training results, sensor capabilities, hardware realism or privacy guarantees.
- Report scaffold validation, simulator execution, model quality and real-world validation as separate evidence.
- Keep training, validation and final evaluation scenarios disjoint. Compare methods on the same scenarios and report failures alongside success-only metrics.
- Record meaningful changes in assumptions in docs/decisions/ and research evidence in docs/research/.
- Runtime preset numeric parameters and success thresholds remain open until specified. Keep draft presets non-runnable.
- Before adding third-party code/assets, record origin, version and license in THIRD_PARTY.md; asset terms may differ from engine terms.

## Work and verification
- Use python3 tools/check_scaffold.py for foundation changes. No Webots, ML framework or GPU is required for this check.
- Add behavior tests when implementing consequential logic; do not invent simulator smoke tests that merely import stubs.
- Keep generated logs, datasets, models, credentials and large downloaded assets out of Git.
- Do not reset, clean, stash, rewrite history or force-push as routine cleanup.
- Stage explicit paths and inspect the staged diff. Commit/push when requested or already authorized; this initial foundation commit/push is explicitly authorized.
- Final reports should state what changed, checks actually run, and remaining limitations.

## Code review rules
- Flag any runtime path that reads privileged state or images.
- Flag training/evaluation leakage, unit/frame mismatches, ignored invalid measurements and unsupported capability claims.
- Flag placeholders presented as executable environments or completed experiments.
