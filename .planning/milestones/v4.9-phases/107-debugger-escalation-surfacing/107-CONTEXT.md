# Phase 107: Debugger Escalation Surfacing - Context

**Gathered:** 2026-04-05
**Status:** Completed

<domain>
## Phase Boundary

Surface escalation status and lifecycle recommendations on the existing debugger routes, with
drillthrough into affected family evidence and lifecycle history. This phase covers the artifact
bridge, typed frontend parsing, and route-local UI presentation.

</domain>

<decisions>
## Implementation Decisions

- Keep escalation and lifecycle surfacing on the existing analysis and comparison routes rather
  than creating a new dashboard or lifecycle workspace.
- Keep policy evaluation backend-owned; the debugger only consumes persisted escalation and
  lifecycle payloads from the query bridge.
- Reuse `SignalDatasetAutomationPanel` as the durable family context surface, and enrich the
  comparison header and analysis signal rows with lightweight badges and rationale.

</decisions>

<code_context>
## Existing Code Insights

- [scripts/query_bridge.py](/Users/padraigobrien/model-failure-lab/scripts/query_bridge.py) is the
  backend bridge for dataset-family history and now also carries lifecycle action history.
- [types.ts](/Users/padraigobrien/model-failure-lab/frontend/src/lib/artifacts/types.ts) and
  [load.ts](/Users/padraigobrien/model-failure-lab/frontend/src/lib/artifacts/load.ts) are the
  right seam for typed escalation and lifecycle payload parsing.
- [AnalysisPage.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/AnalysisPage.tsx),
  [ComparisonDetailHeader.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/components/comparisons/ComparisonDetailHeader.tsx),
  and
  [SignalDatasetAutomationPanel.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/components/datasets/SignalDatasetAutomationPanel.tsx)
  already own the relevant evidence and family drillthrough surfaces.

</code_context>

<deferred>
## Deferred Ideas

- Full workflow proof and milestone closeout belong to Phase 108.

</deferred>
