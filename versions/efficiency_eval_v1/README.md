# Conditional fresh 7A evaluation design

Design-only commitments under [plan 0022](../../docs/plans/0022-fresh-7a-evaluation.md); `runtime_ready=false` and candidate pending. There is no simulator runner or qualified held-out runtime here. Generating geometry/certificates programmatically is not executing or viewing navigation outcomes.

Fresh validation/test have 60 feasible and 12 negative cases each, balanced across five feasible families. Geometry/canonical-task/seed checks use historical v1/v2, all v3 index hashes (including the closed test, without generating its geometry), and exposed v4 cases. The candidate may be bound only after all prerequisite raw reviews and a separate runtime lock. V3 test stays closed.
