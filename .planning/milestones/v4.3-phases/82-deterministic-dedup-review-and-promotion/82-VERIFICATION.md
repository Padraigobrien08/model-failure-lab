status: passed

# 82 Verification

## Automated Proof

- `python3 -m pytest tests/unit/test_harvest_pipeline.py tests/unit/test_cli.py tests/unit/test_failure_datasets.py -q`
  - result: `42 passed`
- `python3 -m pytest tests/unit/test_artifact_query_index.py tests/unit/test_cli_insights.py -q`
  - result: `15 passed`

## Workflow Stories

1. Draft review:
   `failure-lab dataset review` surfaces deterministic canonical duplicate groups and explicit
   normalization decisions over harvested draft packs.
2. Promotion:
   `failure-lab dataset promote` emits a curated dataset with stable canonical case ids and
   preserved harvest lineage.
3. Catalog and run compatibility:
   promoted harvested datasets appear in `failure-lab datasets list` and run through the standard
   engine path without manual reshaping.

## Result

Phase 82 turned harvested drafts into a stable local dataset lifecycle instead of a write-only
export surface.
