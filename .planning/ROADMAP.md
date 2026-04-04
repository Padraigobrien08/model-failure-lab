# Roadmap: Model Failure Lab

## Archived Milestones

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

## Active Milestone: v4.6 Regression Governance And Recommendation Layer

**Goal:** Turn regression enforcement from manual dataset-evolution decisions into deterministic,
policy-driven recommendations and review/apply workflows.

### Phase 93: Policy Contract And Recommendation Rules
- Status: complete
- Requirements: `GOV-01`, `GOV-02`, `GOV-03`
- Goal: define the deterministic governance-policy contract and produce stable recommendation output
  for saved comparison signals.
- Success criteria:
  - A saved comparison yields a deterministic `create`, `evolve`, or `ignore` recommendation.
  - Recommendation output includes explicit rationale, severity basis, matched family, and
    evidence-linked context.
  - Governance policy inputs such as severity threshold, top-N, failure-type filter, family cap,
    and growth rules are local and inspectable.

### Phase 94: Family Matching And Review/Apply CLI
- Status: complete
- Requirements: `REC-01`, `REC-02`, `REC-03`, `FAM-01`, `FAM-02`
- Goal: add family matching plus recent-signal review and apply flows in the CLI.
- Success criteria:
  - Users can review recent recommendations without opening every comparison manually.
  - Dry-run and apply modes stay reproducible and inspectable before writing dataset artifacts.
  - Family matching and family-health reporting are deterministic across lineage, overlap, and
    policy rules.

### Phase 95: Debugger Recommendation Surfacing
- Status: ready
- Requirements: `UI-01`, `UI-02`
- Goal: surface recommendation status, rationale, and matched-family context directly on debugger
  signal views.
- Success criteria:
  - Signal surfaces show recommendation status and rationale before dense inspection.
  - Users can inspect matched-family context and open relevant source or family evidence directly
    from the debugger.

### Phase 96: Governance Stability And Workflow Verification
- Status: pending
- Requirements: `FLOW-01`
- Goal: prove the full governance loop from comparison signal to recommendation to applied dataset
  action.
- Success criteria:
  - Governance decisions remain deterministic and reproducible across repeated runs.
  - Applied decisions generate stable dataset actions over local artifacts.
  - Verification proves the full `compare -> recommend -> review/apply -> dataset action` loop.

## Next Action

```bash
$gsd-discuss-phase 95
$gsd-plan-phase 95
```

---
*Roadmap updated: 2026-04-04 after Phase 94 completion*
