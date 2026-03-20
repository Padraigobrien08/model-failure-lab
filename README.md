# Model Failure Lab

Model Failure Lab is a reproducible machine learning research project for studying how text
classification models fail under distribution shift. The benchmark workflow centers on CivilComments
from WILDS, with explicit separation between baseline, mitigation, evaluation, reporting, and
perturbation stress-test artifacts.

## Installation

Use Python 3.11 or newer.

```bash
python -m pip install -e .[dev]
```

This editable install is the supported clean-machine workflow for `v1.1`. You should not need to
export `PYTHONPATH=src` manually.

## Environment Check

Verify the benchmark runtime before starting any data or model runs:

```bash
python scripts/check_environment.py
```

This command checks:

- importability of `matplotlib`, `wilds`, `torch`, and `transformers`
- writable Matplotlib runtime configuration via `MPLCONFIGDIR`
- the configured DistilBERT model name: `distilbert-base-uncased`
- whether DistilBERT assets are already in the local cache or will need network access on first use

If dependencies are missing, the checker now prints the exact supported install command:

```bash
python -m pip install -e .[dev]
```

If DistilBERT assets are not cached yet, the checker also prints a Hugging Face prefetch command.

## Quickstart

Materialize CivilComments and produce the first baseline artifacts:

```bash
python scripts/download_data.py
python scripts/run_baseline.py --model logistic_tfidf --seed 13 --experiment-group baselines_v1_1 --tag v1.1_baseline
python scripts/run_baseline.py --model distilbert --seed 13 --tier canonical --experiment-group baselines_v1_1 --tag v1.1_baseline
```

If canonical DistilBERT settings are not practical on the local machine, use the constrained tier:

```bash
python scripts/run_baseline.py --model distilbert --seed 13 --tier constrained --experiment-group baselines_v1_1 --tag v1.1_baseline
```

Then evaluate a saved run and build a comparison report:

```bash
python scripts/run_shift_eval.py --run-id <id>
python scripts/build_report.py --experiment-group baselines_v1_1
```

## Benchmark Workflow

The public workflow remains script-first:

1. `python scripts/check_environment.py`
2. `python scripts/download_data.py`
3. `python scripts/run_baseline.py --model logistic_tfidf --seed 13 --experiment-group baselines_v1_1 --tag v1.1_baseline`
4. `python scripts/run_baseline.py --model distilbert --seed 13 --tier canonical --experiment-group baselines_v1_1 --tag v1.1_baseline`
5. `python scripts/run_shift_eval.py --run-id <id>`
6. `python scripts/build_report.py --experiment-group baselines_v1_1`

Optional follow-on commands:

```bash
python scripts/run_mitigation.py --run-id <distilbert_parent_id> --method reweighting
python scripts/run_perturbation_eval.py --run-id <saved_run_id>
python scripts/build_perturbation_report.py --experiment-group <name>
```

## More Docs

- [Runtime setup walkthrough](docs/runtime-setup.md)
- [Cloud GPU run guide](docs/cloud-gpu-run.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Configuration layout](configs/README.md)
