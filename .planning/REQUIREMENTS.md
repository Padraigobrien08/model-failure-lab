# Requirements: v5.3 Closed-Loop Outcome Attestation And Policy Feedback

**Defined:** 2026-04-06  
**Status:** Active

## v5.3 Requirements

### Outcome Attestation

- [ ] **ATTEST-01**: Users can list open execution follow-ups and attach resulting run and
  comparison artifacts to a specific execution receipt from the CLI.
- [ ] **ATTEST-02**: Users can finalize an execution outcome attestation with a persisted closure
  state, linked evidence, and operator notes without mutating family policy implicitly.

### Measured Outcome Verdicts

- [ ] **VERDICT-01**: The system computes a deterministic outcome verdict (`improved`,
  `regressed`, `inconclusive`, or `no_signal`) from linked follow-up comparison evidence.
- [ ] **VERDICT-02**: Every attested outcome preserves the compared signals, delta summary, and
  rationale used to reach the verdict.

### Policy Feedback

- [ ] **FEEDBACK-01**: Attested outcomes feed back into dataset-family history and portfolio
  priority context so operators can see whether prior actions helped.
- [ ] **FEEDBACK-02**: Future plan review and execution surfaces expose relevant prior attested
  outcomes for the same family or action type before new changes are applied.

### Debugger Outcome Closure

- [ ] **UI-01**: Existing debugger routes surface open follow-ups, attested verdicts, and
  action-effect timelines without introducing a separate outcome dashboard.
- [ ] **UI-02**: Users can move from an execution receipt to its linked follow-up evidence,
  measured verdict, and updated family or portfolio context without losing route locality.

### Workflow Verification

- [ ] **FLOW-01**: The full local workflow from triage to saved plan to explicit execution to
  rerun/compare to attested outcome to updated policy context is verified and reproducible.

## Future Requirements

- Automatic closure when matching rerun/compare artifacts appear without explicit operator review.
- Notifications or reminders for stale open follow-ups.
- Multi-user approval or sign-off workflows around attestation overrides or manual verdict changes.

## Out of Scope

- Background or scheduled outcome attestation without explicit operator review.
- Hosted orchestration, remote workers, or queue infrastructure for follow-up execution or
  closure.
- Learned policy tuning that rewrites deterministic governance behavior automatically from
  attested outcomes.
- A new standalone execution or outcomes dashboard that duplicates existing route-local debugger
  surfaces.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ATTEST-01 | Phase 121 | Planned |
| ATTEST-02 | Phase 121 | Planned |
| VERDICT-01 | Phase 122 | Planned |
| VERDICT-02 | Phase 122 | Planned |
| FEEDBACK-01 | Phase 123 | Planned |
| FEEDBACK-02 | Phase 123 | Planned |
| UI-01 | Phase 123 | Planned |
| UI-02 | Phase 123 | Planned |
| FLOW-01 | Phase 124 | Planned |
