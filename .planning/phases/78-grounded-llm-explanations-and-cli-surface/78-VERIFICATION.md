status: passed

# 78 Verification

## Automated Proof

- `python3 -m pytest tests/unit/test_analysis_summarizer.py tests/unit/test_artifact_query_index.py tests/unit/test_cli.py tests/unit/test_cli_insights.py -q`
  - result: `40 passed`

## Workflow Stories

1. Query summarize:
   `failure-lab query --summarize` now returns a structured insight report in heuristic mode and
   exposes the same report in JSON mode.
2. Opt-in llm analysis:
   `failure-lab query --summarize --analysis-mode llm --analysis-model ...` enriches the heuristic
   report through a stubbed registered adapter while preserving evidence refs.
3. Comparison explain:
   `failure-lab compare A B --explain` still writes the saved comparison artifacts and then prints a
   grounded comparison insight report from the saved report id.

## Result

Phase 78 exposed the insight layer on the CLI and proved both deterministic heuristic summaries and
opt-in llm enrichment without changing the shared evidence contract.
