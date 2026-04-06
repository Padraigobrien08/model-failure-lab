# Phase 93: Policy Contract And Recommendation Rules - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Define the deterministic governance-policy contract and produce stable recommendation output for a
single saved comparison signal. This phase stops at backend recommendation logic and dry-run pack
preview support. Recent-comparison review/apply flows, richer family matching, and debugger
surfaces stay in later phases.

</domain>

<decisions>
## Implementation Decisions

### Recommendation Contract
- Recommendation actions use the closed set `create`, `evolve`, or `ignore`.
- The action is determined deterministically from the persisted comparison signal plus local policy
  rules:
  - non-regression or incompatible signals default to `ignore`
  - regressions below the minimum severity threshold default to `ignore`
  - qualifying regressions choose `evolve` only when a deterministically matched family already
    exists; otherwise they choose `create`

### Policy Contract
- Policy stays fully local and inspectable through a typed backend contract, not a hidden config
  file or learned model.
- Phase 93 policy fields include:
  - minimum severity threshold
  - top-N preview limit
  - optional failure-type filter
  - family case-cap guard
  - duplicate-growth threshold
- Phase 93 only needs enough evaluation logic to make one saved comparison recommendation stable.
  Broader multi-family review/apply behavior belongs to Phase 94.

### Family Match Posture
- Phase 93 uses one deterministic candidate family derived from the existing regression-pack naming
  contract plus current family existence under the artifact root.
- Matching remains intentionally narrow here:
  exact family suggestion plus current-family health checks.
- Richer lineage/overlap matching and review across many recent comparisons stays deferred to
  Phase 94.

### Evidence Contract
- Recommendation output must include evidence-linked context without writing any dataset files.
- Add a dry-run regression-pack preview seam so governance can reuse the exact case-selection logic
  already used by dataset generation and evolution.

</decisions>

<code_context>
## Existing Code Insights

- [`src/model_failure_lab/reporting/signals.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/reporting/signals.py)
  already computes deterministic signal verdict, severity, and top drivers from saved comparison
  deltas.
- [`src/model_failure_lab/datasets/evolution.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/datasets/evolution.py)
  already knows how to select regression-pack cases and suggest family ids, but it currently mixes
  dry-run selection with file-writing entrypoints.
- [`src/model_failure_lab/index/query.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/index/query.py)
  already exposes saved comparison signals and case deltas over the derived local index, which is
  the right read-only source for governance inputs.
- [`tests/unit/test_dataset_evolution.py`](/Users/padraigobrien/model-failure-lab/tests/unit/test_dataset_evolution.py)
  and [`tests/unit/test_cli_demo_compare.py`](/Users/padraigobrien/model-failure-lab/tests/unit/test_cli_demo_compare.py)
  already prove deterministic signal and evolution behavior with stable fixture data.

</code_context>

<deferred>
## Deferred Ideas

- Recent-comparison review/apply CLI belongs to Phase 94.
- Family-health explanations across multiple families belong to Phase 94.
- Debugger recommendation surfacing belongs to Phase 95.

</deferred>
