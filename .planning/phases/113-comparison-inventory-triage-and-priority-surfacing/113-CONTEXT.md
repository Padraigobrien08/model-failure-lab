# Phase 113: Comparison Inventory Triage And Priority Surfacing - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Surface governance, lifecycle, family, and priority context directly in the saved comparisons
inventory so operators can triage which reports deserve attention before opening detail views.
This phase covers the comparison inventory bridge payload, typed frontend parsing, and operator-
first filtering/sorting on the existing `/comparisons` route.

</domain>

<decisions>
## Implementation Decisions

### Inventory Data Contract
- Enrich `comparisons.json` with optional governance recommendation and matched portfolio item data
  for each comparison instead of introducing a second per-row fetch path.
- Keep the payload backward compatible: rows without governance or portfolio context still render
  with the existing signal-only inventory view.

### Triage Interaction Model
- Add route-local triage lenses and filtering on the existing comparisons page rather than creating
  a new queue route.
- Preserve the current severity/newest ordering as the default, but allow operator-first views such
  as actionable, critical, and lifecycle follow-up.

### Inventory Density
- Keep the inventory table compact and scannable by reusing badge-heavy summaries rather than
  expanding each row into a card-only dashboard.
- Surface matched family and priority context inline with the signal block so the operator sees the
  recommended next move in one scan line.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- [`scripts/query_bridge.py`](/Users/padraigobrien/model-failure-lab/scripts/query_bridge.py)
  already attaches governance recommendation data to signal analysis results, so the same
  recommendation seam can enrich the comparison inventory.
- [`ComparisonInventoryTable.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/components/comparisons/ComparisonInventoryTable.tsx)
  already handles dense badge-based scan patterns and keyboard-open behavior.
- [`ComparisonsPage.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/ComparisonsPage.tsx)
  already owns sorting and route navigation, making it the right place for triage lenses.

### Established Patterns
- Existing debugger routes prefer route-local enrichment and typed artifact parsing over ad hoc
  browser state.
- Governance, lifecycle, and portfolio context already use optional payload parsing in
  [`load.ts`](/Users/padraigobrien/model-failure-lab/frontend/src/lib/artifacts/load.ts), so the
  inventory can follow the same optional-contract pattern.

### Integration Points
- Backend inventory rows come from [`query.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/index/query.py)
  and the query bridge, then flow through
  [`loadComparisonInventory`](/Users/padraigobrien/model-failure-lab/frontend/src/lib/artifacts/load.ts)
  into [`ComparisonsPage.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/ComparisonsPage.tsx).
- Focused inventory regressions already live in
  [`comparisons.test.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/__tests__/comparisons.test.tsx).

</code_context>

<specifics>
## Specific Ideas

- Show recommendation action, escalation status, lifecycle action, matched family, and priority
  band directly in the inventory row.
- Add quick triage views for actionable comparisons, critical escalations, and lifecycle follow-up.
- Keep multiple datasets and incompatible comparisons readable; triage context must not hide core
  report identity or compatibility status.

</specifics>

<deferred>
## Deferred Ideas

- Persistent operator summary and detail-route restructuring belong to Phase 114.
- Analysis presets and artifact-root shell controls belong to Phase 115.

</deferred>
