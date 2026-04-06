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

## Active Milestone: v5.1 Operator Workflow Clarity And Triage Surfaces

**Goal:** Make the debugger triage-first and action-oriented, so users can identify actionable
items earlier, keep decision-critical context visible while reviewing a comparison, and move
through analysis and workspace setup with less friction.

- [x] Phase 113 complete
- [x] Phase 114 complete
- [x] Phase 115 complete
### Phase 113: Comparison Inventory Triage And Priority Surfacing
- Status: complete
- Requirements: `TRIAGE-01`, `TRIAGE-02`
- Goal: surface governance, lifecycle, family, and priority context directly in the comparisons
  inventory with operator-first triage controls.
- Success criteria:
  - Users can identify urgent or actionable comparisons from inventory without opening each report.
  - Comparison inventory preserves compatibility and report identity while adding meaningful
    triage context.

### Phase 114: Comparison Detail Decision Surfaces And Operator Summary
- Status: complete
- Requirements: `DETAIL-01`, `DETAIL-02`, `DETAIL-03`
- Goal: restructure comparison detail so operator summary, recommendation, action, family state,
  and supporting evidence are easier to parse and navigate.
- Success criteria:
  - Key operator state remains visible while users scroll through comparison evidence.
  - Recommendation and family-history surfaces are decomposed enough to reduce cognitive overload
    on the detail route.

### Phase 115: Analysis Intent Presets And Workspace Orientation
- Status: complete
- Requirements: `ANALYSIS-01`, `ANALYSIS-02`, `SHELL-01`
- Goal: make `/analysis` and the shared shell intent-first, with preset entry points and clearer
  artifact-root/workspace orientation.
- Success criteria:
  - Users can launch common workflows from analysis without manually composing every filter.
  - The active artifact root and workspace source are explicit, inspectable, and easy to trust.

### Phase 116: Operator Workflow Verification And UI Stability
- Status: pending
- Requirements: `FLOW-01`
- Goal: verify the end-to-end local operator workflow across comparison inventory, detail review,
  analysis presets, and workspace context.
- Success criteria:
  - Verification proves the full `triage -> detail -> analysis` route loop is stable and
    reproducible on real artifacts.
  - New UI surfaces preserve shareability, route integrity, and artifact-grounded reasoning.

## Next Action

```bash
$gsd-discuss-phase 116
```

---
*Roadmap updated: 2026-04-06 after Phase 115 completion*
