# Project instructions for all coding agents

## Start here
- Read README.md, docs/architecture/system.md, docs/architecture/data-contracts.md, and docs/decisions/0001-foundation.md before changing architecture.
- Read docs/01-y-tuong-va-quyet-dinh.md for accepted intent. docs/02-du-thao-thi-nghiem-muc-b.md contains proposals, not approved numeric requirements.
- Communicate with the user in Vietnamese. Keep code identifiers and technical interfaces in English.
- Preserve existing work. Inspect Git status and relevant diffs before edits. If normal Git is unavailable here, read docs/development.md.
- Continue authorized work without repeatedly asking for approval. State assumptions and distinguish accepted decisions from proposals.
- Delegate only when the user or a higher-priority instruction explicitly authorizes delegation.

## Project boundaries
- Current milestone: frozen v3 validation completed once in CI 40633617042 at source 0c5f598c512a24db63b0fd19ca259a3b85382ee5, 480 episodes/127 tests, independently replayed; see docs/research/2026-10-28-cadence-v3-validation.md. Both arms have 87/100 feasible case success, below the registered 95%; study_outcome=not_met. V3 closes with a negative validation result, not incomplete infrastructure. Test remains unexposed and MUST NOT run because validation did not qualify; the frozen CLI rejects it. V3 validation is now exposed. Keep all four locks/runtime inventory unchanged, no second dispatch/rerun to improve outcomes. GOAL-22 offline diagnosis is now complete under docs/plans/0013-navigation-start-diagnostics.md and docs/research/2026-10-28-navigation-start-diagnostics.md (five development traces, 141 tests): unknown cells wholly inside the sensor-origin ring block execution. The GOAL-22 diagnosis itself did not change navigation or add simulator episodes. GOAL-23 implementation/development is complete in versions/navigation_v4/ under ADR 0007 and plan 0014: source 9503c2c2b483d677d7f0ff25f76d7dcca360bc08, CI 40684709433, 165 unit tests and 352 Webots episodes; reference 62/74 versus v4 74/74 feasible cases, both repeats of five deadlock regressions succeed, no collision/bounds/negative false success. See docs/research/2026-10-28-observed-detour-v4.md. This is exposed development, with added CPU cost and max above 16 ms; no held-out v4 protocol or data-rate reduction result. Keep all four legacy locks and src/ unchanged: v3 inventory includes every src/**/*.py. Future research needs its own protocol/source lock/fresh splits before evaluation. No training or radar implementation authorization.
- Observation memory, hull-aware filtering and online-grid navigation v2 were completed under docs/plans/0005-observation-and-navigation-v2.md. Keep both exposed protocols frozen; further algorithm changes need a new version and fresh evaluation design.
- Stage 0005 is now verified at source 2f422e253376b589e478ac10f3eee8efa970dc74 with 108 official episodes and 64 unit tests; see docs/research/2026-10-26-navigation-v2.md. V2 validation/test are exposed. Keep both locks valid; further algorithm changes need a new protocol/test version, not silent lock regeneration. Maps/CPU are added costs, not evidence of data minimization/privacy or hardware safety.
- This stage is validated in CI at source 373b002d0ada514c95ce409cbb87d4bc3d68a388; see docs/research/2026-10-26-seeded-environments.md. Test v1 is now exposed. Baseline failures remain; do not treat pipeline completion as trained-model quality or reuse test v1 as unseen after tuning.
- First research task: one simulated drone reaches a supplied goal while avoiding static obstacles (level B).
- Webots is the first simulator. Keep local execution, CI execution and GUI inspection evidence separate; training remains a later milestone.
- Historical GitHub integration is recorded at source 63298d7 in docs/plans/0007-github-integration.md and docs/research/2026-10-26-github-integration.md. Runtime 39c34af later passed 82 tests/all four workflows and the final manual 020953/mapped 022316 desktop review. Keep older incomplete/timeout evidence as history rather than replacing its outcomes.
- Local collector sequencing/locking is documented in docs/plans/0008-sequential-local-acceptance.md and the launcher fix in docs/plans/0009-local-launcher-followup.md. Preserve checkout while .local/local-session/active.lock is held. Final local review confirms all control directions and operator observations; sampled telemetry alone does not uniquely prove SPACE/release/R or hardware realtime. Never bypass evidence gates or copy operator answers across runs.
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
- Legacy draft research presets remain non-runnable. V3 cadence-study thresholds are prespecified in configs/experiments/range_cadence_v3.toml under ADR 0006; runtime_ready=false until a separately versioned runtime implementation is verified. Do not change the design lock, tune on validation/test, or claim its 50% target as an achieved result. configs/lab_v1.toml contains provisional engineering parameters for simulator validation.
- Before adding third-party code/assets, record origin, version and license in THIRD_PARTY.md; asset terms may differ from engine terms.

