status: passed

# 87 Verification

## Automated Proof

- `npm --prefix frontend run test -- --run src/app/__tests__/shell.test.tsx src/app/__tests__/runs.test.tsx src/app/__tests__/runDetail.test.tsx src/app/__tests__/comparisons.test.tsx src/app/__tests__/comparisonDetail.test.tsx src/app/__tests__/analysis.test.tsx`
  - result: `38 passed`
- `npm --prefix frontend run build`
  - result: passed

## Result

Phase 87 proved that persisted comparison signals are now visible in the debugger before users open
dense evidence views, and that the new signal mode still hands off cleanly into the existing
comparison/run detail routes.
