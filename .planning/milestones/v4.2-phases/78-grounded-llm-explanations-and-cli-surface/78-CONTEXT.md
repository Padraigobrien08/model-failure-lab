# Phase 78: Grounded LLM Explanations And CLI Surface - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Expose the insight layer on the CLI through `failure-lab query --summarize` and
`failure-lab compare --explain`, with deterministic heuristic mode by default and opt-in LLM
enrichment when the user explicitly supplies an analysis model.

</domain>

<decisions>
## Implementation Decisions

### LLM Execution Contract
- Keep `--analysis-mode heuristic|llm`, with `heuristic` as the default for both query and compare.
- Require an explicit analysis model only when `--analysis-mode llm` is selected.
- Reuse the existing adapter registry for LLM insight generation instead of adding a second
  provider-specific analysis stack.

### Grounding Strategy
- LLM mode should enrich a heuristic base report rather than invent a fresh ungrounded report from
  scratch.
- The prompt builder should pass bounded representative evidence and require structured JSON output.
- Evidence refs stay owned by the heuristic base report; the LLM is allowed to rewrite summaries,
  not to mint arbitrary new evidence links.

### CLI Surface
- `failure-lab query --summarize` should support both human-readable output and the existing
  `--json` mode.
- `failure-lab compare --explain` should still write saved comparison artifacts before printing the
  explanation surface.
- Analysis-specific configuration should stay narrow: model target, optional system prompt, and
  JSON-valued adapter options.

### Claude's Discretion
- The exact prompt wording and JSON output shape for LLM enrichment can evolve as long as the final
  report still conforms to the shared insight schema.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- [`src/model_failure_lab/analysis/summarizer.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/analysis/summarizer.py)
  already provides the heuristic base report.
- [`src/model_failure_lab/adapters/contracts.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/adapters/contracts.py)
  and the provider adapters already normalize model invocation behind `ModelRequest` and
  `ModelResult`.
- [`src/model_failure_lab/cli.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/cli.py)
  already has consistent parsing for model routing and JSON-valued `--model-option` flags.

### Established Patterns
- Provider-specific runtime details live in adapter options, not in a separate orchestration layer.
- Runtime install hints are explicit and provider-contained.
- Human-readable CLI summaries and JSON payloads are separate render paths.

### Integration Points
- Add prompt-building and llm-enrichment helpers under `model_failure_lab.analysis`.
- Extend the query and compare handlers in `cli.py` to call the new analysis helpers.
- Rebuild the derived query index before explaining a freshly written comparison artifact.

</code_context>

<specifics>
## Specific Ideas

- Make llm mode impossible to invoke accidentally by requiring the user to opt in and specify the
  analysis model.
- Keep compare explanations anchored to the saved comparison artifact that was just written.
- Preserve one report contract between heuristic and llm modes so later UI work can stay
  transport-agnostic.

</specifics>

<deferred>
## Deferred Ideas

- Debugger insights panels and clickable evidence clusters belong to Phase 79.
- Grounding rejection logic and milestone-wide workflow proof belong to Phase 80.

</deferred>
