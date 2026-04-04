# Phase 89: Signal-To-Pack Generation - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Turn persisted comparison signals into deterministic draft regression packs without reopening the
older manual harvest path. This phase stops at draft-pack generation and provenance persistence. It
does not yet cover immutable version families, debugger affordances, or replay-loop closeout.

</domain>

<decisions>
## Implementation Decisions

### Signal-First Selection
- Start from the saved comparison signal contract rather than raw comparison rows.
- Use top regression drivers first, then fall back to regression delta order when driver metadata is
  not sufficient.
- Keep pack composition deterministic through explicit `top_n`, `failure_type`, and delta-kind
  policy fields.

### Draft Pack Contract
- Generated packs should stay inside the canonical dataset envelope so the standard runner can use
  them later without a second import format.
- Keep the dataset lifecycle explicit as `draft` and preserve source comparison/signal provenance in
  top-level `source` plus per-case harvest metadata.

### Evidence Rehydration
- Use the index only to select rows.
- Rehydrate prompt text, expectations, and tags from the saved baseline/candidate run artifacts so
  draft packs remain grounded in canonical evidence payloads.

</decisions>

<code_context>
## Existing Code Insights

- [`src/model_failure_lab/reporting/compare.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/reporting/compare.py)
  already persists deterministic signal metadata inside comparison artifacts.
- [`src/model_failure_lab/index/query.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/index/query.py)
  already exposes comparison-signal and case-delta queries over the derived local index.
- [`src/model_failure_lab/datasets/contracts.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/datasets/contracts.py)
  already defines the dataset envelope consumed by the runner.
- [`src/model_failure_lab/testing/insight_fixture.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/testing/insight_fixture.py)
  already materializes saved runs/comparisons that expose compatible signal and delta patterns.

</code_context>

<deferred>
## Deferred Ideas

- Immutable family versioning belongs to Phase 90.
- Debugger-triggered pack generation belongs to Phase 91.
- Replay-loop proof belongs to Phase 92.

</deferred>
