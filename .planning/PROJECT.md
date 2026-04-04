# Model Failure Lab

## What This Is

Model Failure Lab is a local, artifact-native system for evaluating, debugging, comparing,
querying, interpreting, harvesting, and replaying LLM failures. It is built around reproducible
filesystem artifacts, a CLI-first workflow, and a React debugger that reads the same saved
artifact contract.

## Current State

- Latest shipped milestone: `v4.4`
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

## Current Milestone

No active milestone is defined yet.

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
- ✓ Deterministic signal scoring, CLI change surfacing, debugger severity views, and workflow
  stability proof — `v4.4`

### Active

No active milestone requirements yet.

### Out of Scope

- Hosted services, background workers, or external alert pipelines.
- Learned or opaque scoring models replacing deterministic signal computation.
- Natural-language regression detection as the primary interface; quantitative surfaces come first.
- A new provider-specific UI branch; the signal layer must reuse the shared artifact-backed
  debugger posture.

## Context

- The product now covers execution, reporting, comparison, query, grounded interpretation, failure
  harvesting, dataset curation, and replayable evaluation loops.
- The product now supports execution, reporting, comparison, query, grounded interpretation,
  harvesting, dataset promotion, and deterministic change signals over the same artifact contract.
- The next product pressure is how to act on those signals automatically over time rather than
  detecting them manually.

## Constraints

- **Storage:** Filesystem artifacts remain canonical.
- **Determinism:** Core behavior should remain reproducible and inspectable from local artifacts.
- **Grounding:** Higher-level interpretation must stay tied to concrete evidence and drillthrough.
- **Compatibility:** New layers should keep working over the shared artifact contract.
- **Complexity:** Avoid background services or hosted infrastructure unless a milestone explicitly
  justifies them.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep JSON artifacts as the product truth and add only derived local query/index layers | Reproducibility and inspectability matter more than infra breadth | ✓ Validated in `v4.1` |
| Make grounded interpretation opt-in richer, but deterministic by default | Heuristic, testable behavior should remain the base contract | ✓ Validated in `v4.2` |
| Turn harvested failures into first-class datasets rather than one-off exports | Reuse matters only if failures re-enter the evaluation loop cleanly | ✓ Validated in `v4.3` |
| Keep debugger export lightweight and route-local | Review and promotion belong in explicit lifecycle steps, not a browser editor | ✓ Validated in `v4.3` |
| Compute change signals deterministically from comparison artifacts before any LLM enrichment | Users need stable quantitative answers to “what changed?” first | ✓ Validated in `v4.4` |
| Persist signal blocks directly in comparison artifacts and expose them through CLI and debugger | Signals should be artifact-native and queryable without new infrastructure | ✓ Validated in `v4.4` |

---
*Last updated: 2026-04-04 after v4.4 completion*
