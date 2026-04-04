# Requirements: v4.5 Dataset Evolution And Regression Pack Automation

**Defined:** 2026-04-04
**Core Value:** Make structured LLM failure analysis simple, reproducible, queryable,
interpretable, reusable, and actionable from local artifacts.

## v4.5 Requirements

### Regression Pack Generation

- [ ] **PACK-01**: User can generate a deterministic draft regression pack directly from a saved
  comparison using persisted signal context and explicit pack policies.
- [ ] **PACK-02**: Generated regression packs preserve full provenance for source comparison ids,
  signal verdicts, driver failure types, and case-level evidence references.

### Dataset Versioning

- [ ] **VERS-01**: User can create immutable versioned dataset artifacts from generated regression
  packs without mutating earlier versions.
- [ ] **VERS-02**: User can inspect version history for a dataset, including creation time, source
  comparisons, and parent-version lineage.

### Dataset Evolution

- [ ] **EVOL-01**: User can evolve an existing dataset from a new comparison and produce a new
  dataset version that composes fresh regressions with the prior curated pack.
- [ ] **EVOL-02**: Evolution policies remain deterministic, including stable top-N selection,
  failure-type filtering, and duplicate collapse.

### Debugger Support

- [ ] **UI-01**: Debugger users can generate regression packs from signal surfaces and inspect
  dataset version provenance without leaving the artifact-backed workflow.
- [ ] **UI-02**: Debugger dataset views link versioned pack contents back to the source
  comparison, signal summary, and case evidence that introduced each item.

### Workflow Verification

- [ ] **LOOP-01**: The end-to-end loop from comparison signal to generated/versioned dataset to
  rerun to compare is verified on local artifacts without custom handling.

## vNext Requirements

### Enforcement Automation

- **AUTO-01**: High-signal regressions can trigger pack generation automatically under explicit
  local policy.
- **POL-01**: Users can tune pack-growth, pruning, and ranking policies as dataset families evolve.
- **RECO-01**: The system can recommend which existing dataset family should absorb a new
  regression signal.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Hosted dataset registry or background automation service | `v4.5` keeps dataset evolution fully local and artifact-native |
| Opaque or learned pack-composition policies | Deterministic pack rules are required for reproducibility |
| Full browser-side dataset editor | Review and promotion remain explicit workflow steps, not a rich in-browser authoring surface |
| Silent mutation of existing dataset versions | History must remain immutable and auditable |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PACK-01 | Phase 89 | Pending |
| PACK-02 | Phase 89 | Pending |
| VERS-01 | Phase 90 | Pending |
| VERS-02 | Phase 90 | Pending |
| EVOL-01 | Phase 90 | Pending |
| EVOL-02 | Phase 90 | Pending |
| UI-01 | Phase 91 | Pending |
| UI-02 | Phase 91 | Pending |
| LOOP-01 | Phase 92 | Pending |

**Coverage:**
- v4.5 requirements: 9 total
- Mapped to phases: 9
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-04 for milestone v4.5*
