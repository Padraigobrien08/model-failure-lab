# Phase 83: Debugger Export And Provenance Drillback - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Add lightweight draft-dataset export to the existing debugger surfaces without turning the browser
into a dataset editor. This phase covers `/analysis` and comparison detail export actions plus the
artifact-root bridge needed to write draft packs from the active workspace. Review, promotion, and
rerun proof stay in later phases.

</domain>

<decisions>
## Implementation Decisions

### Export Posture
- Keep export explicit and route-local: one button on `/analysis` for the current filtered result
  set, and one button on comparison detail for the currently selected transition slice.
- Do not support aggregate export. Export is only valid for concrete case or delta selections.

### Bridge Contract
- Reuse the existing frontend -> `query_bridge.py` middleware seam instead of introducing a new
  service or browser-side filesystem workflow.
- The browser sends structured filters plus an output stem; the bridge resolves the active
  artifact root and writes the draft pack locally.

### Provenance Model
- Preserve the current detail-route drillthrough model. Exported draft packs carry the same
  harvest provenance metadata written by the CLI pipeline, so source evidence stays reconnectable
  through run or comparison routes.
- Success/failure messaging should stay adjacent to the export action instead of pushing users into
  a separate review route.

</decisions>

<code_context>
## Existing Code Insights

- [`scripts/query_bridge.py`](/Users/padraigobrien/model-failure-lab/scripts/query_bridge.py)
  already owns the structured query bridge between the frontend and the local Python index layer.
- [`frontend/src/app/routes/AnalysisPage.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/AnalysisPage.tsx)
  already has URL-backed structured filters over cases, deltas, and aggregates.
- [`frontend/src/app/routes/ComparisonDetailPage.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/ComparisonDetailPage.tsx)
  already has exact selected-case state, transition grouping, and run drillthrough.
- [`src/model_failure_lab/harvest/pipeline.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/harvest/pipeline.py)
  already materializes canonical draft dataset packs from structured filters.

</code_context>

<deferred>
## Deferred Ideas

- Draft review and promotion are already handled in Phase 82.
- Full closed-loop replay verification belongs to Phase 84.

</deferred>
