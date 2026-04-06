# Phase 99: CLI History Surfaces And Governance Context - Context

**Gathered:** 2026-04-04
**Status:** Completed

<domain>
## Phase Boundary

Expose the time-aware history layer through the CLI and thread historical context into governance
recommendation output. This phase stops at backend and CLI surfaces; UI work remains in Phase 100.

</domain>

<decisions>
## Implementation Decisions

- Add a top-level `failure-lab history` command instead of burying timelines inside query mode.
- Keep governance deterministic by using history as contextual input, not a replacement for the
  existing create/evolve/ignore policy contract.
- Allow recent recurrence to override low-severity `ignore` decisions only under explicit local
  thresholds.
- Surface the same history context through the query bridge so the debugger renders persisted
  payloads rather than recomputing anything client-side.

</decisions>

<code_context>
## Existing Code Insights

- [`src/model_failure_lab/cli.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/cli.py)
  already owns signal, governance, and dataset-family CLI workflows.
- [`scripts/query_bridge.py`](/Users/padraigobrien/model-failure-lab/scripts/query_bridge.py)
  is the established seam for debugger-facing read-only artifact payloads.

</code_context>

<deferred>
## Deferred Ideas

- Route-local timeline surfacing in React belongs to Phase 100.
- Proactive alerts or automatic governance mutation based on history alone stay out of scope.

</deferred>
