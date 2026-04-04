# Phase 84: Harvest Replay Loop And Workflow Verification - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Prove the closed-loop workflow from observed artifact failures to curated rerunnable datasets.
This phase is verification-heavy: it should not invent a second replay format or a hosted workflow.
It only needs to demonstrate that harvested packs flow back through the existing dataset, run,
report, compare, query, and insight surfaces without manual reshaping.

</domain>

<decisions>
## Implementation Decisions

### Proof Surface
- Use the deterministic insight fixture workspace as the source artifact root so the loop stays
  reproducible and fast.
- Keep the proof automated: harvest a regression slice, review/promote it, rerun the promoted
  dataset with two fixture models, then compare and summarize those rerun artifacts.

### Documentation Posture
- Add one concrete README loop example using the same fixture workspace so the manual path matches
  the automated proof.
- Do not add a new dedicated smoke harness unless the current test surface proves insufficient.

</decisions>

<deferred>
## Deferred Ideas

- Automatic regression-pack creation and alerts belong to the next milestone, not this one.
- Dataset versioning remains out of scope for `v4.3`.

</deferred>
