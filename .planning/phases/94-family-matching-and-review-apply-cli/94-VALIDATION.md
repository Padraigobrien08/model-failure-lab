# 94 Validation

## Must Pass

1. User can request a single-comparison recommendation from the CLI and receive the Phase 93
   payload.
2. User can review recent actionable recommendations without writing dataset files.
3. User can apply recommendations reproducibly and receive created or evolved dataset summaries.
4. User can inspect dataset family health and see why a family is chosen, capped, or duplicate
   heavy.
5. Applying the same saved comparisons twice is stable: the second pass should either skip or
   evolve deterministically based on current family state, not produce ambiguous actions.

## Automated Proof

- backend tests for family health and review/apply workflow
- CLI tests for `regressions recommend`, `regressions review`, `regressions apply`, and
  `dataset families`
