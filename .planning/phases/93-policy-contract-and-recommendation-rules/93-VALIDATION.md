# 93 Validation

## Must Pass

1. A qualifying regression with no existing family yields a deterministic `create`
   recommendation.
2. A qualifying regression with an existing matching family yields a deterministic `evolve`
   recommendation.
3. An improvement, neutral, incompatible, filtered-out, or below-threshold signal yields
   `ignore` with explicit rationale.
4. Recommendation payload includes:
   - action
   - policy
   - signal snapshot
   - matched family context
   - evidence-linked preview case ids
5. Repeated recommendation calls over the same saved comparison produce identical payloads.

## Automated Proof

- unit tests covering recommendation action selection and rationale fields
- unit tests covering family existence/cap checks and duplicate-growth checks
- unit tests covering dry-run regression-pack preview reuse without file writes
