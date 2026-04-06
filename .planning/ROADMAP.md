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

## Active Milestone: v5.2 Guided Plan Execution And Outcome Verification

**Goal:** Turn saved lifecycle plans into an explicit, checkpointed execution workflow with
outcome verification, so operators can safely act on portfolio decisions and measure whether those
actions improved behavior.

### Phase 117: Execution Contract And Preflight Checks
- Status: complete
- Requirements: `EXEC-01`, `VERIFY-01`
- Goal: define the persisted execution and preflight contract over saved plans, planned lifecycle
  actions, and before/after state capture.
- Success criteria:
  - Operators can validate a plan before execution and see blockers without mutating any dataset
    family.
  - Execution records preserve enough state to inspect what changed before and after each action.

### Phase 118: CLI Plan Execution, Checkpoints, And Rollback Receipts
- Status: complete
- Requirements: `EXEC-02`, `EXEC-03`, `VERIFY-02`
- Goal: expose explicit saved-plan execution, checkpoint progression, compensating-action
  receipts, and rerun/compare handoff through the CLI.
- Success criteria:
  - Operators can execute or resume a saved plan in bounded steps or batches with persisted
    checkpoint state.
  - Failed or interrupted execution produces inspectable receipts and clear follow-up options,
    including rerun/compare preparation.

### Phase 119: Debugger Execution Context And Before/After Outcome Views
- Status: complete
- Requirements: `UI-01`, `UI-02`
- Goal: surface execution status, receipts, and outcome deltas on existing debugger routes.
- Success criteria:
  - Existing comparison and family surfaces show execution status and before/after state without
    becoming a separate dashboard.
  - Users can drill from execution context into the originating plan, affected family state, and
    post-execution evidence.

### Phase 120: Workflow Verification And Stability
- Status: complete
- Requirements: `FLOW-01`
- Goal: verify the full local workflow from triage to saved plan to explicit execution to
  rerun/compare and updated family state.
- Success criteria:
  - Verification proves the full `triage -> plan -> execute -> rerun -> compare -> updated state`
    loop is stable and reproducible.
  - Execution receipts, checkpoints, and outcome snapshots remain deterministic and inspectable
    across rebuilds.

## Next Action

```bash
$gsd-complete-milestone
```

---
*Roadmap updated: 2026-04-06 for v5.2 completion*
