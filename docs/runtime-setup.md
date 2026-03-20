# Runtime Setup

This guide is the clean-machine setup path for `v1.1`.

## Prerequisites

- Python 3.11+
- enough disk for the CivilComments dataset and saved run artifacts
- network access for first-time WILDS download
- network access or a pre-populated local cache for the first `distilbert-base-uncased` run

## 1. Install The Project

```bash
python -m pip install -e .[dev]
```

The editable install is the supported setup path. The public scripts should run without a manual
`PYTHONPATH=src` export.

## 2. Verify The Environment

```bash
python scripts/check_environment.py
```

Successful output should confirm:

- `matplotlib`, `wilds`, `torch`, and `transformers` are importable
- a writable `MPLCONFIGDIR` is available for report generation
- the configured DistilBERT model is `distilbert-base-uncased`
- whether DistilBERT assets are already cached locally or the first run will need network access

If this command reports missing dependencies, resolve those first before launching benchmark runs.

## 3. Materialize CivilComments

```bash
python scripts/download_data.py
```

This prepares the manifest and validation bundle under `artifacts/data/` while keeping WILDS as the
raw source of truth.

## 4. Run The Baselines

```bash
python scripts/run_baseline.py --model logistic_tfidf
python scripts/run_baseline.py --model distilbert
```

Each run writes a complete artifact bundle under `artifacts/baselines/`.

## 5. Evaluate And Report

Evaluate a saved run:

```bash
python scripts/run_shift_eval.py --run-id <id>
```

Build a comparison report from saved evaluation bundles:

```bash
python scripts/build_report.py --experiment-group <name>
```

## 6. Optional Follow-On Paths

Mitigation:

```bash
python scripts/run_mitigation.py --run-id <distilbert_parent_id> --method reweighting
```

Perturbation stress testing:

```bash
python scripts/run_perturbation_eval.py --run-id <saved_run_id>
python scripts/build_perturbation_report.py --experiment-group <name>
```

## Smoke Check Sequence

If you want a short confidence pass before running long jobs:

```bash
python scripts/check_environment.py
python scripts/download_data.py
python scripts/run_baseline.py --model logistic_tfidf
```

Once those succeed, the DistilBERT baseline, shift evaluation, and reporting paths are the next
expected steps.
