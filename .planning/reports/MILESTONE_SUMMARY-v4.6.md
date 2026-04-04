# Milestone v4.6 — Project Summary

**Generated:** 2026-04-04
**Purpose:** Team onboarding and project review

---

## 1. Project Overview

`v4.6 Regression Governance And Recommendation Layer` turned regression enforcement from a manual
judgment call into a deterministic workflow over local artifacts.

Before this milestone, the system could:
- detect regressions through persisted comparison signals (`v4.4`)
- turn those signals into versioned regression packs and immutable dataset families (`v4.5`)

What was still missing was governance:
- which regressions deserve action
- whether to create a new dataset family or evolve an existing one
- how to explain those decisions
- how to review and apply them without opening every comparison by hand

`v4.6` closes that gap. A saved comparison can now produce a deterministic recommendation to
`create`, `evolve`, or `ignore`, that recommendation can be reviewed or applied from the CLI, and
the same recommendation is visible in the debugger on signal-focused surfaces.

The milestone stayed inside the project’s core product principles:
- filesystem artifacts remain the source of truth
- governance decisions are deterministic and locally inspectable
- no hosted policy service or opaque ranking model was added
- debugger surfaces render persisted governance payloads instead of recomputing policy client-side

## 2. Architecture & Technical Decisions

- **Decision:** Keep recommendation actions to a closed set: `create`, `evolve`, `ignore`.
  - **Why:** Governance needed to be deterministic, explainable, and easy to review across CLI and
    debugger surfaces.
  - **Phase:** 93

- **Decision:** Reuse regression-pack preview logic instead of creating a separate governance case
  selector.
  - **Why:** Governance recommendations should be based on the exact same deterministic case
    selection logic as dataset generation and evolution.
  - **Phase:** 93

- **Decision:** Keep policy local and typed, not hidden in config or learned behavior.
  - **Why:** Users need explicit control over minimum severity, top-N selection, failure-type
    filtering, family caps, and duplicate-growth thresholds.
  - **Phase:** 93

- **Decision:** Keep family matching intentionally narrow and inspectable.
  - **Why:** In `v4.6`, exact suggested-family matching plus family-health checks was enough to
    make governance reliable without introducing heuristic family ranking.
  - **Phase:** 93, 94

- **Decision:** Put governance under existing CLI namespaces rather than inventing a new top-level
  surface.
  - **Why:** `regressions` already represented raw signal inspection and `dataset` already
    represented dataset lifecycle operations, so governance fit naturally there.
  - **Phase:** 94

- **Decision:** Keep debugger surfacing on existing signal routes.
  - **Why:** The goal was to make governance visible where users already inspect signals:
    `/analysis?mode=signals` and comparison detail, not to create a new governance dashboard.
  - **Phase:** 95

- **Decision:** Make the backend bridge the source of truth for governance payloads.
  - **Why:** Policy evaluation belongs on the backend artifact side; the React app should only
    render persisted recommendation data and matched-family context.
  - **Phase:** 95

- **Decision:** Treat final verification as a workflow proof, not a new feature phase.
  - **Why:** The milestone needed to prove `compare -> recommend -> review/apply -> dataset action`
    on real artifacts, including repeat-apply stability and debugger payload availability.
  - **Phase:** 96

### Core Modules Introduced Or Extended

- [policy.py](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/policy.py)
  defines the governance policy contract and recommendation engine.
- [workflow.py](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/workflow.py)
  adds review/apply and family-health orchestration.
- [cli.py](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/cli.py)
  exposes `regressions recommend`, `regressions review`, `regressions apply`, and
  `dataset families`.
- [query_bridge.py](/Users/padraigobrien/model-failure-lab/scripts/query_bridge.py) and
  [vite.config.ts](/Users/padraigobrien/model-failure-lab/frontend/vite.config.ts) bridge
  persisted governance payloads into the debugger.
- [SignalDatasetAutomationPanel.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/components/datasets/SignalDatasetAutomationPanel.tsx)
  is the durable UI surface for matched-family context, preview cases, and follow-on dataset
  actions.

## 3. Phases Delivered

| Phase | Name | Status | One-Liner |
|-------|------|--------|-----------|
| 93 | Policy Contract And Recommendation Rules | Complete | Added deterministic governance recommendations and a write-free regression-pack preview seam. |
| 94 | Family Matching And Review/Apply CLI | Complete | Added family-health inspection and CLI recommend/review/apply workflows over saved comparison signals. |
| 95 | Debugger Recommendation Surfacing | Complete | Surfaced recommendation status, rationale, and matched-family context on analysis and comparison detail routes. |
| 96 | Governance Stability And Workflow Verification | Complete | Proved the full governance loop across fresh compare artifacts, repeat apply stability, and debugger smoke. |

## 4. Requirements Coverage

- ✅ `GOV-01`: saved comparisons now yield deterministic `create`, `evolve`, or `ignore`
  recommendations.
- ✅ `GOV-02`: every recommendation includes explicit rationale, policy rule, matched-family
  context, and evidence-linked preview data.
- ✅ `GOV-03`: policy inputs are configurable locally through the CLI.
- ✅ `REC-01`: recent recommendations can be reviewed without opening each comparison manually.
- ✅ `REC-02`: dry-run review remains inspectable before writing dataset artifacts.
- ✅ `REC-03`: governance decisions can be applied reproducibly to create or evolve datasets.
- ✅ `FAM-01`: dataset-family health is visible and explains why a family is actionable, capped,
  or duplicate-heavy.
- ✅ `FAM-02`: family matching remains deterministic across dataset identity, failure type,
  lineage, and overlap heuristics.
- ✅ `UI-01`: debugger signal surfaces now show recommendation status and policy rationale.
- ✅ `UI-02`: debugger users can inspect matched-family context and open source evidence from the
  recommendation surface.
