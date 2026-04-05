# Requirements: v5.0 Portfolio Prioritization And Guided Lifecycle Planning

**Defined:** 2026-04-05  
**Status:** Active

## v5.0 Requirements

### Portfolio Priority

- [ ] **PORT-01**: Users can list dataset families in a deterministic priority order derived from
  escalation, recurrence, lifecycle health, and recent failure history.
- [ ] **PORT-02**: Portfolio priority items preserve explicit rationale and links back to the
  families, comparisons, clusters, and lifecycle actions that drove their rank.

### Guided Planning

- [ ] **PLAN-01**: The system can group related families or merge candidates into explicit planning
  units with deterministic rationale for why they should be reviewed together.
- [ ] **PLAN-02**: Users can generate a saved dry-run lifecycle plan that proposes a bounded set of
  actions without mutating any dataset family automatically.
- [ ] **PLAN-03**: Saved lifecycle plans preserve projected impact, dependencies, and the exact
  family-level actions they recommend so operators can step through them explicitly.

### CLI Surfaces

- [ ] **CLI-01**: Users can list and filter the portfolio queue and saved lifecycle plans from the
  CLI by family, model, failure type, actionability, or priority band.
- [ ] **CLI-02**: Users can inspect one queue item or saved plan with rationale, contributing
  evidence, and the proposed family-level actions.
- [ ] **CLI-03**: Users can promote one saved plan action into the existing explicit review/apply
  workflow without introducing background execution.

### Debugger Support

- [ ] **UI-01**: Existing debugger routes surface priority and plan context on affected family or
  comparison views without introducing a new control-center dashboard.
- [ ] **UI-02**: Users can drill from surfaced priority or plan items into the relevant family
  histories, clusters, comparisons, and lifecycle action evidence.

### Workflow Verification

- [ ] **FLOW-01**: The full local workflow from portfolio queue to saved plan to explicit
  review/apply to updated family state is verified and reproducible.

## Future Requirements

- Automatic execution of saved plans without an explicit user step.
- Background scheduling, notifications, or hosted escalation delivery.
- Multi-user coordination or approval workflows over shared lifecycle plans.

## Out of Scope

- Hosted prioritization services, queues, or orchestration backends.
- Learned ranking or opaque portfolio scoring that cannot be reproduced from local artifacts.
- A separate browser-side planning workspace that duplicates existing debugger routes.
- Silent mutation of dataset families from plan generation alone.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PORT-01 | Phase 109 | Planned |
| PORT-02 | Phase 109 | Planned |
| PLAN-01 | Phase 109 | Planned |
| PLAN-02 | Phase 110 | Planned |
| PLAN-03 | Phase 110 | Planned |
| CLI-01 | Phase 110 | Planned |
| CLI-02 | Phase 110 | Planned |
| CLI-03 | Phase 110 | Planned |
| UI-01 | Phase 111 | Planned |
| UI-02 | Phase 111 | Planned |
| FLOW-01 | Phase 112 | Planned |
