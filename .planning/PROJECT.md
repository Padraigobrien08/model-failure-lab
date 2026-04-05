# Model Failure Lab

## What This Is

Model Failure Lab is a local, artifact-native system for evaluating, debugging, comparing,
querying, interpreting, harvesting, replaying, enforcing, tracking, clustering, escalating, and
lifecycle-managing recurring LLM failure behavior. It is built around reproducible filesystem
artifacts, a CLI-first workflow, and a React debugger that reads the same saved artifact contract.

## Current State

- Latest shipped milestone: `v4.9`
- Active milestone: `v5.0`
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
  - `v4.7` added artifact-derived history, deterministic trend and dataset-health signals,
    history-aware governance context, and lightweight debugger timeline surfacing
  - `v4.8` added deterministic recurring cluster identity, cluster summaries/history, debugger
    cluster context, and governance rationale enriched with recurring-pattern evidence
  - `v4.9` added deterministic escalation statuses, explicit dataset-family lifecycle review/apply,
    debugger lifecycle surfacing, and end-to-end workflow proof

## Latest Completed Milestone: v4.9 Proactive Escalation And Dataset Lifecycle Management

**Goal:** Turn recurring clusters and temporal governance context into explicit lifecycle actions
over dataset families, so the system can escalate, prune, merge, retire, or keep packs with a
deterministic local policy.

**Delivered:**
- Stable deterministic escalation statuses and provenance-rich lifecycle recommendations over
  recurring clusters, family history, and dataset-health evidence.
- CLI lifecycle review/apply flows with explicit persisted action records for `keep`, `prune`,
  `merge_candidate`, and `retire`.
- Lightweight debugger escalation and lifecycle surfacing on `/analysis` and comparison detail,
  backed by the same stored governance payloads.
- Verified workflow stability across backend policy, CLI apply, frontend rendering, and real
  artifact smoke.

## Current Milestone: v5.0 Portfolio Prioritization And Guided Lifecycle Planning

**Goal:** Turn the per-family lifecycle signals from `v4.9` into a deterministic operator queue
and saved plan artifacts, so users can prioritize and execute lifecycle work across many families
without background automation.

**Target features:**
- Deterministic portfolio ranking across dataset families from escalation, recurrence, and health.
- Explicit planning-unit grouping for related families and merge candidates.
- Saved dry-run lifecycle plans with projected impact and stepwise explicit apply handoff.
- Lightweight debugger priority and plan context on existing routes.

## Core Value

Make structured LLM failure analysis simple, reproducible, queryable, interpretable, reusable,
actionable, time-aware, pattern-aware, and lifecycle-manageable from local artifacts.

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
- ✓ Deterministic governance recommendations, review/apply workflows, and debugger recommendation
  surfacing — `v4.6`
- ✓ Artifact-derived history, recurring cluster identity, proactive escalation, and explicit
  dataset-family lifecycle management — `v4.7` to `v4.9`

### Active

- Operators need a deterministic portfolio queue over many dataset families rather than only
  per-family lifecycle surfaces.
- Cross-family planning should stay explicit, saved, bounded, and artifact-native rather than
  becoming background automation.
- Future behavior-management work should stay artifact-native unless a clear structural limit
  forces broader infrastructure.
- The debugger should keep priority and plan context compact and route-local rather than turning
  into a full observability dashboard.
- Any future automation must preserve explicit reviewability; no silent mutation of published
  dataset families.

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
- The core system now covers execution, comparison, insight, harvesting, enforcement, governance,
  history, recurring clusters, proactive escalation, and explicit dataset-family lifecycle
  management over local artifacts.
- The next missing layer is not more family-level policy detail; it is helping operators decide
  which families deserve attention first and how related actions should be grouped into explicit
  plans.
- `v5.0` should solve that prioritization and planning problem before any future bounded
  automation work is considered.

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
- **Explainability:** Governance decisions, escalation statuses, and cluster identities must be
  deterministic and inspectable, not opaque.

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
| Add temporal intelligence as a deterministic artifact-derived layer before introducing proactive automation | Governance is still correct locally but blind globally without longitudinal context | ✓ Validated in `v4.7` |
| Add recurring cluster identity before proactive alerts or pruning | The system needs to know whether the same problem is returning before escalating or consolidating | ✓ Validated in `v4.8` |
| Keep proactive escalation and dataset lifecycle actions local, deterministic, and explicitly reviewable | Maintenance decisions matter only if users can audit why a family should be kept, pruned, merged, or retired | ✓ Validated in `v4.9` |

*Last updated: 2026-04-05 for v5.0 initialization*
