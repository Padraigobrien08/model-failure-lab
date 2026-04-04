# Phase 95: Debugger Recommendation Surfacing - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Surface governance recommendation status, rationale, and matched-family context directly in the
debugger on the existing signal views. This phase covers bridge payloads, React types/loaders, and
signal-surface presentation only. Full milestone workflow proof stays in Phase 96.

</domain>

<decisions>
## Implementation Decisions

### Signal Surface Posture
- Keep recommendation surfacing on the existing signal routes:
  - `/analysis` in `signals` mode
  - comparison detail framing/enforcement area
- Do not add a new governance route or family-management workspace in this milestone.

### Data Flow Contract
- Governance payloads must come from the backend bridge, not client-side recomputation.
- Extend the query bridge and Vite artifact middleware so signal rows and comparison detail payloads
  already contain deterministic recommendation data when the UI renders.

### Matched-Family Context
- Reuse the existing `SignalDatasetAutomationPanel` as the durable family-context surface.
- Add recommendation status, policy rationale, and family-health context into that panel, while
  keeping version-history/source-comparison links as the “open relevant evidence” action.
- On `/analysis`, keep family-history loading on demand.
- On comparison detail, keep the richer version-history auto-load because the user is already
  focused on one signal.

</decisions>

<code_context>
## Existing Code Insights

- [`frontend/src/app/routes/AnalysisPage.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/AnalysisPage.tsx)
  already owns the `signals` mode cards and embeds the dataset-automation panel for each saved
  comparison signal.
- [`frontend/src/app/routes/ComparisonDetailPage.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/ComparisonDetailPage.tsx)
  already has a stable “regression enforcement surface” near the top of the route.
- [`frontend/src/components/datasets/SignalDatasetAutomationPanel.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/components/datasets/SignalDatasetAutomationPanel.tsx)
  already loads version history and preview/source links, so it is the natural place to add
  recommendation and family-health context.
- [`scripts/query_bridge.py`](/Users/padraigobrien/model-failure-lab/scripts/query_bridge.py)
  and [`frontend/vite.config.ts`](/Users/padraigobrien/model-failure-lab/frontend/vite.config.ts)
  already bridge signal and dataset-evolution data into the React app.

</code_context>

<deferred>
## Deferred Ideas

- Full governance-loop workflow proof belongs to Phase 96.
- Any future family-management route or dashboard stays outside `v4.6`.

</deferred>
