# Requirements: v4.6 Regression Governance And Recommendation Layer

**Defined:** 2026-04-04
**Core Value:** Make structured LLM failure analysis simple, reproducible, queryable,
interpretable, reusable, and actionable from local artifacts.

## v4.6 Requirements

### Governance Policy

- [ ] **GOV-01**: User can evaluate a saved comparison and receive a deterministic recommendation to
  `create`, `evolve`, or `ignore`.
- [ ] **GOV-02**: Every governance recommendation includes explicit rationale covering severity,
  matched family (if any), policy rule, and evidence-linked context.
- [ ] **GOV-03**: User can configure or select local governance policy inputs such as minimum
  severity, top-N limits, failure-type filters, family caps, and duplicate-growth controls.

### Review And Apply

- [ ] **REC-01**: User can review recommended actions across recent saved comparisons without
  opening each comparison manually.
- [ ] **REC-02**: User can dry-run governance application and inspect proposed dataset actions
  before any files are written.
- [ ] **REC-03**: User can apply governance decisions reproducibly to generate or evolve datasets
  from recent signals.

### Family Matching And Health

- [ ] **FAM-01**: User can inspect dataset-family health and see why a family was chosen, skipped,
  or capped for a signal.
- [ ] **FAM-02**: Family matching remains deterministic across dataset identity, failure type,
  lineage, and overlap heuristics.

### Debugger Support

- [ ] **UI-01**: Debugger signal surfaces show recommendation status and policy rationale without
  requiring detailed route drilldown.
- [ ] **UI-02**: Debugger users can inspect matched-family context and open the relevant family or
  source signal evidence from the recommendation surface.

### Workflow Verification

- [ ] **FLOW-01**: The governance loop from comparison signal to recommendation to applied dataset
  action is verified and reproducible on local artifacts.

## vNext Requirements

### Enforcement Automation

- **ALERT-01**: High-confidence governance decisions can emit proactive alert-style summaries over
  recent comparisons.
- **AUTO-01**: Approved governance policies can apply unattended across recent comparisons under
  explicit local opt-in.
- **HEALTH-01**: Dataset-family governance can recommend pruning or merge actions when packs drift
  beyond healthy size or signal quality.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Hosted governance service or background worker | `v4.6` keeps recommendation and apply flows fully local |
| Learned ranking or opaque family recommendation models | Governance decisions must stay deterministic and explainable |
| Automatic file mutation without dry-run or inspectable policy basis | Users need explicit reviewable governance before writes |
| Full browser-side dataset management workspace | UI support stays lightweight and signal-surface oriented |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GOV-01 | Phase 93 | Pending |
| GOV-02 | Phase 93 | Pending |
| GOV-03 | Phase 93 | Pending |
| REC-01 | Phase 94 | Pending |
| REC-02 | Phase 94 | Pending |
| REC-03 | Phase 94 | Pending |
| FAM-01 | Phase 94 | Pending |
| FAM-02 | Phase 94 | Pending |
| UI-01 | Phase 95 | Pending |
| UI-02 | Phase 95 | Pending |
| FLOW-01 | Phase 96 | Pending |

**Coverage:**
- v4.6 requirements: 11 total
- Mapped to phases: 11
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-04 for milestone v4.6*
