# 96 Verification

## Automated Proof

- `python3 -m pytest tests/unit/test_regression_governance.py tests/unit/test_cli_governance.py tests/unit/test_cli_demo_compare.py -q`
- `npm --prefix frontend run test -- --run src/app/__tests__/shell.test.tsx src/app/__tests__/runs.test.tsx src/app/__tests__/runDetail.test.tsx src/app/__tests__/comparisons.test.tsx src/app/__tests__/comparisonDetail.test.tsx src/app/__tests__/analysis.test.tsx`
- `npm --prefix frontend run build`
- `node frontend/scripts/smoke-real-artifacts.mjs --mode demo`

## Result

- Fresh `compare` artifacts can flow into deterministic governance recommendation, review, apply,
  and dataset-family health inspection without any manual artifact editing.
- Re-running governance apply over the same comparison stays stable and does not create duplicate
  dataset versions.
- Demo-mode debugger smoke verifies persisted governance recommendation payloads on comparison
  detail and analysis signal endpoints.
- The full governance loop is now proven across backend policy evaluation, CLI workflow, and
  debugger-facing artifact delivery.
