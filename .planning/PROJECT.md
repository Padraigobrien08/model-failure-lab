# Model Failure Lab

## What This Is

Model Failure Lab is a local, artifact-native system for evaluating, debugging, comparing,
querying, interpreting, harvesting, and replaying LLM failures. It is built around reproducible
filesystem artifacts, a CLI-first workflow, and a React debugger that reads the same saved
artifact contract.

## Current State

- Latest shipped milestone: `v4.3`
- Active milestone: `v4.4 Regression Detection And Signal Layer`
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

## Latest Completed Milestone: v4.3 Failure Harvesting And Dataset Pack Generation

**Goal:** Turn observed failures into reusable evaluation assets by harvesting real artifact cases
into curated dataset packs that rerun through the standard engine workflow.

**Delivered:**
- Query-compatible harvesting from saved runs, cross-run analysis results, and comparison delta
  slices.
- Deterministic draft review, deduplication, curated promotion, and local dataset catalog
  discovery.
- Lightweight debugger export from `/analysis` and comparison detail into draft dataset packs.
- Automated proof of the full `artifact -> harvest -> curated dataset -> rerun -> compare ->
  insight` loop.

## Current Milestone: v4.4 Regression Detection And Signal Layer

**Goal:** Add a deterministic signal layer that detects, scores, persists, and surfaces meaningful
regressions and improvements across runs.

**Target features:**
- Persisted comparison signal blocks with deterministic verdict, regression score, improvement
  score, and top failure-type drivers.
- CLI signal surfaces for raw scoring, deterministic summaries, alert-style output, and recent
  regression listing.
- Comparison and analysis debugger views that show severity, change direction, top drivers, and
  direct evidence handoff before users open dense detail views.
- One shared signal contract that stays quantitative first and can optionally feed the existing
  insight layer for richer interpretation.

## Next Milestone Goals

- Generate regression packs automatically from high-signal comparison changes.
- Add dataset versioning and evolution over curated harvested packs.
- Use recurring signal patterns to drive more proactive recommendations and debugging workflows.

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

### Active

- Every comparison should produce deterministic persisted regression and improvement signals.
- Users should be able to identify meaningful changes without manually opening every comparison.
- Debugger views should highlight severity and top drivers before deep inspection.

### Out of Scope

- Hosted services, background workers, or external alert pipelines.
- Learned or opaque scoring models replacing deterministic signal computation.
- Natural-language regression detection as the primary interface; quantitative surfaces come first.
- A new provider-specific UI branch; the signal layer must reuse the shared artifact-backed
  debugger posture.

## Context

- The product now covers execution, reporting, comparison, query, grounded interpretation, failure
  harvesting, dataset curation, and replayable evaluation loops.
- The next product pressure is no longer “can we inspect or reuse failures?” It is “can we tell
  users what changed and how severe it is without manual comparison-by-comparison inspection?”
- The right next layer is deterministic and quantitative first:
  explicit verdicts, persisted scores, top drivers, and evidence-linked summaries over comparison
  artifacts.

## Constraints

- **Storage:** Filesystem artifacts remain canonical. Signals must persist inside comparison
  artifacts, not in a separate service.
- **Determinism:** Signal scoring must be reproducible and independent of LLM behavior.
- **Grounding:** Signal summaries must stay tied to concrete failure types and case-level evidence.
- **Compatibility:** The query, insight, harvest, and debugger layers must keep working over the
  same artifact contract.
- **Complexity:** No background jobs or external infrastructure; compute signals at comparison
  time and query them locally.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep JSON artifacts as the product truth and add only derived local query/index layers | Reproducibility and inspectability matter more than infra breadth | ✓ Validated in `v4.1` |
| Make grounded interpretation opt-in richer, but deterministic by default | Heuristic, testable behavior should remain the base contract | ✓ Validated in `v4.2` |
| Turn harvested failures into first-class datasets rather than one-off exports | Reuse matters only if failures re-enter the evaluation loop cleanly | ✓ Validated in `v4.3` |
| Keep debugger export lightweight and route-local | Review and promotion belong in explicit lifecycle steps, not a browser editor | ✓ Validated in `v4.3` |
| Compute change signals deterministically from comparison artifacts before any LLM enrichment | Users need stable quantitative answers to “what changed?” first | — Targeted in `v4.4` |
| Persist signal blocks directly in comparison artifacts and expose them through CLI and debugger | Signals should be artifact-native and queryable without new infrastructure | — Targeted in `v4.4` |

---
*Last updated: 2026-04-04 for milestone v4.4 initialization*
