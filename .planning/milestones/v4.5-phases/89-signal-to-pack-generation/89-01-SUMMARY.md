# 89-01 Summary

- Added [`evolution.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/datasets/evolution.py)
  as the deterministic signal-to-pack engine for draft regression datasets.
- Implemented signal-driver-first case selection with fallback to regression delta order and
  policy-controlled `top_n` / `failure_type` filtering.
- Rehydrated canonical prompt cases from saved run artifacts so generated packs remain grounded in
  the same artifact contract as the runner and debugger.
