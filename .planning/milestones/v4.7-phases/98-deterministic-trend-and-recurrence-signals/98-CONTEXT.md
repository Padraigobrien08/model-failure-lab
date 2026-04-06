# Phase 98: Deterministic Trend And Recurrence Signals - Context

**Gathered:** 2026-04-04
**Status:** Completed

<domain>
## Phase Boundary

Compute deterministic trend, volatility, recurrence, and dataset-health signals over the history
contract added in Phase 97. This phase stops at backend signal computation and typed payloads.

</domain>

<decisions>
## Implementation Decisions

- Use simple deterministic deltas and volatility bands instead of statistical forecasting.
- Compute recurrence from recent comparison history and persisted signal/top-driver metadata.
- Summarize dataset health from versioned dataset families plus the runs that evaluated them.
- Keep the signal layer reusable by both governance and the frontend bridge.

</decisions>

<code_context>
## Existing Code Insights

- [`src/model_failure_lab/history.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/history.py)
  is the right home for trend and health derivation because it already owns ordered history rows.
- [`src/model_failure_lab/governance/policy.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/policy.py)
  already evaluates deterministic actions from saved signals and can consume historical context
  without changing the action model.

</code_context>

<deferred>
## Deferred Ideas

- CLI rendering of history belongs to Phase 99.
- Debugger trend and timeline surfacing belongs to Phase 100.

</deferred>
