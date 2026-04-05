# Phase 110: CLI Queue And Plan Draft Surfaces - Context

**Gathered:** 2026-04-05
**Status:** Completed

<domain>
## Phase Boundary

Expose the portfolio queue, saved plan drafts, and explicit plan-to-apply handoff through the CLI.
This phase covers command surfaces, artifact persistence, and CLI-level contract proof. Debugger
surfacing stays in Phase 111.

</domain>

<decisions>
## Implementation Decisions

- Keep portfolio workflow under the existing `dataset` command family so queue, lifecycle, and
  plan operations remain one coherent local workflow.
- Treat saved plans as deterministic JSON artifacts under governance storage; regenerating the same
  bounded plan should resolve to the same saved artifact instead of duplicating drafts.
- Promote one saved action directly into the existing lifecycle-apply path as an explicit operator
  step, preserving the no-background-execution constraint.

</decisions>

<code_context>
## Existing Code Insights

- Phase 109 now provides typed portfolio items, planning units, and saved-plan primitives, so the
  CLI can stay thin and mostly focus on filtering, rendering, and JSON output shape.
- [`src/model_failure_lab/cli.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/cli.py)
  already follows a stable `list -> review -> apply` pattern for governance and lifecycle flows.
- Governance storage now has a dedicated portfolio-plan root, making saved plans a natural CLI
  artifact rather than an in-memory convenience layer.

</code_context>

<specifics>
## Phase-Specific Gaps To Close

- Add queue listing and inspectable planning-unit context to the CLI.
- Add saved-plan creation, listing, inspection, and explicit promotion commands with JSON output.
- Prove filtering by family, dataset, model, failure type, actionability, and priority band over
  both queue rows and saved plans.

</specifics>

<deferred>
## Deferred Ideas

- Browser-side priority and plan surfacing belongs to Phase 111.
- End-to-end workflow proof across CLI plus debugger belongs to Phase 112.

</deferred>
