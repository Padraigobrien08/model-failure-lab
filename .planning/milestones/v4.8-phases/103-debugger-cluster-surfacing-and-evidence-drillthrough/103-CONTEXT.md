# Phase 103: Debugger Cluster Surfacing And Evidence Drillthrough - Context

**Gathered:** 2026-04-04  
**Status:** Completed

## Phase Boundary

Surface recurring cluster context on existing debugger routes without creating a new workspace:
`/analysis` gets a cluster mode, and comparison enforcement surfaces gain recurring cluster cards
with direct evidence drillthrough.

## Implementation Decisions

- Keep cluster UI route-local and lightweight.
- Reuse the existing evidence-link semantics for run/comparison drillthrough.
- Treat cluster mode as another query-backed analysis variant, not a standalone dashboard.

## Existing Code Insights

- [AnalysisPage.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/AnalysisPage.tsx)
  already rendered query-backed result modes and was the natural home for cluster cards.
- [SignalDatasetAutomationPanel.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/components/datasets/SignalDatasetAutomationPanel.tsx)
  already owned history/governance context on comparison signal surfaces and could absorb compact
  recurring cluster cards.
