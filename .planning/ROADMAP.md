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

## Active Milestone: v4.8 Recurring Failure Clusters And Pattern Mining

**Goal:** Add deterministic recurring-failure clusters so the system can tell when the same
underlying problem is coming back across runs, comparisons, and governance decisions.

### Phase 101: Cluster Contract And Stable Identity
- Status: ready
- Requirements: `CLUSTER-01`, `CLUSTER-02`
- Goal: define stable deterministic cluster identity over saved failures, deltas, and recurring
  temporal context.
- Success criteria:
  - The same recurring behavior maps to the same stable cluster id across compatible artifact
    history.
  - Cluster identity remains fully local, reproducible, and artifact-derived.

### Phase 102: Cluster Summaries And CLI Surfaces
- Status: pending
- Requirements: `SUMMARY-01`, `SUMMARY-02`, `CLI-01`, `CLI-02`
- Goal: expose cluster summaries, representative evidence, and detailed cluster history in the
  CLI.
- Success criteria:
  - Users can list and filter clusters without opening individual comparisons manually.
  - Users can inspect one cluster’s recurrence, severity, affected models/datasets, and evidence
    cases.

### Phase 103: Debugger Cluster Surfacing And Evidence Drillthrough
- Status: pending
- Requirements: `UI-01`, `UI-02`
- Goal: surface cluster context on existing debugger routes and allow drillthrough into source
  evidence.
- Success criteria:
  - Analysis and comparison surfaces show recurring cluster context without becoming dashboard-like.
  - Users can move from a surfaced cluster directly into representative evidence and source routes.

### Phase 104: Governance Cluster Context And Workflow Verification
- Status: pending
- Requirements: `GOV-01`, `FLOW-01`
- Goal: thread recurring cluster context into governance rationale and verify the full local
  workflow.
- Success criteria:
  - Governance recommendations can explain that a change belongs to a recurring cluster, not just a
    one-off regression.
  - Verification proves the full `history -> cluster -> governance -> debugger evidence` loop.

## Next Action

```bash
$gsd-discuss-phase 101
$gsd-plan-phase 101
```

---
*Roadmap updated: 2026-04-04 for milestone v4.8 initialization*
