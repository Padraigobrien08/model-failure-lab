# Phase 88: Signal Stability And Workflow Verification - Context

**Gathered:** 2026-04-04
**Status:** Completed

<domain>
## Phase Boundary

Close `v4.4` by proving the full signal layer is stable and workflow-complete across persisted
artifacts, CLI surfaces, query/index listing, and debugger severity views. This phase is proof and
workflow hardening, not a new product surface.

</domain>

<decisions>
## Implementation Decisions

### Stability Contract
- Treat repeated `compare` calls over the same saved runs as a deterministic operation: the signal
  payload must remain identical and the same comparison identity should remain queryable after an
  index rebuild.

### Workflow Proof
- Reuse the existing real-artifacts smoke script rather than inventing a separate verifier.
- Extend that smoke proof to include the new `signals` analysis query path and persisted comparison
  signal presence.

### Milestone Bar
- Close `v4.4` only after backend signal tests, CLI signal workflow tests, debugger route tests,
  the frontend production build, and the real-artifacts smoke all pass together.

</decisions>

<code_context>
## Existing Code Insights

- [`tests/unit/test_cli_demo_compare.py`](/Users/padraigobrien/model-failure-lab/tests/unit/test_cli_demo_compare.py)
  already exercised the compare/report/query loop, so it was the right place to add repeated
  compare and index-rebuild stability proof.
- [`frontend/scripts/smoke-real-artifacts.mjs`](/Users/padraigobrien/model-failure-lab/frontend/scripts/smoke-real-artifacts.mjs)
  already verified cases, deltas, and aggregates against a live Vite middleware instance, making
  `signals` the natural final addition.

</code_context>

<deferred>
## Deferred Ideas

- Automatic alerts or scheduled regression detection stay out of `v4.4`.
- Dataset seeding or alert routing from signals belongs to later milestones.

</deferred>
