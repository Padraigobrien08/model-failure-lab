status: passed

# 84 Verification

## Automated Proof

- `python3 -m pytest tests/unit/test_harvest_pipeline.py tests/unit/test_harvest_replay_loop.py tests/unit/test_cli_insights.py -q`
  - result: `13 passed`
- `npm --prefix frontend run test -- --run src/app/__tests__/shell.test.tsx src/app/__tests__/runs.test.tsx src/app/__tests__/runDetail.test.tsx src/app/__tests__/comparisons.test.tsx src/app/__tests__/comparisonDetail.test.tsx src/app/__tests__/analysis.test.tsx`
  - result: `37 passed`
- `npm --prefix frontend run build`
  - result: passed

## Workflow Stories

1. Harvest one regression slice from existing artifacts, review it, and promote it into a curated
   dataset.
2. Rerun that curated dataset with two deterministic fixture models, build reports, and compare
   the reruns with grounded explanation.
3. Summarize the rerun dataset through the query insight layer without any manual artifact
   reshaping.

## Result

Phase 84 proved that observed failures can become reusable evaluation assets and still flow through
the same run, compare, insight, and debugger contract.
