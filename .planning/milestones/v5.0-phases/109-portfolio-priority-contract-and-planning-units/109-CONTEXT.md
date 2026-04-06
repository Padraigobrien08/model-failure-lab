# Phase 109: Portfolio Priority Contract And Planning Units - Context

**Gathered:** 2026-04-05
**Status:** Completed

<domain>
## Phase Boundary

Define the deterministic backend contract for portfolio priority items and inspectable planning
units over existing dataset families. This phase covers artifact-derived ranking, rationale, and
grouping semantics only; saved plan persistence and CLI creation/review flows belong to Phase 110,
while debugger surfacing belongs to Phase 111.

</domain>

<decisions>
## Implementation Decisions

- Keep existing governed dataset families as the portfolio queue anchor; suggested-but-uncreated
  families stay in comparison-level governance surfaces rather than entering the portfolio queue.
- Build portfolio evidence from shipped lifecycle recommendations, dataset-family health, and
  recent saved comparison recommendations so the queue remains fully artifact-derived.
- Use deterministic planning-unit rules instead of opaque clustering:
  merge-candidate families group first, then remaining families can group by shared source dataset
  and primary failure type, otherwise they remain single-family units.
- Preserve explicit inspectability by carrying the comparison IDs, recurring cluster IDs, lifecycle
  context, and related-family rationale that drive each portfolio rank or planning unit.

</decisions>

<code_context>
## Existing Code Insights

- [`src/model_failure_lab/governance/workflow.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/workflow.py)
  already exposes deterministic family-health rows and lifecycle review helpers over local
  artifacts.
- [`src/model_failure_lab/governance/policy.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/policy.py)
  already computes the escalation and lifecycle signals that should feed portfolio ranking instead
  of introducing a second policy engine.
- [`src/model_failure_lab/history.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/history.py)
  already persists family history, health, and recurring-cluster context that can be re-used as
  queue rationale.
- The CLI and query bridge currently stop at family-level lifecycle review/apply, so a clean
  portfolio module can extend that behavior without destabilizing the shipped `v4.9` workflow.

</code_context>

<specifics>
## Phase-Specific Gaps To Close

- Introduce typed portfolio queue items with deterministic rank, band, actionability, rationale,
  and evidence links.
- Introduce inspectable planning units that explain why families should be reviewed together.
- Persist enough portfolio metadata to support later saved plans and route-local debugger
  surfacing without redesigning the payload shape in Phase 110 or 111.

</specifics>

<deferred>
## Deferred Ideas

- Saved dry-run lifecycle plans, plan listing, and explicit promotion belong to Phase 110.
- Debugger route surfacing and drillthrough refinements belong to Phase 111.
- End-to-end queue-to-plan-to-apply workflow proof belongs to Phase 112.

</deferred>
