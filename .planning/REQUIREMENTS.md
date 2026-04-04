# Requirements: v4.4 Regression Detection And Signal Layer

**Defined:** 2026-04-04
**Core Value:** Make behavior changes explicit, deterministic, and actionable from local
comparison artifacts.

## v4.4 Requirements

### Comparison Signal Contract

- [x] **SIG-01**: Every comparison artifact persists a deterministic signal block with explicit
  verdict, regression score, improvement score, and top drivers.
- [x] **SIG-02**: Signal scoring and top-driver detection are reproducible from saved comparison
  artifacts and remain independent of LLM behavior.

### CLI Signal Surfaces

- [x] **CLI-01**: User can inspect raw comparison signal output with `failure-lab compare A B --score`.
- [x] **CLI-02**: User can inspect a deterministic human-readable signal summary with
  `failure-lab compare A B --summary`, including top drivers and case-level evidence references.
- [x] **CLI-03**: User can emit thresholded alert-style output with `failure-lab compare A B --alert`.
- [x] **IDX-01**: User can list recent regressions or improvements ordered by severity without
  manually opening each saved comparison.

### Debugger Signal Layer

- [ ] **UI-01**: Comparison debugger views show verdict, severity score, top contributing failure
  types, and direct links to affected evidence.
- [ ] **UI-02**: `/analysis` supports a recent-regressions view with severity sorting and filtering
  by failure type or dataset.

### Stability And Verification

- [ ] **VERF-01**: Signal outputs remain stable and reproducible across repeated runs over the same
  artifacts, and verification proves users can identify meaningful changes without opening dense
  detail views first.

## vNext Requirements

### Signal Automation

- **AUTO-01**: High-signal regressions can automatically seed harvested regression packs.
- **VERS-01**: Curated harvested packs can version and evolve as signal patterns change over time.
- **RECO-01**: The system can recommend next inspection or dataset actions from recurring signal
  patterns.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Hosted alerts, schedulers, or background workers | `v4.4` keeps signals fully local and artifact-native |
| Learned regression scoring models | Deterministic quantitative scoring is the first bar |
| Natural-language alerting as the primary interface | Users need explicit quantitative surfaces first |
| Provider-specific signal UI branches | The signal layer must reuse the shared debugger surfaces |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SIG-01 | Phase 85 | Complete |
| SIG-02 | Phase 85 | Complete |
| CLI-01 | Phase 86 | Complete |
| CLI-02 | Phase 86 | Complete |
| CLI-03 | Phase 86 | Complete |
| IDX-01 | Phase 86 | Complete |
| UI-01 | Phase 87 | Pending |
| UI-02 | Phase 87 | Pending |
| VERF-01 | Phase 88 | Pending |

**Coverage:**
- v4.4 requirements: 9 total
- Mapped to phases: 9
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-04 for milestone v4.4*
