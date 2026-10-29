# 0016 — DATA-04: occupied-hit TTL

Status: development implementation and unit tests complete; Webots study pending.

1. Freeze the design in [ADR 0009](../decisions/0009-data04-hit-ttl.md): expire each occupied hit after 10.0 simulation seconds since its latest observation; refresh on repeat hit.
2. Keep DATA-03 as the paired reference. Change no sensor, timing, controller, free retention, planner, case, scoring, or map-budget variable.
3. Implement in `versions/data_history_v1/` with separate Webots world/controller, runner, reviewer and runtime inventory. Keep v1/v2/v3/v4 and DATA-03 files immutable.
4. Test hit expiry, inflation rebuild, repeat packet behavior, unknown-route stop, map budget, and absence of privileged imports.
5. Run only the 88 exposed development cases, two repeats and two arms (352 episodes). Preserve each attempt and every failure; no validation/test split is defined by this study.
6. Independently review raw evidence and report task success, paired outcomes, failures, CPU, process RSS, map entries and TTL/memory effects.
7. Treat this as a diagnostic point only. Any alternate TTL or configuration selection requires a new version and fresh evaluation design.

No v3 test run is authorized by this plan. No claim of held-out quality, hardware safety, privacy, or minimum information follows from this experiment.
