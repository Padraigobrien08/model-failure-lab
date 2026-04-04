# Model Failure Lab

## What This Is

Model Failure Lab is a local, artifact-native system for evaluating, debugging, comparing,
querying, interpreting, harvesting, replaying, and now enforcing LLM failures. It is built around
reproducible filesystem artifacts, a CLI-first workflow, and a React debugger that reads the same
saved artifact contract.

## Current State

- Latest shipped milestone: `v4.6`
- Active milestone: `v4.7 Model Behavior Tracking And Dataset Health Over Time`
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
  - `v4.6` added deterministic governance recommendations, review/apply workflows, debugger
    recommendation surfacing, and proven governance-loop stability

## Latest Completed Milestone: v4.6 Regression Governance And Recommendation Layer

**Goal:** Turn regression enforcement from manual dataset-evolution decisions into deterministic,
policy-driven recommendations and review/apply workflows.

**Delivered:**
- Deterministic governance recommendations over saved comparison signals, including explicit
  severity, matched-family, policy-rule, and evidence-linked rationale.
- Review/apply CLI workflows and dataset-family health inspection across recent signals.
- Debugger recommendation status, rationale, and matched-family context on `/analysis` signal
  views and comparison detail surfaces.
- End-to-end governance proof across fresh compare artifacts, repeat apply stability, frontend
  regressions, production build, and real-artifact smoke.

## Current Milestone: v4.7 Model Behavior Tracking And Dataset Health Over Time

**Goal:** Add deterministic temporal tracking so the system can evaluate model behavior, dataset
health, and recurring regressions across time instead of only per comparison.

**Target features:**
- Artifact-derived history and timeline queries over runs, comparisons, and dataset families.
- Deterministic trend and recurrence signals such as improving/degrading/stable, recent delta
  direction, and recurring regression counts.
- Dataset health summaries for versioned evaluation packs, including recent fail-rate movement and
  volatility.
- CLI history surfaces and governance context that incorporate historical state, not just the
  latest comparison.
- Lightweight debugger timeline and trend indicators on existing analysis and comparison surfaces.

## Next Milestone Goals

- Build on temporal tracking with clustering, pattern mining, or longer-horizon dataset-health
  management.
- Extend governance with history-aware automation only after deterministic timeline signals are
  proven.
- Keep future behavior-management work artifact-native unless a clear structural limit forces
  broader infrastructure.

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

### Active

- Users should be able to inspect run, comparison, and dataset behavior across time, not just one
  comparison at a time.
- Trend labels such as improving, degrading, stable, and volatile should be computed
  deterministically from saved artifacts.
- The system should detect recurring regressions or repeated failure patterns across recent
  history.
- Governance should be able to consume historical context while staying deterministic and fully
  inspectable.
- The debugger should expose lightweight timeline and dataset-health context without turning into a
  dashboard product.

### Out of Scope

- Hosted services, background workers, or external dataset automation pipelines.
- Learned or opaque pack-composition policies replacing deterministic rules.
- A full browser-side dataset editor; governance remains lightweight and route-local.
- Silent mutation of published dataset versions.

## Context

- The product now covers execution, reporting, comparison, query, grounded interpretation,
  harvesting, signal scoring, and versioned regression-pack enforcement over local artifacts.
- `v4.3` proved users can turn saved failures into curated datasets, but the capture step was still
  explicit and manual.
- `v4.4` proved the system can identify what changed and how severe it is without manual
  comparison-by-comparison inspection.
- `v4.5` proved those regressions can become future evaluation inputs automatically and traceably.
- `v4.6` proved governance decisions can now be deterministic, explainable, reviewable, and stable
  over local artifacts.
- The next product pressure is time and continuity:
  whether behavior is improving or degrading over time, whether datasets are still pulling their
  weight, and whether the same regression classes keep returning.

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
- **Explainability:** Governance decisions must be deterministic and inspectable, not opaque.

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
| Make governance decisions explicit, deterministic, and reviewable before writing dataset changes | Recommendation quality matters only if users can trust and inspect the policy basis | ✓ Validated in `v4.6` |
| Add temporal intelligence as a deterministic artifact-derived layer before introducing proactive automation | Governance is still correct locally but blind globally without longitudinal context | — Targeted in `v4.7` |

---
*Last updated: 2026-04-04 for milestone v4.7 initialization*
