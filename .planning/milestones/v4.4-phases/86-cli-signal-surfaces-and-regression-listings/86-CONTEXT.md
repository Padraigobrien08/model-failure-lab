# Phase 86: CLI Signal Surfaces And Regression Listings - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Expose the persisted comparison signal contract through the CLI. This phase covers score, summary,
alert, and severity-ordered listing surfaces only. Debugger severity rendering stays in Phase 87.

</domain>

<decisions>
## Implementation Decisions

### Compare Command Posture
- Keep the existing default `failure-lab compare` summary intact and additive.
- Layer new signal-specific flags on top:
  - `--score` for raw JSON
  - `--summary` for deterministic human-readable signal output
  - `--alert` for thresholded directional alerts

### Alert Contract
- Only emit alert output when the persisted signal verdict is `regression` or `improvement` and
  the signal severity exceeds the configured threshold.
- Neutral and incompatible comparisons stay silent under `--alert`.

### Listing Contract
- Add a dedicated `failure-lab regressions` surface backed by the query index mirror instead of
  rescanning comparison artifacts in the CLI.
- Keep the direction filter explicit so the same command can list regressions, improvements,
  neutrals, or all saved signal rows.

</decisions>

<code_context>
## Existing Code Insights

- [`src/model_failure_lab/cli.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/cli.py)
  already owns the compare command, query command, and the table/JSON rendering helpers.
- [`src/model_failure_lab/index/query.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/index/query.py)
  now mirrors persisted signal rows and ranked signal drivers, which makes the new listing surface
  a read-only query layer feature rather than a second scoring path.
- [`tests/unit/test_cli_demo_compare.py`](/Users/padraigobrien/model-failure-lab/tests/unit/test_cli_demo_compare.py)
  and [`tests/unit/test_cli_insights.py`](/Users/padraigobrien/model-failure-lab/tests/unit/test_cli_insights.py)
  already cover compare/report/query CLI behavior with deterministic local fixtures.

</code_context>

<deferred>
## Deferred Ideas

- Surfacing recent regressions inside `/analysis` belongs to Phase 87.
- Full milestone workflow proof belongs to Phase 88.

</deferred>