## Work and verification
- Use python3 tools/check_scaffold.py for foundation changes. No Webots, ML framework or GPU is required for this check.
- For lab changes run python3 tools/build_lab.py --check and python3 -m unittest discover -s tests -p 'test_*.py' -v. Real simulator verification uses python3 tools/run_webots.py --smoke with Webots R2025a; a missing executable must fail rather than skip silently.
- Navigation changes also require python3 tools/run_webots.py --navigation on real Webots. Keep direct/reactive paired development results, impossible negative controls and later held-out research results distinct.
- Seed-suite changes require python3 tools/build_scenarios.py --check and the frozen protocol. Do not tune after validation/test exposure or replace the v1 lock silently. Only world/evaluation may read witness paths. A baseline failure is an outcome, not permission to drop a case.
- Run python3 tools/build_research_v3.py --check for v3 design/data-integrity changes; make check includes it. Maintain CHECKLIST_MUC_TIEU_NGHIEN_CUU.md with evidence at milestone handoff.
- Add behavior tests when implementing consequential logic; do not invent simulator smoke tests that merely import stubs.
- Keep generated logs, datasets, models, credentials and large downloaded assets out of Git.
- Do not reset, clean, stash, rewrite history or force-push as routine cleanup.
- Stage explicit paths and inspect the staged diff. Follow the standing Git authorization below.
- Final reports should state what changed, checks actually run, and remaining limitations.
- Keep CHECKLIST_DU_AN.md current at milestone handoff: mark only evidenced completion, retain local/CI/hardware distinctions and label future work as proposals. Update its date/evidence links without rewriting historical reports or exposed-test status.

## Standing Git authorization for this workspace

The user explicitly authorized Codex to commit and push at appropriate project milestones on 2026-10-26. This applies to ongoing authorized project work and future sessions in this repository; no repeated confirmation is needed for routine commits, feature-branch pushes or a verified fast-forward to main. A later user instruction overrides this policy.

- Use small, coherent commits: accepted plan/protocol, a working module with its checks, a validated integration/fix, and the evidence/docs handoff. Combine adjacent steps when that makes review clearer; do not commit every file or tool call.
- Run checks appropriate to the change, inspect diff/status, stage only task-owned paths and use descriptive messages (docs/feat/fix/test/ci as appropriate). Preserve unrelated user changes and existing authorship.
- Push a feature branch when local checks pass and remote CI is needed, at a useful recovery checkpoint, and before handing off a completed milestone. A CI-fix commit may precede simulator success, but describe its unverified state honestly. Do not push logs, downloads, credentials, datasets or model outputs; small reviewed research evidence belongs in docs/research.
- Promote to main only when the milestone's relevant checks have passed, required simulator evidence exists, and a fresh remote read confirms a safe fast-forward. For docs-only evidence added after the verified source commit, rerun documentation checks and retain the exact tested source SHA. Respect repository protection rules and use a PR if required.
- Never force-push, rewrite published history, reset/clean/stash other work, change remotes/access controls or bypass approval/network restrictions as part of this authorization. On a non-fast-forward or new remote work, inspect it and integrate safely without overwriting it.
- Prefer normal Git/SSH when available. In the managed workspace use tools/git.sh; if shell network is unavailable, an authorized GitHub connector may publish the same reviewed tree. Verify matching tree/commit hashes and synchronize local refs without discarding files.
- Report the branch, commit, push/CI status and any remaining limitation at handoff. A failed push/CI is not a successful publication or completed validation.

## Code review rules
- Flag any runtime path that reads privileged state or images.
- Flag training/evaluation leakage, unit/frame mismatches, ignored invalid measurements and unsupported capability claims.
- Flag placeholders presented as executable environments or completed experiments.
