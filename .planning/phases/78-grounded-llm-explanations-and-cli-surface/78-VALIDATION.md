# Phase 78 Validation

- `failure-lab query ... --summarize` works in heuristic mode and returns structured report data in
  JSON mode.
- `failure-lab query ... --summarize --analysis-mode llm --analysis-model ...` enriches the base
  report through a stubbed adapter and preserves grounding refs.
- `failure-lab compare A B --explain` writes artifacts, rebuilds the index, and returns a grounded
  explanation for the saved comparison.

