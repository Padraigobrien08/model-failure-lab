# Phase 122: Measured Verdicts And CLI Outcome Closure - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Turn linked follow-up evidence into deterministic measured verdicts and explicit CLI closure
flows. This phase covers the verdict contract, source versus follow-up signal deltas, and the
final attestation command that closes a saved execution outcome.

</domain>

<decisions>
## Implementation Decisions

### Verdict Inputs
- Derive measured verdicts from saved comparison artifacts rather than implicit model metadata so
  closure stays grounded in the same artifact-native comparison contract used elsewhere.

### Closure Contract
- Keep attestation explicit: evidence linking and final attestation are separate steps so users
  can inspect linked artifacts before closing an outcome.

### Explanation Shape
- Persist both source and follow-up signal summaries plus a compact delta summary so closure
  rationale remains inspectable without reopening every artifact manually.

</decisions>

<code_context>
## Existing Code Insights

- [`outcomes.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/outcomes.py)
  already owns attestation persistence and is the correct place for deterministic verdict logic.
- [`query.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/index/query.py)
  already exposes saved comparison signal rows, so verdict computation can reuse stable signal
  metadata instead of reparsing reports manually.
- [`cli.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/cli.py)
  already contains the follow-up inspection surfaces added in Phase 121 and can extend them with
  an explicit attestation command.

</code_context>

<specifics>
## Specific Ideas

- Add one deterministic verdict builder that returns `improved`, `regressed`, `inconclusive`, or
  `no_signal`.
- Persist signal summaries and delta counts directly inside the saved attestation payload.
- Make the CLI render the attested verdict, linked evidence, and rationale from the same payload
  returned by the governance helpers.

</specifics>
