# Phase 117: Execution Contract And Preflight Checks - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Define the persisted preflight and execution artifact contract for saved portfolio plans without
changing the existing lifecycle-action storage model. This phase covers blocker detection before
mutation, minimal before/after family snapshots, and stable read/write seams for saved execution
receipts.

</domain>

<decisions>
## Implementation Decisions

### Storage Boundary
- Store saved plan executions under a dedicated governance root instead of mixing checkpoint
  receipts into portfolio plans or lifecycle-action records.
- Keep lifecycle apply persistence unchanged so execution receipts sit above the existing family
  action contract rather than replacing it.

### Preflight Rules
- Recompute current lifecycle recommendation and family/portfolio presence during preflight so stale
  plans block before any mutation.
- Treat already-active lifecycle actions as explicit preflight outcomes instead of silent no-ops.

### Snapshot Shape
- Capture a compact before/after family snapshot with health, priority, and active lifecycle
  state instead of embedding the full family-history payload into every receipt.

</decisions>

<code_context>
## Existing Code Insights

- [`portfolio.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/portfolio.py)
  already owns saved plan creation and plan-action semantics.
- [`lifecycle.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/lifecycle.py)
  already persists explicit lifecycle-action records and is the correct mutation seam.
- [`layout.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/storage/layout.py)
  already separates governance artifact roots, so execution receipts can follow the same pattern.
- [`workflow.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/workflow.py)
  and portfolio helpers already expose enough family and priority context to build minimal
  before/after snapshots.

</code_context>

<specifics>
## Specific Ideas

- Add a dedicated execution module with typed preflight checks, checkpoint receipts, follow-up
  preparation, and persisted execution records.
- Make stepwise execution default to one ready action while batch mode executes all or a bounded
  subset of ready actions.
- Persist execution artifacts incrementally so a stopped or repeated invocation still leaves an
  inspectable trail.

</specifics>
