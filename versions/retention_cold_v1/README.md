# Cold retention v1 — exposed development only

Separate version of v4 with the same accounting/budget wrapper in both arms: full measured free-history versus a 2 s free-history window. Occupied hits persist, expired cells are unknown and command verification remains conservative. No learning or held-out inference. Design: [ADR 0012](../../docs/decisions/0012-retention-cold-development.md), [plan 0020](../../docs/plans/0020-complete-7a.md).

88 exposed v4 cases, two arms, two repeats, each in a fresh Webots process: 352 episodes. Legacy runtimes and four locks remain unchanged.
