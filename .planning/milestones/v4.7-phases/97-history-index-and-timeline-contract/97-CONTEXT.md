# Phase 97: History Index And Timeline Contract - Context

**Gathered:** 2026-04-04
**Status:** Completed

<domain>
## Phase Boundary

Add the artifact-derived history contract for ordered run, comparison, and dataset-family
timelines. This phase stops at the read model and index/schema changes needed to expose stable
history snapshots over local artifacts.

</domain>

<decisions>
## Implementation Decisions

- Extend the existing derived query index rather than introducing a second store.
- Keep filesystem artifacts canonical; timelines are always rebuilt from saved runs, reports, and
  dataset JSON.
- Include run metrics and dataset-version lineage directly in the index so later phases can compute
  trends without re-scanning raw artifacts on every request.
- Order all history by saved artifact timestamps with deterministic tie-breaking on identifiers.

</decisions>

<code_context>
## Existing Code Insights

- [`src/model_failure_lab/index/builder.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/index/builder.py)
  already owns the derived SQLite schema and rebuild triggers.
- [`src/model_failure_lab/index/query.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/index/query.py)
  already exposes artifact-backed runs, comparisons, cases, and signals over that index.
- [`src/model_failure_lab/datasets/evolution.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/datasets/evolution.py)
  already encodes dataset-family lineage in generated dataset packs, which is the right basis for
  timeline records.

</code_context>

<deferred>
## Deferred Ideas

- Trend labels, volatility, and recurrence scoring belong to Phase 98.
- CLI rendering and governance consumption of history belong to Phase 99.
- Debugger timeline surfacing belongs to Phase 100.

</deferred>
