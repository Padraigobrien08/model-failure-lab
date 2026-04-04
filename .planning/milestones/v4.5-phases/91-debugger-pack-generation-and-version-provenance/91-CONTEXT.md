# Phase 91: Debugger Pack Generation And Version Provenance - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Expose the new regression-pack and dataset-evolution workflows from the existing artifact-backed
debugger without turning it into a browser-side dataset editor. This phase owns the bridge,
loaders, and route-local UI surfaces for generation, evolution, family history, and provenance
drillback.

</domain>

<decisions>
## Implementation Decisions

### UI Posture
- Keep dataset automation attached to existing signal surfaces rather than inventing a separate
  dataset-management route.
- Reuse the comparison and analysis signal views where regression severity is already visible.
- Keep the panel lightweight: generate, evolve, inspect history, and drill back to the source
  comparison.

### Bridge Contract
- Reuse the artifact query bridge and Vite middleware instead of adding a new service.
- Add explicit endpoints for regression-pack creation, dataset evolution, and family-version
  listing so the frontend stays strongly typed.

### Provenance Drillback
- Version history should link back to source comparisons and case evidence through the existing
  detail-route return-state model.
- The UI should preserve current route context while opening source comparison evidence.

</decisions>

<code_context>
## Existing Code Insights

- [`frontend/src/app/routes/AnalysisPage.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/AnalysisPage.tsx)
  already has signal-mode cards backed by the local query layer.
- [`frontend/src/app/routes/ComparisonDetailPage.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/ComparisonDetailPage.tsx)
  already has a framing section where comparison signal context lives near evidence drillthrough.
- [`scripts/query_bridge.py`](/Users/padraigobrien/model-failure-lab/scripts/query_bridge.py) and
  [`frontend/vite.config.ts`](/Users/padraigobrien/model-failure-lab/frontend/vite.config.ts)
  already define the artifact-backed frontend bridge pattern.

</code_context>
