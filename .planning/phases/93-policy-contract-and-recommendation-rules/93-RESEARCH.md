# 93 Research

## Goal

Define a deterministic governance recommendation contract without duplicating the existing
comparison-signal and dataset-evolution logic.

## Findings

1. The current signal layer already supplies the exact quantitative inputs governance needs.
   - `signal.verdict`
   - `signal.severity`
   - `signal.top_drivers`
   - saved case-delta evidence ids

2. The current dataset-evolution layer is structurally close to governance but lacks a dry-run seam.
   - `generate_regression_pack(...)` and `evolve_dataset_family(...)` both depend on the same
     selection logic.
   - governance needs that same selection result without writing draft or curated dataset files.

3. Family matching should remain intentionally narrow in this phase.
   - `suggest_dataset_family_id(...)` already gives one deterministic family candidate derived from
     dataset identity plus the primary regression driver.
   - full lineage/overlap matching should be deferred until the review/apply phase.

4. The most useful Phase 93 output is a typed recommendation payload.
   - It should capture policy, signal, family match, action, and evidence preview together.
   - Later CLI and debugger surfaces can render this payload without inventing a second policy path.

## Chosen Approach

- Add a governance backend module with typed policy and recommendation dataclasses.
- Refactor dataset evolution to expose a read-only regression-pack preview function that governance
  can reuse.
- Keep the recommendation engine single-comparison scoped in this phase.
