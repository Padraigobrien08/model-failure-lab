# 97-01 Summary

- Added [`src/model_failure_lab/history.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/history.py)
  as the typed history/timeline layer for runs, comparisons, dataset versions, and reusable
  history snapshots.
- Extended the derived index in
  [`src/model_failure_lab/index/builder.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/index/builder.py)
  to `query_index_v3`, including run metrics, dataset-version lineage, and dataset-aware rebuild
  invalidation.
- Added regression coverage in
  [`tests/unit/test_history_tracking.py`](/Users/padraigobrien/model-failure-lab/tests/unit/test_history_tracking.py)
  for ordered dataset history and family-history reconstruction.
