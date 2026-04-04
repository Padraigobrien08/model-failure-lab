# Roadmap: Model Failure Lab

## Archived Milestones

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

## Active Milestone: v4.7 Model Behavior Tracking And Dataset Health Over Time

**Goal:** Add deterministic temporal tracking so the system can understand model behavior, dataset
health, and recurring regressions across time, not just one comparison at a time.

### Phase 97: History Index And Timeline Contract
- Status: ready
- Requirements: `HIST-01`, `HIST-02`
- Goal: add the artifact-derived history contract for ordered run, comparison, and dataset-family
  timelines.
- Success criteria:
  - Users can retrieve ordered history by dataset, model, or family from local artifacts.
  - Timeline records remain reproducible and derive only from saved artifact state.

### Phase 98: Deterministic Trend And Recurrence Signals
- Status: pending
- Requirements: `TREND-01`, `TREND-02`, `HEALTH-01`
- Goal: compute deterministic trend, volatility, recurrence, and dataset-health signals over
  recent history.
- Success criteria:
  - Trend labels like `improving`, `degrading`, and `stable` are computed from recent history.
  - Recurring regressions and volatility indicators are exposed deterministically.
  - Dataset health summarizes whether a versioned pack is helping, stale, or unstable over time.

### Phase 99: CLI History Surfaces And Governance Context
- Status: pending
- Requirements: `CLI-01`, `GOV-01`
- Goal: expose history and trend context in the CLI and thread that context into governance
  decisions.
- Success criteria:
  - Users can inspect history via CLI by dataset, model, or family.
  - Governance can incorporate historical context while preserving deterministic policy output.

### Phase 100: Debugger Timeline Views And Workflow Verification
- Status: pending
- Requirements: `UI-01`, `FLOW-01`
- Goal: surface lightweight timeline views in the debugger and prove the full time-aware workflow.
- Success criteria:
  - Existing debugger routes show trend and timeline context without a dashboard rewrite.
  - Verification proves the full `history -> trend -> governance context` loop over local
    artifacts.

## Next Action

```bash
$gsd-discuss-phase 97
$gsd-plan-phase 97
```

---
*Roadmap updated: 2026-04-04 for milestone v4.7 initialization*
