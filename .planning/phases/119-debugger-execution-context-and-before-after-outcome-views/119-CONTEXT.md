# Phase 119: Debugger Execution Context And Before/After Outcome Views - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Surface saved execution state on the existing debugger routes without creating a separate
execution dashboard. This phase covers bridge payload enrichment, typed frontend parsing, and
route-local execution context on the comparison detail automation surfaces.

</domain>

<decisions>
## Implementation Decisions

### Route Strategy
- Reuse the existing dataset-versions bridge payload so execution context arrives with the same
  family, lifecycle, and saved-plan request already used on comparison detail and analysis routes.
- Keep execution context inside the existing automation panel and sticky operator summary instead
  of adding a new execution page.

### UI Density
- Show only the newest linked execution prominently, with before/after family state, rollback
  guidance, and next steps, because the operator is already anchored on one comparison.
- Preserve the same route-local badge and card language used for lifecycle, portfolio, and family
  context so execution feels like the next step in the same workflow.

</decisions>

<code_context>
## Existing Code Insights

- [`query_bridge.py`](/Users/padraigobrien/model-failure-lab/scripts/query_bridge.py)
  already enriches dataset-version payloads with lifecycle and saved-plan context.
- [`load.ts`](/Users/padraigobrien/model-failure-lab/frontend/src/lib/artifacts/load.ts)
  already owns the typed parser for dataset-versions responses, making it the right contract seam.
- [`SignalDatasetAutomationPanel.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/components/datasets/SignalDatasetAutomationPanel.tsx)
  already decomposes family-state and portfolio sections, so execution context can sit beside
  those surfaces.
- [`ComparisonDetailPage.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/ComparisonDetailPage.tsx)
  already keeps a sticky operator summary rail for the same family and plan data.

</code_context>
