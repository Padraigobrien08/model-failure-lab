# Requirements: v4.8 Recurring Failure Clusters And Pattern Mining

**Defined:** 2026-04-04
**Core Value:** Make structured LLM failure analysis simple, reproducible, queryable,
interpretable, reusable, actionable, time-aware, and now pattern-aware from local artifacts.

## v4.8 Requirements

### Cluster Contract

- [ ] **CLUSTER-01**: The system assigns stable deterministic cluster identities to recurring
  failure behaviors across runs and comparisons.
- [ ] **CLUSTER-02**: Cluster identity remains artifact-derived, reproducible, and local, with no
  learned or hosted clustering dependency.

### Cluster Summaries

- [ ] **SUMMARY-01**: Users can inspect cluster summaries including recurrence count, affected
  datasets/models, recent severity, and representative evidence cases.
- [ ] **SUMMARY-02**: Cluster summaries preserve evidence links back to source cases,
  comparisons, and runs.

### CLI Surfaces

- [ ] **CLI-01**: Users can list and filter recurring clusters from the CLI.
- [ ] **CLI-02**: Users can inspect one cluster’s detailed history and representative evidence from
  the CLI.

### Debugger Support

- [ ] **UI-01**: The debugger surfaces recurring cluster context on existing analysis or comparison
  routes without introducing a new dashboard-style workspace.
- [ ] **UI-02**: Users can drill from a surfaced cluster directly into representative evidence and
  source artifact routes.

### Governance Context

- [ ] **GOV-01**: Governance recommendations can include recurring cluster context as explicit,
  deterministic rationale.

### Workflow Verification

- [ ] **FLOW-01**: The full local workflow from artifact history to recurring cluster to governance
  and debugger evidence handoff is verified and reproducible.

## vNext Requirements

### Proactive Actions

- **ALERT-01**: High-confidence recurring clusters can drive alert-style summaries under explicit
  local policy.
- **PRUNE-01**: Cluster history can inform dataset-family pruning or consolidation decisions.
- **AUTO-01**: Stable recurring clusters can seed proactive recommendations without requiring a
  fresh comparison-led review every time.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Embedding-based or learned clustering | `v4.8` keeps pattern mining deterministic and inspectable |
| Hosted vector store, search backend, or background worker | Clustering stays fully local and artifact-native |
| Full dashboard-style cluster workspace | UI stays route-local and lightweight |
| Opaque automatic governance mutation from clusters alone | Clusters should inform decisions before they automate them |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CLUSTER-01 | Phase 101 | Pending |
| CLUSTER-02 | Phase 101 | Pending |
| SUMMARY-01 | Phase 102 | Pending |
| SUMMARY-02 | Phase 102 | Pending |
| CLI-01 | Phase 102 | Pending |
| CLI-02 | Phase 102 | Pending |
| UI-01 | Phase 103 | Pending |
| UI-02 | Phase 103 | Pending |
| GOV-01 | Phase 104 | Pending |
| FLOW-01 | Phase 104 | Pending |

**Coverage:**
- v4.8 requirements: 10 total
- Mapped to phases: 10
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-04 for milestone v4.8*
