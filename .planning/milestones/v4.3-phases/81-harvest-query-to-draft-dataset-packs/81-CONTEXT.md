# Phase 81: Harvest Query-To-Draft Dataset Packs - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Add the first harvesting surface: convert indexed saved run or comparison selections into draft
dataset packs without breaking the existing dataset -> run contract. This phase stops at draft pack
creation. It does not yet finalize deduplication, review, promotion, or debugger export affordances.

</domain>

<decisions>
## Implementation Decisions

### Harvest Output Contract
- Harvested drafts should still be canonical dataset envelopes so the runner can consume them later
  without a second import format.
- Add lightweight top-level harvest fields directly to the dataset contract:
  `created_at`, `lifecycle`, and `source`.
- Keep per-case provenance under `case.metadata.harvest` so prompt text, tags, and expectations
  remain the same prompt-case model the runner already understands.

### Source Hydration Strategy
- Use the indexed query layer only to select result rows; hydrate canonical prompt content from the
  saved run artifacts themselves.
- For run-case harvesting, source each prompt directly from the selected saved run case.
- For comparison-delta harvesting, source the prompt from the saved baseline/candidate case pair
  and record any prompt mismatch explicitly in metadata instead of hiding it.

### Draft Identity Rules
- Draft case ids must be unique and deterministic across repeated harvest runs on the same source
  evidence.
- Draft ids are source-specific entry ids, not the future deduplicated curated ids. Phase 82 will
  decide which duplicates survive promotion.

### CLI Posture
- Add `failure-lab harvest` as the one draft-creation command.
- Reuse the current structured query filters so harvesting feels like a continuation of query, not
  a separate selection language.
- Support `--comparison` as a comparison-centric alias while still preserving the same internal
  filter contract.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- [`src/model_failure_lab/index/query.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/index/query.py)
  already resolves cross-run case and delta selections from the derived local SQLite index.
- [`src/model_failure_lab/reporting/load.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/reporting/load.py)
  already reloads saved run artifacts with per-case prompt snapshots and expectations.
- [`src/model_failure_lab/datasets/contracts.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/datasets/contracts.py)
  already defines the dataset envelope consumed by the runner.
- [`src/model_failure_lab/testing/insight_fixture.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/testing/insight_fixture.py)
  already materializes deterministic multi-run and comparison artifacts for harvest testing.

### Established Patterns
- The CLI prefers explicit, structured flags over freeform selection.
- The repo uses dataclass-based JSON contracts with deterministic `write_json(...)` formatting.
- Artifact compatibility comes from reusing the canonical prompt-case and dataset contracts instead
  of inventing parallel draft-only shapes.

</code_context>

<specifics>
## Specific Ideas

- Always tag harvested prompt cases with `harvested` so later reruns can be sliced easily.
- Preserve failure/delta labels in harvest metadata so later review and export surfaces do not need
  to recompute them from scratch.
- Keep draft lifecycle explicit from the start so Phase 82 can upgrade draft -> curated instead of
  inferring state from filenames.

</specifics>

<deferred>
## Deferred Ideas

- Dedup grouping, duplicate inspection, and promotion belong to Phase 82.
- Debugger export affordances belong to Phase 83.
- The full rerun/compare/insight loop proof belongs to Phase 84.

</deferred>
