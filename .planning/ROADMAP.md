# Roadmap: Model Failure Lab

## Archived Milestones

- [x] `v4.7` Model Behavior Tracking And Dataset Health Over Time - shipped 2026-04-04;
  artifact-derived history timelines, deterministic trend and dataset-health signals,
  history-aware governance context, and time-aware debugger surfacing with workflow proof.
- [x] `v4.6` Regression Governance And Recommendation Layer - shipped 2026-04-04; deterministic
  create/evolve/ignore recommendations, governance review/apply CLI, debugger recommendation
  surfacing, and end-to-end governance workflow proof.
- [x] `v4.5` Dataset Evolution And Regression Pack Automation - shipped 2026-04-04; deterministic
  regression-pack generation, immutable dataset-family evolution, debugger enforcement surfaces,
  and end-to-end enforcement-loop proof.
- [x] `v4.4` Regression Detection And Signal Layer - shipped 2026-04-04; deterministic comparison
  signals, CLI score/summary/alert surfaces, debugger severity views, and workflow-stability
  proof.
- [x] `v4.3` Failure Harvesting And Dataset Pack Generation - shipped 2026-04-04; harvest draft
  dataset packs, deterministic review/promotion, debugger export, and replay-loop proof.
- [x] `v4.2` Insight Layer And Grounded Failure Interpretation - shipped 2026-04-03; heuristic and
  opt-in LLM insight reports, debugger insight panels, and grounded evidence drillthrough.
- [x] `v4.1` Artifact Query And Cross-Run Analysis Layer - shipped 2026-04-03; derived local
  query index, structured query CLI, and query-backed analysis view.
- [x] [v3.0 Packaged Engine And Ollama Adapter Reach](/Users/padraigobrien/model-failure-lab/.planning/milestones/v3.0-ROADMAP.md) - shipped 2026-04-03; installable CLI path, built-in Ollama adapter, and debugger compatibility proof across packaged and Ollama artifacts.
- [x] [v2.1 Cross-Artifact Drillthrough And Debugger Operability](/Users/padraigobrien/model-failure-lab/.planning/milestones/v2.1-ROADMAP.md) - shipped 2026-04-02; deep-linkable detail state, exact comparison-to-run drillthrough, singular route provenance, strong active-case cues, and explicit workflow proof.
- [x] [v2.0 React Debugger On Real Artifacts](/Users/padraigobrien/model-failure-lab/.planning/milestones/v2.0-ROADMAP.md) - shipped 2026-03-31; artifact-backed runs/comparisons debugger, denser guided inspection, and audit-clean UI milestone closure.
- [x] [v1.9 Failure Dataset Packs And Report Quality](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.9-ROADMAP.md) - shipped 2026-03-30; bundled datasets, shared taxonomy, richer run/comparison reporting, and engine-first quickstart.
- [x] [v1.8 Core Failure Analysis Engine](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.8-ROADMAP.md) - shipped 2026-03-30; CLI-first engine, canonical artifacts, reporting, comparison, and zero-config demo.
- [x] [v1.7 Trace-First Failure Debugger Rebuild](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.7-ROADMAP.md) - shipped 2026-03-27; strict `Summary -> Lane -> Method -> Run -> Raw` route chain.
- [x] [v1.5 React Failure Debugger UI](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.5-ROADMAP.md) - shipped 2026-03-25; first React debugger over saved artifacts.
- [x] [v1.4 Final Robustness Attempt Before Expansion](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.4-ROADMAP.md) - shipped 2026-03-25; final robustness closeout and expansion gate.
- [x] [v1.3 Artifact-Driven Results UI And Robustness Consolidation](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.3-ROADMAP.md) - shipped 2026-03-24; artifact index and read-only results explorer.
- [x] [v1.2 Seed Stability And Reweighting Validation](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.2-ROADMAP.md) - shipped 2026-03-22; seeded cohorts and mitigation stability work.
- [x] [v1.1 Live Benchmark Validation And Research Packaging](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.1-ROADMAP.md) - shipped 2026-03-20; real-run validation and reproducibility packaging.
- [x] [v1.0 MVP](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.0-ROADMAP.md) - shipped 2026-03-20; benchmark pipeline, baselines, evaluation, and reporting contract.

