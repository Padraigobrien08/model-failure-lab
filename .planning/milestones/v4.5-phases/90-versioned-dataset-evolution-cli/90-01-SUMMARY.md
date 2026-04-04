# 90-01 Summary

- Added immutable dataset-family history and version records in
  [`evolution.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/datasets/evolution.py).
- Implemented deterministic family evolution with normalized prompt hashing, stable case ids, and
  duplicate collapse against the prior immutable version.
- Preserved explicit version lineage through `family_id`, `version_number`, `version_tag`,
  `parent_dataset_id`, and `source_comparison_id` metadata.
