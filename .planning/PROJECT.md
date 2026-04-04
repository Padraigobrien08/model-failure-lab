# Model Failure Lab

## What This Is

Model Failure Lab is a local, artifact-native system for evaluating, debugging, comparing,
querying, interpreting, harvesting, replaying, and now enforcing LLM failures. It is built around
reproducible filesystem artifacts, a CLI-first workflow, and a React debugger that reads the same
saved artifact contract.

## Current State

- Latest shipped milestone: `v4.5`
- Active milestone: none
- Primary public surface:
  - [failure-lab CLI](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/cli.py)
- Secondary surfaces:
  - [React Failure Debugger](/Users/padraigobrien/model-failure-lab/frontend)
  - [artifact query bridge](/Users/padraigobrien/model-failure-lab/scripts/query_bridge.py)
- Operational status:
  - `v1.8` shipped the real engine loop: `demo`, `run`, `report`, and `compare`
  - `v1.9` added bundled datasets plus richer single-run and comparison reports
  - `v2.0` and `v2.1` rebuilt the debugger on real artifacts with deep-linkable state and exact
    drillthrough
  - `v3.0` made the package install-first and added Ollama over the shared artifact contract
  - `v4.0` widened adapter reach and optional extras without changing the debugger contract
  - `v4.1` added a derived local query/index layer and a query-backed `/analysis` route
  - `v4.2` added grounded heuristic and opt-in LLM insight reports in the CLI and debugger
  - `v4.3` added failure harvesting, deterministic dataset promotion, debugger export, and a
    proven replay loop
  - `v4.4` added deterministic regression/improvement signals with CLI and debugger severity views
  - `v4.5` turned those signals into versioned regression packs, immutable family evolution, and
    enforced replay loops

## Latest Completed Milestone: v4.5 Dataset Evolution And Regression Pack Automation

**Goal:** Turn detected regressions into versioned evaluation datasets that evolve deterministically
from real comparison signals.

**Delivered:**
- Deterministic draft regression-pack generation directly from saved comparison signals.
- Immutable dataset-family evolution with stable duplicate collapse, lineage metadata, and CLI
  history inspection.
- Debugger enforcement surfaces on comparison detail and `/analysis` signal views for generate,
  evolve, and version-history inspection.
- End-to-end enforcement proof across Python workflow tests, frontend regressions, production
  build, and real-artifact smoke.

## Current Milestone

No active milestone. The repository is ready for the next planning cycle.

## Next Milestone Goals

- Use evolving regression packs to drive more proactive alerting and enforcement workflows.
- Add pack-policy tuning and recommendation layers over recurring signal clusters.
- Strengthen dataset governance around growth, pruning, and long-term pack quality.

## Core Value

Make structured LLM failure analysis simple, reproducible, queryable, interpretable, reusable,
and actionable from local artifacts.

## Requirements

### Validated

- ✓ Reproducible benchmark-first research workflow and robustness closeout — `v1.0` to `v1.4`
- ✓ React debugger surfaces over saved artifacts — `v1.5`, `v1.7`
- ✓ CLI-first failure analysis engine with canonical artifact contract — `v1.8`
- ✓ Bundled datasets, richer reports, and engine-first quickstart — `v1.9`
- ✓ Artifact-backed debugger over real runs and comparisons with operational drillthrough — `v2.0`,
  `v2.1`
- ✓ Install-first package flow plus debugger-compatible Ollama artifacts — `v3.0`
- ✓ Query/index layer over saved artifacts and query-backed debugger analysis — `v4.1`
- ✓ Grounded insight reports, `query --summarize`, `compare --explain`, and debugger insight
  panels — `v4.2`
- ✓ Failure harvesting, deterministic dataset promotion, debugger export, and replay-loop proof —
  `v4.3`
- ✓ Deterministic signal scoring, CLI change surfacing, debugger severity views, and workflow
  stability proof — `v4.4`
- ✓ Signal-driven regression-pack generation, immutable dataset evolution, debugger enforcement
  surfaces, and enforced replay-loop proof — `v4.5`

### Out of Scope

- Hosted services, background workers, or external dataset automation pipelines.
- Learned or opaque pack-composition policies replacing deterministic rules.
- A full browser-side dataset editor; dataset evolution remains lightweight and route-local.
- Silent mutation of published dataset versions.

## Context

- The product now covers execution, reporting, comparison, query, grounded interpretation,
  harvesting, signal scoring, and versioned regression-pack enforcement over local artifacts.
- `v4.3` proved users can turn saved failures into curated datasets, but the capture step was still
  explicit and manual.
- `v4.4` proved the system can identify what changed and how severe it is without manual
  comparison-by-comparison inspection.
- `v4.5` proved those regressions can become future evaluation inputs automatically and traceably.
- The next product pressure is policy and governance:
  how packs should grow, merge, alert, and stay high-signal over time.

## Constraints

- **Storage:** Filesystem artifacts remain canonical.
- **Determinism:** Pack composition and versioning rules must be reproducible from local artifacts.
- **Immutability:** Published dataset versions cannot be rewritten in place.
- **Grounding:** Generated packs must retain provenance back to source comparisons, signals, and
  cases.
- **Compatibility:** Evolved datasets must run through the standard engine and debugger surfaces
  unchanged.
- **Complexity:** Keep the next milestone local and artifact-native unless a real structural limit
  forces broader infrastructure.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep JSON artifacts as the product truth and add only derived local query/index layers | Reproducibility and inspectability matter more than infra breadth | ✓ Validated in `v4.1` |
| Make grounded interpretation opt-in richer, but deterministic by default | Heuristic, testable behavior should remain the base contract | ✓ Validated in `v4.2` |
| Turn harvested failures into first-class datasets rather than one-off exports | Reuse matters only if failures re-enter the evaluation loop cleanly | ✓ Validated in `v4.3` |
| Keep debugger export lightweight and route-local | Review and promotion belong in explicit lifecycle steps, not a browser editor | ✓ Validated in `v4.3` |
| Compute change signals deterministically from comparison artifacts before any LLM enrichment | Users need stable quantitative answers to “what changed?” first | ✓ Validated in `v4.4` |
| Persist signal blocks directly in comparison artifacts and expose them through CLI and debugger | Signals should be artifact-native and queryable without new infrastructure | ✓ Validated in `v4.4` |
| Turn high-signal regressions into generated dataset packs instead of alert-only outputs | Enforcement only matters if regressions become future evaluation inputs | ✓ Validated in `v4.5` |
| Make dataset versions immutable and explicitly linked to source signals and comparisons | Evolution needs traceability and reproducibility, not silent mutation | ✓ Validated in `v4.5` |

---
*Last updated: 2026-04-04 after v4.5 completion*
