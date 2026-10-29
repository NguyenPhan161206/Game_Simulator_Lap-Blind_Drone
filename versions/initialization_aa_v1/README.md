# Initialization A/A v1 — development only

Both labels use the frozen v4 full-history navigator. Compare warm sequential episodes with one new Webots process per cold episode; this does not change retention or estimate held-out quality. Design: [plan 0019](../../docs/plans/0019-initialization-aa-development.md), [ADR 0011](../../docs/decisions/0011-initialization-aa-development.md).

12 exposed cases, two modes, two labels and two repeats: 96 episodes. Cold equivalence gates are fixed before simulator execution. Keep all old runtime inventories and locks unchanged; no training/radar/v3 test.