- ✅ `FLOW-01`: the full governance loop is verified and reproducible on local artifacts.

**Audit verdict:** passed, from [v4.6-MILESTONE-AUDIT.md](/Users/padraigobrien/model-failure-lab/.planning/v4.6-MILESTONE-AUDIT.md).

## 5. Key Decisions Log

- **93 / Recommendation contract:** Governance uses only `create`, `evolve`, and `ignore`.
- **93 / Preview seam:** Governance reuses dataset evolution’s regression-pack preview path so
  recommendation and dataset composition stay aligned.
- **93 / Policy posture:** Thresholds, top-N, failure-type filters, family caps, and
  duplicate-growth guards are local and typed.
- **94 / CLI posture:** Governance lives under `regressions` and `dataset`, not a new command
  namespace.
- **94 / Apply posture:** `review` is read-only; `apply` recomputes and then materializes only
  actionable dataset changes in deterministic signal order.
- **95 / UI posture:** Recommendation surfaces stay on existing routes, especially `/analysis` in
  signal mode and comparison detail.
- **95 / Data-flow contract:** React renders governance payloads from the bridge; it does not
  compute policy.
- **96 / Verification posture:** Workflow proof must cover fresh comparison artifacts, repeat
  apply behavior, and debugger-visible governance payloads.

## 6. Tech Debt & Deferred Items

### Deferred To Later Milestones

- `ALERT-01`: proactive alert-style summaries for high-confidence governance decisions
- `AUTO-01`: unattended policy application across recent comparisons under explicit opt-in
- `HEALTH-01`: pruning, merge, or long-term family-health recommendations

### Known Boundaries Kept Intentionally Out Of Scope

- no hosted governance service or background worker
- no learned or opaque family recommendation model
- no silent file mutation without dry-run or inspectable policy basis
- no full browser-side dataset management workspace

### Practical Notes For Future Work

- Family matching is intentionally narrow in `v4.6`; it prefers exact suggested-family behavior
  plus health guards over richer cross-family ranking.
- The debugger intentionally surfaces governance on existing signal routes rather than a dedicated
  governance workspace, which keeps chrome low but limits multi-family bulk management.
- There is no retrospective artifact for this milestone, so lessons learned come from context,
  verification, and the audit rather than a dedicated postmortem document.

## 7. Getting Started

### Run The Project

Install the package and exercise the local artifact loop:

```bash
python3 -m pip install .
failure-lab demo
failure-lab run --dataset reasoning-failures-v1 --model demo
failure-lab report --run <run-id>
failure-lab compare <baseline-run-id> <candidate-run-id>
```

To open the debugger on a workspace:

```bash
export FAILURE_LAB_ARTIFACT_ROOT=/path/to/failure-lab-workspace
npm --prefix frontend run dev
```

### Governance Commands Added In v4.6

```bash
failure-lab regressions recommend --comparison <comparison-id> --root <workspace>
failure-lab regressions review --root <workspace>
failure-lab regressions apply --root <workspace>
failure-lab dataset families --root <workspace>
```

### Key Directories

- [src/model_failure_lab](/Users/padraigobrien/model-failure-lab/src/model_failure_lab): core engine, reporting, dataset evolution, and governance logic
- [frontend/src](/Users/padraigobrien/model-failure-lab/frontend/src): React debugger routes and UI components
- [scripts/query_bridge.py](/Users/padraigobrien/model-failure-lab/scripts/query_bridge.py): backend-to-debugger artifact bridge
- [tests/unit](/Users/padraigobrien/model-failure-lab/tests/unit): Python workflow and contract tests
- [.planning/milestones/v4.6-ROADMAP.md](/Users/padraigobrien/model-failure-lab/.planning/milestones/v4.6-ROADMAP.md): archived milestone plan

### Tests

Governance-focused verification:

```bash
python3 -m pytest tests/unit/test_regression_governance.py tests/unit/test_cli_governance.py tests/unit/test_cli_demo_compare.py -q
```

Frontend governance/debugger verification:

```bash
npm --prefix frontend run test -- --run src/app/__tests__/shell.test.tsx src/app/__tests__/runs.test.tsx src/app/__tests__/runDetail.test.tsx src/app/__tests__/comparisons.test.tsx src/app/__tests__/comparisonDetail.test.tsx src/app/__tests__/analysis.test.tsx
npm --prefix frontend run build
node frontend/scripts/smoke-real-artifacts.mjs --mode demo
```

### Where To Look First

- Start with [PROJECT.md](/Users/padraigobrien/model-failure-lab/.planning/PROJECT.md) for the
  current product shape.
- Read [v4.6-ROADMAP.md](/Users/padraigobrien/model-failure-lab/.planning/milestones/v4.6-ROADMAP.md)
  and [v4.6-REQUIREMENTS.md](/Users/padraigobrien/model-failure-lab/.planning/milestones/v4.6-REQUIREMENTS.md)
  for milestone scope.
- Then inspect [policy.py](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/policy.py),
  [workflow.py](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/workflow.py),
  [cli.py](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/cli.py),
  and [SignalDatasetAutomationPanel.tsx](/Users/padraigobrien/model-failure-lab/frontend/src/components/datasets/SignalDatasetAutomationPanel.tsx).

---

## Stats

- **Timeline:** 2026-04-04 18:17 IST → 2026-04-04 19:02 IST
- **Phases:** 4 / 4 complete
- **Commits:** 6 milestone commits
- **Implementation diff:** 22 files changed, +2104 / -75, excluding archive-only planning changes
- **Contributors:** Padraigobrien08

This summary is grounded in the archived roadmap, requirements, milestone audit, and phase
93-96 context, summary, and verification artifacts.
