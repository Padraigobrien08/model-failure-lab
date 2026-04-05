# Phase 106: CLI Alerting And Family Health Actions - Context

**Gathered:** 2026-04-05
**Status:** Completed

<domain>
## Phase Boundary

Expose escalation listings, family-health rationale, and explicit lifecycle review/apply flows in
the CLI. This phase covers workflow helpers, command wiring, and human-readable plus JSON output.
Debugger surfacing remains in Phase 107.

</domain>

<decisions>
## Implementation Decisions

- Keep lifecycle commands inside the existing `dataset` namespace instead of creating a new
  top-level alert surface.
- Reuse backend governance workflow ordering and policy evaluation for CLI review output; the CLI
  only renders persisted recommendations and applies explicit lifecycle actions.
- Keep lifecycle apply explicit and idempotent: users review first, then apply a named action that
  writes governance artifacts without mutating older dataset versions in place.

</decisions>

<code_context>
## Existing Code Insights

- [workflow.py](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/workflow.py)
  now exposes review, apply, and listing helpers for lifecycle actions plus active family state.
- [cli.py](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/cli.py) already owns
  adjacent dataset-family and governance flows, so Phase 106 extends that namespace directly.
- [lifecycle.py](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/lifecycle.py)
  provides the persisted action records the CLI can inspect and report.

</code_context>

<deferred>
## Deferred Ideas

- Debugger surfacing and drillthrough belong to Phase 107.
- Milestone-wide workflow proof belongs to Phase 108.

</deferred>
