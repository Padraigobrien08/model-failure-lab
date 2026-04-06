# Phase 116: Operator Workflow Verification And UI Stability - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Close `v5.1` by validating the operator workflow end-to-end and absorbing the remaining local UI
stability fixes already identified during manual browser testing. This phase covers route-stability
verification across comparisons, comparison detail, and analysis, plus the pending router-warning
and duplicate-key cleanup.

</domain>

<decisions>
## Implementation Decisions

### Stability Scope
- Treat the existing local `App.tsx` router future-flag change and `InsightPanel.tsx` duplicate-key
  fix as Phase 116 stability work rather than leaving them as uncommitted session drift.
- Prefer broader route/build verification over adding speculative new features.

### Verification Shape
- Re-run the focused route suites that define the `triage -> detail -> analysis` loop:
  comparisons, comparison detail, and analysis.
- Add a production build check so the milestone closes with route behavior and bundle stability,
  not just isolated component tests.

</decisions>

<code_context>
## Existing Code Insights

### Pending Local Fixes
- [`App.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/App.tsx) already has a local
  React Router future-flag patch to remove dev-console upgrade warnings.
- [`InsightPanel.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/components/insights/InsightPanel.tsx)
  already has a local duplicate-key fix for repeated anomaly/pattern group keys.

### Verification Anchors
- [`comparisons.test.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/__tests__/comparisons.test.tsx)
  covers the triage inventory.
- [`comparisonDetail.test.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/__tests__/comparisonDetail.test.tsx)
  covers operator summary, lifecycle, portfolio, and evidence drillthrough.
- [`analysis.test.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/__tests__/analysis.test.tsx)
  covers analysis presets, draft export, signal rows, and shell orientation.

</code_context>

<specifics>
## Specific Ideas

- Land the router future flags and duplicate-key fix as part of the final stability commit.
- Verify route-local shareability and artifact-grounded behavior across all `v5.1` UI phases in one
  final test/build pass.

</specifics>