- [x] `v4.8` Recurring Failure Clusters And Pattern Mining - shipped 2026-04-04; deterministic
  recurring cluster identity, cluster CLI/detail/history surfaces, lightweight debugger cluster
  context, and governance rationale enriched with recurring cluster evidence.
- [x] `v4.9` Proactive Escalation And Dataset Lifecycle Management - shipped 2026-04-05;
  deterministic escalation statuses, lifecycle review/apply CLI, debugger lifecycle surfacing,
  and full `history -> cluster -> escalation -> lifecycle action -> family state` proof.
- [x] `v5.0` Portfolio Prioritization And Guided Lifecycle Planning - shipped 2026-04-05;
  deterministic portfolio ranking, saved guided lifecycle plans, explicit plan promotion, and
  route-local debugger plan context.
- [x] `v5.1` Operator Workflow Clarity And Triage Surfaces - shipped 2026-04-06; triage-first
  comparison inventory context, sticky operator summary, URL-backed analysis presets, stronger
  workspace orientation, and verified `triage -> detail -> analysis` route stability.
- [x] `v5.2` Guided Plan Execution And Outcome Verification - shipped 2026-04-06; saved-plan
  preflight, checkpointed execution receipts, rollback and rerun/compare guidance, and route-local
  debugger outcome context.

## Active Milestone: v5.3 Closed-Loop Outcome Attestation And Policy Feedback

**Goal:** Turn post-execution follow-up into explicit, persisted outcome closure, so operators can
prove whether a lifecycle action helped and feed that result back into future policy decisions.

### Phase 121: Outcome Attestation Contract And Evidence Linking
- Status: pending
- Requirements: `ATTEST-01`, `ATTEST-02`
- Goal: define the persisted attestation contract over execution receipts, open follow-ups, linked
  rerun artifacts, and explicit closure state.
- Success criteria:
  - Operators can identify open follow-ups and attach resulting run and comparison evidence to a
    specific executed action.
  - Attestation records preserve linked evidence and closure status without silently changing
    family policy.

### Phase 122: Measured Verdicts And CLI Outcome Closure
- Status: pending
- Requirements: `VERDICT-01`, `VERDICT-02`
- Goal: compute deterministic measured verdicts from linked evidence and expose explicit CLI
  closure flows for outcome attestation.
- Success criteria:
  - The system can derive `improved`, `regressed`, `inconclusive`, or `no_signal` from follow-up
    comparison evidence and persist the basis for that verdict.
  - CLI users can finalize an outcome closure and inspect the exact deltas and rationale behind
    it.

### Phase 123: Policy Feedback And Debugger Outcome Timelines
- Status: pending
- Requirements: `FEEDBACK-01`, `FEEDBACK-02`, `UI-01`, `UI-02`
- Goal: feed attested outcomes back into family and portfolio context while surfacing open and
  closed outcomes on existing debugger routes.
- Success criteria:
  - Family history, portfolio views, and future plan or execution review surfaces reflect relevant
    prior attested outcomes.
  - Existing debugger routes show open follow-ups, outcome verdicts, and action-effect timelines
    without becoming a separate dashboard.

### Phase 124: Workflow Verification And Stability
- Status: pending
- Requirements: `FLOW-01`
- Goal: verify the full local workflow from triage to plan to execute to attested outcome and
  updated policy context.
- Success criteria:
  - Verification proves the full `triage -> plan -> execute -> rerun -> compare -> attest outcome
    -> updated context` loop is stable and reproducible.
  - Outcome linking, measured verdicts, and policy feedback remain deterministic and inspectable
    across rebuilds.

## Next Action

```bash
$gsd-discuss-phase 121
```

---
*Roadmap updated: 2026-04-06 for v5.3 initialization*
