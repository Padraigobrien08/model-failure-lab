# Roadmap: Model Failure Lab

## Archived Milestones

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

## Active Milestone: v4.4 Regression Detection And Signal Layer

**Goal:** Add a deterministic, artifact-native signal layer that scores comparisons, surfaces
meaningful regressions and improvements, and directs users to the most important behavior changes
without manual inspection.

### Phase 85: Comparison Signal Contract And Artifact Persistence
- Status: complete
- Requirements: `SIG-01`, `SIG-02`
- Goal: compute deterministic verdicts, scores, and top drivers at comparison time and persist
  them in comparison artifacts.
- Success criteria:
  - Every comparison produces a persisted signal block with verdict, regression score,
    improvement score, and top drivers.
  - Scores are derived deterministically from saved comparison data and do not depend on LLM
    behavior.
  - Top drivers identify the highest-impact failure-type deltas behind the verdict.

### Phase 86: CLI Signal Surfaces And Regression Listings
- Status: pending
- Requirements: `CLI-01`, `CLI-02`, `CLI-03`, `IDX-01`
- Goal: expose raw scores, deterministic summaries, thresholded alerts, and recent-regression
  listings over the persisted signal contract.
- Success criteria:
  - `failure-lab compare --score` emits the raw signal block.
  - `failure-lab compare --summary` emits a deterministic human-readable signal summary with
    evidence-linked drivers.
  - `failure-lab compare --alert` only emits when configured thresholds are exceeded.
  - Users can list recent regressions and improvements ordered by severity without manually opening
    each comparison.

### Phase 87: Debugger Severity Surfacing And Evidence Handoff
- Status: pending
- Requirements: `UI-01`, `UI-02`
- Goal: highlight signal severity, direction, and top drivers in comparison and analysis views
  before users open dense detail sections.
- Success criteria:
  - Comparison routes show regression/improvement badges, score displays, and top drivers.
  - The debugger links directly from signal surfaces into affected cases and existing detail views.
  - `/analysis` exposes a recent-regressions view with severity sorting and filtering by dataset or
    failure type.

### Phase 88: Signal Stability And Workflow Verification
- Status: pending
- Requirements: `VERF-01`
- Goal: prove that the signal layer is stable, reproducible, and useful across CLI and debugger
  workflows.
- Success criteria:
  - Signal outputs are stable across repeated rebuilds or reruns over the same artifacts.
  - Verification proves persisted comparison signals, CLI surfacing, and debugger severity
    rendering together.
  - Users can answer “what changed?” without opening dense detail views first.

## Next Action

```bash
$gsd-plan-phase 86
$gsd-execute-phase 86
```

---
*Roadmap updated: 2026-04-04 after Phase 85 completion*
