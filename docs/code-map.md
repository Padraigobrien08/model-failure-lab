# Code Map

A quick guide for contributors to find the right files fast.

## If you want to...

- **Add or change CLI commands**
  - `src/model_failure_lab/cli.py`

- **Change run execution behavior**
  - `src/model_failure_lab/runner/execute.py`
  - `src/model_failure_lab/runner/artifacts.py`

- **Change report/comparison output**
  - `src/model_failure_lab/reporting/core.py`
  - `src/model_failure_lab/reporting/compare.py`
  - `src/model_failure_lab/reporting/signals.py`

- **Change query/index behavior**
  - `src/model_failure_lab/index/builder.py`
  - `src/model_failure_lab/index/query.py`
  - `src/model_failure_lab/index/contracts.py`

- **Change governance recommendations / policy logic**
  - `src/model_failure_lab/governance/policy.py`
  - `src/model_failure_lab/governance/workflow.py`
  - `src/model_failure_lab/governance/gates.py`

- **Change recurring cluster/root-cause summaries**
  - `src/model_failure_lab/clusters.py`
  - `src/model_failure_lab/governance/intelligence.py`

- **Change baseline registry or PR reliability output**
  - `src/model_failure_lab/governance/baselines.py`

- **Change harvesting and dataset promotion**
  - `src/model_failure_lab/harvest/pipeline.py`
  - `src/model_failure_lab/harvest/review.py`
  - `src/model_failure_lab/datasets/evolution.py`

## Test map

- CLI and command contracts:
  - `tests/unit/test_cli.py`
  - `tests/unit/test_cli_governance.py`
  - `tests/unit/test_cli_production_smoke.py`

- Evaluation/reporting math and payloads:
  - `tests/unit/test_evaluation_aggregate_metrics.py`
  - `tests/unit/test_report_bundle.py`
  - `tests/unit/test_shift_eval_pipeline.py`

- Governance lifecycle and regressions:
  - `tests/unit/test_regression_governance.py`

## Operational files

- CI workflow: `.github/workflows/ci.yml`
- Packaging metadata: `pyproject.toml`
- Shortcut commands: `Makefile`
