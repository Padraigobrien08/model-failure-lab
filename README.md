# Model Failure Lab

Model Failure Lab is a reproducible machine learning research project for studying how text
classification models fail under distribution shift. The benchmark workflow centers on CivilComments
from WILDS, with explicit separation between baseline, mitigation, evaluation, reporting, and
perturbation stress-test artifacts.

## What Shipped In `v1.1`

- a clean-machine script-first workflow for CivilComments
- real Logistic Regression and DistilBERT baseline runs
- real mitigation validation for `temperature_scaling`
- real synthetic perturbation validation against the official DistilBERT lineage
- repository-ready report artifacts and findings docs

## Start here

For the full end-to-end workflow, read:

- [v1.1 reproducibility walkthrough](docs/v1_1_reproducibility.md)

That document is the canonical runbook for setup, baseline execution, evaluation, mitigation, and
perturbation reporting.

## Quickstart

Use Python 3.11 or newer.

```bash
python -m pip install -e .[dev]
python scripts/check_environment.py
python scripts/download_data.py
```

If you only want the detailed setup guidance first, see:

- [Runtime setup reference](docs/runtime-setup.md)

## Key results

- DistilBERT is the stronger real baseline on CivilComments, with OOD Macro F1 `0.800` versus
  `0.747` for Logistic Regression, but it still shows a measurable robustness gap of `0.071`.
- Temperature scaling is a calibration win, not a robustness win: ECE improves by `0.011` and
  Brier score by `0.0015`, while ID/OOD and worst-group metrics stay unchanged.
- Under the synthetic perturbation suite, average Macro F1 drops by `0.063`, with `typo_noise`
  the worst family and `high` the harshest severity. Calibration does not materially change that
  brittleness.

The full findings layer is here:

- [v1.1 findings](docs/v1_1_findings.md)

## Official evidence

The curated `v1.1` evidence package is the three-report set below:

- [Baseline comparison report](artifacts/reports/comparisons/baselines_v1_1/20260320_161852_report_34b3/report.md)
- [Mitigation comparison report](artifacts/reports/comparisons/phase13_temperature_scaling/20260320_171418_report_b3fb/report.md)
- [Perturbation comparison report](artifacts/reports/perturbations/phase13_temperature_scaling_perturbations/20260320_172934_perturbation_report_cbd4/report.md)

## Deep dive docs

- [v1.1 reproducibility walkthrough](docs/v1_1_reproducibility.md)
- [v1.1 findings](docs/v1_1_findings.md)
- [Runtime setup reference](docs/runtime-setup.md)
- [Cloud GPU run guide](docs/cloud-gpu-run.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Configuration layout](configs/README.md)
