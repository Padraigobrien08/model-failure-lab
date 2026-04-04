# Phase 77: Structured Insight Reports And Heuristic Baselines - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Define one structured insight-report contract and ship deterministic heuristic summarization for
query-backed case and delta result sets. This phase does not add opt-in LLM execution or debugger
panels yet; it establishes the reusable analysis shape that later phases will expose through CLI
flags and UI.

</domain>

<decisions>
## Implementation Decisions

### Insight Report Contract
- Use one shared report schema for both query summarization and future comparison explanation.
- The report must be structured, not freeform text: summary, scoped totals, patterns, anomalies,
  and evidence references.
- Evidence references must stay route-local and drillable through existing run or comparison detail
  routes; do not invent a second evidence model.
- Pattern rows should carry concise metrics such as count, share, and dominant grouping labels so
  CLI and debugger can render them without re-parsing prose.

### Heuristic Summarization Strategy
- Build deterministic summaries from query rows plus bounded aggregate context rather than raw
  filesystem scans.
- Prefer grouping by existing query dimensions already present in the index: failure type,
  expectation verdict, transition type, model, dataset, and prompt id.
- Select representative evidence deterministically from ranked rows instead of random sampling.
- Treat anomalies as explicit low-frequency or high-impact outliers, not just "anything outside the
  top bucket."

### Bounded Context Rules
- Phase 77 must prove bounded representative sampling at the API layer, even before LLM mode exists.
- Summaries should operate on capped row windows and derived counts, with sampling metadata carried
  in the report.
- If a result set is truncated or sampled, the report should say so explicitly instead of implying
  full coverage.

### Claude's Discretion
- File/module boundaries inside `model_failure_lab.analysis` are flexible as long as the public
  contract is stable and easy to reuse in later phases.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- [`src/model_failure_lab/index/query.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/index/query.py)
  already exposes structured case, delta, and aggregate retrieval over the derived SQLite index.
- [`src/model_failure_lab/reporting/core.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/reporting/core.py)
  already contains deterministic aggregation patterns for failure breakdowns, verdicts, and notable
  case selection.
- [`src/model_failure_lab/reporting/compare.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/reporting/compare.py)
  already defines directional comparison concepts like delta kinds and transition summaries.
- [`frontend/src/app/routes/AnalysisPage.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/AnalysisPage.tsx)
  already has a query-backed route with URL filters and drillthrough links the future insights
  surface can attach to.

### Established Patterns
- The repo favors dataclass-based Python contracts and explicit typed JSON payloads.
- Query-facing surfaces already separate transport filters from rendered rows.
- Existing detail drillthrough relies on run/comparison ids plus case ids in URL-backed route state.

### Integration Points
- New insight APIs should sit above `model_failure_lab.index` and below CLI/UI transport layers.
- The query bridge can expose insight payloads once the backend contract exists.
- CLI rendering can follow the existing split between human-readable text tables and JSON payloads.

</code_context>

<specifics>
## Specific Ideas

- Keep heuristic mode as the product baseline, not a fallback afterthought.
- Carry enough evidence metadata in each claim for later debugger drillthrough without requiring the
  UI to reconstruct grouping logic on its own.
- Reuse the query layer as the source for cross-run analysis; do not reopen raw artifact scanning as
  part of insight generation.

</specifics>

<deferred>
## Deferred Ideas

- Opt-in LLM interpretation and prompt building belong to Phase 78.
- Debugger insights panels and clickable evidence clusters belong to Phase 79.
- Grounding rejection and milestone-wide workflow proof belong to Phase 80.

</deferred>
