# Phase 123: Policy Feedback And Debugger Outcome Timelines - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Feed attested outcomes back into family and portfolio context, then surface open and closed outcome
state on the existing debugger routes. This phase covers portfolio feedback summaries, bridge
payload enrichment, and route-local outcome context in the React UI.

</domain>

<decisions>
## Implementation Decisions

### Feedback Scope
- Keep feedback family-scoped and artifact-derived instead of introducing a separate portfolio
  history store.

### Payload Reuse
- Extend the existing dataset-versions payload so comparison detail and automation surfaces can
  load family versions, plan executions, and outcomes in one request.

### UI Shape
- Surface outcome state on the current automation panel and sticky comparison-detail summary rail
  rather than creating a separate outcomes dashboard.

</decisions>

<code_context>
## Existing Code Insights

- [`portfolio.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/portfolio.py)
  already computes deterministic priority and rationale for dataset families.
- [`query_bridge.py`](/Users/padraigobrien/model-failure-lab/scripts/query_bridge.py)
  already aggregates dataset-family history, portfolio, and execution context for the debugger.
- [`SignalDatasetAutomationPanel.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/components/datasets/SignalDatasetAutomationPanel.tsx)
  and
  [`ComparisonDetailPage.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/ComparisonDetailPage.tsx)
  already carry route-local lifecycle and execution context that outcome timelines should extend.

</code_context>

<specifics>
## Specific Ideas

- Summarize open, evidence-linked, and attested outcomes per family and fold those counts into
  portfolio rationale and priority scoring.
- Add typed frontend support for outcome payloads and render the latest outcome plus timeline in
  the existing automation surfaces.
- Keep the sticky operator summary focused on decision state by surfacing the latest attestation
  next to lifecycle, priority, and execution.

</specifics>
