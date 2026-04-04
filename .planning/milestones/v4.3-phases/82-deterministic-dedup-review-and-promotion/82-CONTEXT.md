# Phase 82: Deterministic Dedup Review And Promotion - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Take harvested draft packs from Phase 81 and make them reviewable, deduplicated, and promotable
into normal local dataset files. This phase still stays CLI-first. It does not yet add debugger
export affordances or the end-to-end replay proof.

</domain>

<decisions>
## Implementation Decisions

### Draft Versus Curated Lifecycle
- Draft harvest packs remain raw selections with source-specific draft ids.
- `dataset review` computes deterministic duplicate groups but does not mutate the draft file.
- `dataset promote` writes the curated output with canonical case ids and explicit lifecycle
  transition to `curated`.

### Dedup Semantics
- Dedup remains prompt-first, but it is expectation-sensitive to avoid collapsing prompt-identical
  cases that carry different authored expectations.
- Review should explicitly label whether a group is an exact prompt match or only a normalized
  prompt match.
- Promotion should keep one deterministic representative per canonical group, chosen by stable
  ordering over draft case ids.

### Local Dataset Discovery
- Keep bundled dataset listing intact and add local dataset packs as a second catalog section.
- Promoted harvested datasets should appear in the standard `failure-lab datasets list` surface
  instead of a parallel harvested-only catalog.

### CLI Surface
- Use one singular `failure-lab dataset ...` command family for lifecycle operations:
  `review` and `promote`.
- Keep promotion output deterministic by defaulting to the artifact-root `datasets/` directory
  unless the user explicitly overrides the output path.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- [`src/model_failure_lab/harvest/pipeline.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/harvest/pipeline.py)
  already writes draft packs with exact and normalized prompt hashes in per-case metadata.
- [`src/model_failure_lab/datasets/contracts.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/datasets/contracts.py)
  now carries lifecycle/source fields needed by both draft and curated packs.
- [`src/model_failure_lab/cli.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/cli.py)
  already owns the install-first dataset discovery surface and can host the lifecycle commands.

### Established Patterns
- Canonical ids and deterministic JSON output matter more than interactive mutation.
- The repo prefers explicit review summaries over hidden automatic cleanup.
- Promoted assets should flow back into the same normal dataset/run/report commands rather than a
  separate harvested-only execution path.

</code_context>

<specifics>
## Specific Ideas

- Keep the promoted curated case ids independent from the draft source ids.
- Record promotion metadata back under `metadata.harvest` so later debugger export can reconnect
  curated cases to original evidence without reopening the draft file.
- Expose duplicate counts and kept-case decisions in both human text and JSON review modes.

</specifics>

<deferred>
## Deferred Ideas

- Frontend export affordances belong to Phase 83.
- The milestone-wide rerun/compare/insight loop proof belongs to Phase 84.

</deferred>
