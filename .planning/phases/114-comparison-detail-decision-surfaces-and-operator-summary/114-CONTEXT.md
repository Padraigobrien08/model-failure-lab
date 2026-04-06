# Phase 114: Comparison Detail Decision Surfaces And Operator Summary - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Restructure the comparison detail route so the operator can keep the decision state in view while
scrolling through evidence. This phase covers the right-rail summary, decomposition of the
regression enforcement surface, and detail-route information architecture on the existing
`/comparisons/:reportId` flow.

</domain>

<decisions>
## Implementation Decisions

### Sticky Operator Summary
- Promote the key operator state into the existing sticky right rail instead of creating a new top-
  level route or modal workflow.
- Keep section jumps and provenance cards, but move them below a decision-first summary card.

### Data Loading Strategy
- Reuse the existing dataset-versions payload that already carries lifecycle actions, family health,
  portfolio priority, and saved plan context.
- Keep auto-loading on the detail route, but surface the loaded family state back to the route so
  the rail can summarize it without duplicating fetch endpoints.

### Automation Surface Decomposition
- Preserve the current regression-enforcement card and actions, but split its contents into named
  sections: recommendation, family state, portfolio context, action controls, preview, and history.
- Prefer small section labels and grouped blocks over a single uninterrupted vertical stack.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- [`ComparisonDetailPage.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/ComparisonDetailPage.tsx)
  already owns the sticky aside and route search state, so it should also own the operator summary.
- [`SignalDatasetAutomationPanel.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/components/datasets/SignalDatasetAutomationPanel.tsx)
  already loads dataset-family versions and exposes all governance/lifecycle surfaces needed for a
  summary rail.
- [`comparisonDetail.test.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/__tests__/comparisonDetail.test.tsx)
  already mocks dataset-version payloads with lifecycle, family health, portfolio item, and saved
  plan data.

### Established Patterns
- The debugger routes use sticky side rails for route-local context and section navigation.
- Frontend artifact parsing already treats governance and portfolio context as optional, so the
  detail route can stay compatible with older artifact roots.

### Integration Points
- The detail route reads comparison detail from
  [`loadComparisonDetail`](/Users/padraigobrien/model-failure-lab/frontend/src/lib/artifacts/load.ts)
  and family context from
  [`loadArtifactDatasetVersions`](/Users/padraigobrien/model-failure-lab/frontend/src/lib/artifacts/load.ts).
- The right rail currently only shows section jumps, provenance, and run links, leaving the newer
  operator state buried inside the automation panel.

</code_context>

<specifics>
## Specific Ideas

- Add an “Operator summary” card with severity, recommendation, escalation, lifecycle state,
  matched family, portfolio rank, and saved plan count.
- Keep family state visible even when the main column scrolls deep into coverage and transition
  evidence.
- Break the automation panel into explicit sections so recommendation, history, and actions are
  easier to parse independently.

</specifics>

<deferred>
## Deferred Ideas

- Comparisons inventory triage belongs to completed Phase 113.
- Analysis presets and workspace controls belong to Phase 115.
- Router warning cleanup and broader UI stability checks belong to Phase 116.

</deferred>
