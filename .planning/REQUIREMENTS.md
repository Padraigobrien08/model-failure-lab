# Requirements: v5.1 Operator Workflow Clarity And Triage Surfaces

**Defined:** 2026-04-06  
**Status:** Active

## v5.1 Requirements

### Comparison Triage

- [x] **TRIAGE-01**: Users can scan saved comparisons with governance recommendation, escalation,
  lifecycle state, matched family, and portfolio-priority context visible in the inventory itself.
- [x] **TRIAGE-02**: Comparison inventory supports operator-first sorting, filtering, or grouping
  by actionability and lifecycle context rather than only raw comparison identity fields.

### Comparison Detail Workflow

- [x] **DETAIL-01**: Comparison detail keeps the current operator state visible in a persistent
  summary surface that includes severity, escalation, lifecycle action, matched family, priority,
  and saved-plan linkage.
- [x] **DETAIL-02**: The current regression-enforcement surface is decomposed into clearer
  recommendation, action, family-state, and history sections so users do not parse one overloaded
  card.
- [x] **DETAIL-03**: Users can move from the operator summary into supporting family history,
  lifecycle actions, saved plans, and comparison evidence without losing route context.

### Analysis And Workspace Intent

- [x] **ANALYSIS-01**: `/analysis` exposes intent-first presets for common workflows such as
  actionable regressions, critical families, merge candidates, or plan-backed items.
- [x] **ANALYSIS-02**: Analysis presets remain URL-shareable and preserve the underlying filter
  logic so operators can return to the same view predictably.
- [x] **SHELL-01**: The shared shell makes artifact-root and workspace status first-class context
  with clearer controls, provenance, and orientation cues.

### Workflow Verification

- [x] **FLOW-01**: The full local operator workflow from comparison inventory to detail decision
  support to analysis preset drillthrough is verified and reproducible.

## Future Requirements

- A new standalone control-center dashboard that replaces the existing route-local debugger model.
- Full user-customizable workspace layouts or per-user preference storage.
- Hosted collaboration, notifications, or background automation over triage decisions.

## Out of Scope

- A visual redesign disconnected from the operator-workflow gaps identified in current routes.
- Hosted workflow orchestration, notification services, or shared-user state.
- Browser-only state that cannot be reproduced through local artifacts or shareable URLs.
- Silent lifecycle execution or dataset mutation from UI-only actions.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TRIAGE-01 | Phase 113 | Complete |
| TRIAGE-02 | Phase 113 | Complete |
| DETAIL-01 | Phase 114 | Complete |
| DETAIL-02 | Phase 114 | Complete |
| DETAIL-03 | Phase 114 | Complete |
| ANALYSIS-01 | Phase 115 | Complete |
| ANALYSIS-02 | Phase 115 | Complete |
| SHELL-01 | Phase 115 | Complete |
| FLOW-01 | Phase 116 | Complete |
