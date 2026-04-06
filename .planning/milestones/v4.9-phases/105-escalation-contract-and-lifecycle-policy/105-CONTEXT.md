# Phase 105: Escalation Contract And Lifecycle Policy - Context

**Gathered:** 2026-04-05
**Status:** Completed

<domain>
## Phase Boundary

Define the backend contract for deterministic escalation status and dataset-family lifecycle
assessment over existing recurring-cluster, history, and governance artifacts. This phase stops at
typed policy payloads, helper seams, and backend tests; CLI review/apply surfaces belong to Phase
106 and debugger surfacing belongs to Phase 107.

</domain>

<decisions>
## Implementation Decisions

- Keep `create` / `evolve` / `ignore` as the governance action model and attach escalation as
  contextual metadata, not a replacement action system.
- Derive lifecycle health from local artifact history, projected family growth, and recurring
  cluster context with deterministic thresholds and rationale.
- Treat the current unstaged work in
  [`src/model_failure_lab/governance/policy.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/policy.py)
  as the Phase 105 starting point, but tighten it into an explicit contract before exposing it
  through later CLI and UI phases.
- Preserve explicit reviewability: lifecycle outputs must explain why a family is `keepable`,
  `overgrown`, `merge_candidate`, or `stale` without adding hosted services or silent mutation.

</decisions>

<code_context>
## Existing Code Insights

- [`src/model_failure_lab/governance/policy.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/policy.py)
  already contains draft `GovernanceEscalation`, `LifecycleRecommendation`, and
  `describe_dataset_family_lifecycle()` seams plus deterministic score thresholds.
- [`src/model_failure_lab/history.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/history.py)
  already provides the reusable history and dataset-health summaries that should remain the source
  of truth for lifecycle decisions.
- [`src/model_failure_lab/governance/workflow.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/workflow.py)
  and [`src/model_failure_lab/cli.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/cli.py)
  already own the downstream review/apply and rendering surfaces that later phases will extend.
- Existing governance and history tests pass with the draft policy changes, which means the Phase
  105 risk is missing contract proof, not an active regression in shipped behavior.

</code_context>

<specifics>
## Phase-Specific Gaps To Close

- Add focused proof for escalation states such as `suppressed`, `watch`, `elevated`, and
  `critical`.
- Make lifecycle recommendations preserve the provenance needed by `HEALTH-02`, especially links
  back to source dataset/family context and the family history used to make the decision.
- Tighten merge-candidate detection so it keys off the intended regression-family semantics rather
  than any loosely matching dataset metadata.

</specifics>

<deferred>
## Deferred Ideas

- Alert listing, inspect, and review/apply CLI flows belong to Phase 106.
- Debugger route surfacing and drillthrough belong to Phase 107.
- End-to-end workflow proof across review/apply and resulting family state belongs to Phase 108.

</deferred>
