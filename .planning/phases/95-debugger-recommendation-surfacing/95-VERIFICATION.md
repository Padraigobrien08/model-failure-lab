# 95 Verification

## Automated Proof

- `npm --prefix frontend run test -- --run src/app/__tests__/analysis.test.tsx src/app/__tests__/comparisonDetail.test.tsx`
- `npm --prefix frontend run test -- --run src/app/__tests__/shell.test.tsx src/app/__tests__/runs.test.tsx src/app/__tests__/runDetail.test.tsx src/app/__tests__/comparisons.test.tsx src/app/__tests__/comparisonDetail.test.tsx src/app/__tests__/analysis.test.tsx`
- `npm --prefix frontend run build`

## Result

- `/analysis?mode=signals` now shows recommendation action and rationale on signal cards.
- Comparison detail shows recommendation status in the framing header and matched-family context in
  the existing automation panel.
- Recommendation surfaces keep source-evidence drillthrough via preview links and comparison detail
  navigation.
- Governance payload normalization is centralized in the frontend artifact loaders; React surfaces
  only render bridge-provided policy data.
