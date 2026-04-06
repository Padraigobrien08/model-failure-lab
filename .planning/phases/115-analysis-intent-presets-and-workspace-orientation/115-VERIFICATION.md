# Phase 115 Verification

- `npm --prefix frontend test -- --run src/app/__tests__/analysis.test.tsx` -> `7 passed`
- `python3 scripts/query_bridge.py query --root /private/tmp/model-failure-lab-local-ui.Ah5mhB --mode signals --signal-direction regression --limit 5` -> passed with `portfolio_item` and `portfolio_plans` in the payload
