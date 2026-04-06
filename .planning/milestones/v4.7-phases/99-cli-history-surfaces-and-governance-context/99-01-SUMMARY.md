# 99-01 Summary

- Added `failure-lab history` and history rendering in
  [cli.py](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/cli.py).
- Extended governance policy and recommendation payloads in
  [policy.py](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/policy.py)
  with recurrence policy fields and persisted historical context.
- Extended
  [query_bridge.py](/Users/padraigobrien/model-failure-lab/scripts/query_bridge.py)
  so dataset-version and dedicated history endpoints now expose temporal snapshots for the
  debugger.
