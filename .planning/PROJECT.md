# Model Failure Lab

## What This Is

Model Failure Lab is a local, artifact-native system for evaluating, debugging, comparing,
querying, interpreting, harvesting, and replaying LLM failures. It is built around reproducible
filesystem artifacts, a CLI-first workflow, and a React debugger that reads the same saved
artifact contract.

## Current State

- Latest shipped milestone: `v4.4`
- Active milestone: `v4.5 Dataset Evolution And Regression Pack Automation`
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
  - `v4.5` will turn those signals into versioned regression packs and evolving datasets

## Latest Completed Milestone: v4.4 Regression Detection And Signal Layer

**Goal:** Make behavior changes explicit, deterministic, and actionable from local comparison
artifacts.

**Delivered:**
- Persisted comparison signal blocks with deterministic verdict, regression score, improvement
  score, and top failure-type drivers.
- CLI signal surfaces for raw scoring, deterministic summaries, alert-style output, and recent
  regression listing.
- Comparison and analysis debugger views that show severity, change direction, top drivers, and
  direct evidence handoff before users open dense detail views.
- Stability proof across repeated compare operations, index rebuilds, debugger routes, and
  real-artifact smoke.

## Current Milestone: v4.5 Dataset Evolution And Regression Pack Automation

**Goal:** Turn detected regressions into versioned evaluation datasets that evolve deterministically
from real comparison signals.

**Target features:**
- Automatic regression-pack generation from saved comparison signals using deterministic pack
  policies.
- Immutable dataset version history with provenance back to source comparisons, signals, and cases.
- Incremental dataset evolution commands that compose new regressions without mutating prior
  versions.
- Debugger affordances for pack generation, version inspection, and provenance drillback.
- End-to-end proof that generated packs rerun through the standard `run -> compare -> insight`
  workflow without custom handling.

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

### Active

- Regression signals should generate deterministic draft packs without manual case picking.
- Dataset packs should become immutable, versioned artifacts with traceable lineage.
- Existing packs should evolve incrementally from new comparisons without rewriting old versions.
- Generated packs should remain compatible with the standard CLI, query, insight, and debugger
  workflow.

### Out of Scope

- Hosted services, background workers, or external dataset automation pipelines.
- Learned or opaque pack-composition policies replacing deterministic rules.
- A full browser-side dataset editor; `v4.5` focuses on lightweight generation and inspection.
- Silent mutation of published dataset versions.

## Context

- The product now covers execution, reporting, comparison, query, grounded interpretation, failure
  harvesting, dataset curation, replayable evaluation loops, and deterministic change signals.
- `v4.3` proved users can turn saved failures into curated datasets, but the capture step is still
  explicit and manual.
- `v4.4` proved the system can identify what changed and how severe it is without manual
  comparison-by-comparison inspection.
- The next product pressure is enforcement:
  high-signal regressions should become future evaluation inputs automatically and traceably.

## Constraints

- **Storage:** Filesystem artifacts remain canonical — dataset evolution must stay artifact-native.
- **Determinism:** Pack composition and versioning rules must be reproducible from local artifacts.
- **Immutability:** Published dataset versions cannot be rewritten in place.
- **Grounding:** Every generated pack must retain provenance back to source comparisons, signals,
  and cases.
- **Compatibility:** Evolved datasets must run through the standard engine and debugger surfaces
  unchanged.
- **Complexity:** Avoid hosted services, background workers, or opaque policy engines in `v4.5`.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep JSON artifacts as the product truth and add only derived local query/index layers | Reproducibility and inspectability matter more than infra breadth | ✓ Validated in `v4.1` |
| Make grounded interpretation opt-in richer, but deterministic by default | Heuristic, testable behavior should remain the base contract | ✓ Validated in `v4.2` |
| Turn harvested failures into first-class datasets rather than one-off exports | Reuse matters only if failures re-enter the evaluation loop cleanly | ✓ Validated in `v4.3` |
| Keep debugger export lightweight and route-local | Review and promotion belong in explicit lifecycle steps, not a browser editor | ✓ Validated in `v4.3` |
| Compute change signals deterministically from comparison artifacts before any LLM enrichment | Users need stable quantitative answers to “what changed?” first | ✓ Validated in `v4.4` |
| Persist signal blocks directly in comparison artifacts and expose them through CLI and debugger | Signals should be artifact-native and queryable without new infrastructure | ✓ Validated in `v4.4` |
| Turn high-signal regressions into generated dataset packs instead of alert-only outputs | Enforcement only matters if regressions become future evaluation inputs | — Targeted in `v4.5` |
| Make dataset versions immutable and explicitly linked to source signals and comparisons | Evolution needs traceability and reproducibility, not silent mutation | — Targeted in `v4.5` |

---
*Last updated: 2026-04-04 for milestone v4.5 initialization*
