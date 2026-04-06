# Model Failure Lab

## What This Is

Model Failure Lab is a local, artifact-native system for evaluating, debugging, comparing,
querying, interpreting, harvesting, replaying, enforcing, tracking, clustering, escalating, and
lifecycle-managing recurring LLM failure behavior. It is built around reproducible filesystem
artifacts, a CLI-first workflow, and a React debugger that reads the same saved artifact contract.

## Current State

- Latest shipped milestone: `v5.2`
- Active milestone: `v5.3`
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
  - `v5.0` added deterministic portfolio ranking, saved guided lifecycle plans, explicit plan
    promotion, and route-local debugger plan context
  - `v5.1` made the debugger triage-first with inventory triage context, persistent operator
    summary, analysis presets, stronger workspace orientation, and verified route stability
  - `v5.2` added explicit saved-plan preflight, checkpointed execution, persisted receipts,
    rollback guidance, and route-local execution outcome surfacing

## Latest Completed Milestone: v5.2 Guided Plan Execution And Outcome Verification

**Goal:** Turn saved lifecycle plans into an explicit, checkpointed execution workflow with
outcome verification, so operators can safely act on portfolio decisions and measure whether those
actions improved behavior.

**Delivered:**
- Saved-plan preflight that blocks stale or missing-family actions before lifecycle mutation.
- Explicit CLI plan execution with stepwise or bounded batch checkpoints, persisted receipts, and
  rollback guidance.
- Compact before/after family snapshots plus prepared rerun/compare follow-up derived from saved
  plan scope.
- Route-local debugger execution context on the existing automation panel and sticky operator
  summary without creating a separate execution dashboard.

## Current Milestone: v5.3 Closed-Loop Outcome Attestation And Policy Feedback

**Goal:** Turn post-execution follow-up into explicit, persisted outcome closure, so operators can
prove whether a lifecycle action helped and feed that result back into future policy decisions.

**Target features:**
- Execution-receipt attestation that links follow-up runs and comparison artifacts back to the
  executed action.
- Deterministic measured outcome verdicts with persisted deltas, rationale, and closure state.
- Policy feedback that feeds attested outcomes into family history, portfolio priority, and future
  plan review context.
- Route-local CLI and debugger surfaces for open follow-ups, closed outcomes, and action-effect
  timelines.

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
- ✓ Triage-first debugger workflows with persistent operator context, analysis presets, workspace
  orientation, and route-stability proof — `v5.1`
- ✓ Saved-plan preflight, checkpointed execution, persisted receipts, and route-local outcome
  verification — `v5.2`

### Active

- Execution receipts need explicit outcome attestation and evidence linking rather than leaving
  rerun/compare follow-up as an external manual step.
- Operators need deterministic measured verdicts and persisted rationale so they can tell whether
  a lifecycle action improved behavior.
- Family history, portfolio priority, and future plan review should reflect prior attested outcomes
  before new changes are proposed or applied.
- Future behavior-management work should stay artifact-native unless a clear structural limit
  forces broader infrastructure.
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
- `v5.0` solved the operator-prioritization layer with deterministic ranking, explicit planning
  units, saved portfolio drafts, and route-local debugger context.
- `v5.1` resolved the most obvious workflow bottleneck by making triage, decision-making, and
  workspace orientation clearer without replacing the route-local, artifact-native debugger shape.
- `v5.2` closed the next bottleneck by turning saved plans into explicit execution workflows with
  preflight, checkpoints, receipts, and route-local outcome review.
- `v5.2` prepared rerun/compare follow-up from execution receipts, but the system still stops short
  of persisting whether that evidence proved an action helped.
- `v5.3` should close that final manual gap by linking execution receipts to follow-up evidence,
  persisting measured outcome verdicts, and feeding those results back into future policy context.

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
| Improve the existing debugger with route-local triage, persistent operator context, and URL-backed analysis presets instead of adding a separate dashboard | The product had already outgrown its UI, but the artifact-native model still fit; workflow clarity mattered more than a brand new surface | ✓ Validated in `v5.1` |
| Keep saved-plan execution checkpointed, explicit, and artifact-native instead of introducing background automation | Execution only matters if operators can inspect blockers, receipts, and outcome context before and after every mutation | ✓ Validated in `v5.2` |
| Close the post-execution loop with explicit attestation and policy feedback before pursuing schedule-driven automation | The system should first prove whether an action measurably helped before it optimizes when or how often actions run | — Pending in `v5.3` |

*Last updated: 2026-04-06 for v5.3 initialization*
