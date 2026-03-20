# v1.1 Reproducibility Walkthrough

This is the canonical end-to-end runbook for `v1.1`.

It covers:

1. clean-machine setup
2. CivilComments materialization
3. the official baseline commands
4. saved-run evaluation and reporting
5. the official mitigation and perturbation follow-on paths
6. where to inspect the official `v1.1` evidence set

## Official Evidence Set

The curated `v1.1` package is the three-report set below:

- [Baseline comparison report](../artifacts/reports/comparisons/baselines_v1_1/20260320_161852_report_34b3/report.md)
- [Mitigation comparison report](../artifacts/reports/comparisons/phase13_temperature_scaling/20260320_171418_report_b3fb/report.md)
- [Perturbation comparison report](../artifacts/reports/perturbations/phase13_temperature_scaling_perturbations/20260320_172934_perturbation_report_cbd4/report.md)

If you only want the interpretation layer, skip to:

- [v1.1 findings](v1_1_findings.md)

## 1. Install

Use Python 3.11 or newer.

```bash
python -m pip install -e .[dev]
```

This is the supported `v1.1` workflow. You should not need to export `PYTHONPATH=src`.

## 2. Verify The Environment

Before running anything expensive:

```bash
python scripts/check_environment.py
```

You want this to confirm:

- `matplotlib`, `wilds`, `torch`, and `transformers` are importable
- the Matplotlib runtime directory is writable
- `distilbert-base-uncased` is the configured transformer
- whether DistilBERT assets are cached or will need first-run network access

If the local machine cannot sustain the transformer run, use:

- [Cloud GPU run guide](cloud-gpu-run.md)

If setup fails, use:

- [Troubleshooting](troubleshooting.md)

## 3. Materialize CivilComments

```bash
python scripts/download_data.py
```

This keeps WILDS as the raw source of truth and writes the local manifest plus validation bundle
under `artifacts/data/`.

## 4. Run The Official Baselines

The official `v1.1` cohort uses one Logistic Regression run and one DistilBERT run.

Logistic Regression:

```bash
python scripts/run_baseline.py --model logistic_tfidf --seed 13 --experiment-group baselines_v1_1 --tag v1.1_baseline
```

DistilBERT:

```bash
python scripts/run_baseline.py --model distilbert --seed 13 --tier constrained --experiment-group baselines_v1_1 --tag v1.1_baseline
```

Why `constrained`:

- the official `v1.1` DistilBERT evidence was produced with the constrained tier
- the constrained path preserves the same backbone, split policy, and selection contract
- it is the most reproducible option across modest hardware

If you want to try the canonical DistilBERT config on a stronger machine, that remains available:

```bash
python scripts/run_baseline.py --model distilbert --seed 13 --tier canonical --experiment-group baselines_v1_1 --tag v1.1_baseline
```

Official reference run IDs from the shipped `v1.1` evidence:

- Logistic baseline: `20260320_115756_baseline_bab8`
- DistilBERT baseline: `20260320_151004_baseline_2326`

## 5. Evaluate Saved Runs

After the baseline commands finish, evaluate each saved run:

```bash
python scripts/run_shift_eval.py --run-id <logistic_run_id>
python scripts/run_shift_eval.py --run-id <distilbert_run_id>
```

Then build the shared baseline report:

```bash
python scripts/build_report.py --experiment-group baselines_v1_1
```

The official shipped baseline report lives at:

- [baselines_v1_1/report.md](../artifacts/reports/comparisons/baselines_v1_1/20260320_161852_report_34b3/report.md)

## 6. Run The Official Mitigation Path

The official mitigation lane for `v1.1` is `temperature_scaling` on the real DistilBERT parent
run.

Run the child mitigation:

```bash
python scripts/run_mitigation.py --run-id <distilbert_parent_run_id> --method temperature_scaling --seed 13 --notes "Phase 13 official mitigation proof path"
```

Evaluate the child run:

```bash
python scripts/run_shift_eval.py --run-id <temperature_scaling_run_id>
```

Then build the official parent-versus-child mitigation report with explicit eval IDs:

```bash
python scripts/build_report.py --eval-ids <parent_eval_id>,<temperature_scaling_eval_id> --report-name phase13_temperature_scaling
```

Official reference IDs from the shipped evidence:

- parent baseline run: `20260320_151004_baseline_2326`
- refreshed parent eval: `20260320_171342_shift_eval_b834`
- temperature-scaling child run: `20260320_171203_temperature_scaling_1355`
- child eval: `20260320_171233_shift_eval_018a`

Official mitigation report:

- [phase13_temperature_scaling/report.md](../artifacts/reports/comparisons/phase13_temperature_scaling/20260320_171418_report_b3fb/report.md)

## 7. Run The Official Perturbation Comparison

The official perturbation comparison uses the same DistilBERT parent and the official
`temperature_scaling` child.

Run perturbation evaluation for both:

```bash
python scripts/run_perturbation_eval.py --run-id <distilbert_parent_run_id> --output-tag phase13_official
python scripts/run_perturbation_eval.py --run-id <temperature_scaling_run_id> --output-tag phase13_official
```

Then build the dedicated perturbation report:

```bash
python scripts/build_perturbation_report.py --eval-ids <parent_perturb_eval_id>,<temperature_scaling_perturb_eval_id> --report-name phase13_temperature_scaling_perturbations
```

Official reference IDs from the shipped evidence:

- parent perturbation bundle: `20260320_172420_perturbation_3d59`
- child perturbation bundle: `20260320_172710_perturbation_ea3f`

Official perturbation report:

- [phase13_temperature_scaling_perturbations/report.md](../artifacts/reports/perturbations/phase13_temperature_scaling_perturbations/20260320_172934_perturbation_report_cbd4/report.md)

## 8. Inspect The Official Evidence Package

If you want to inspect the exact real `v1.1` outputs without rerunning the whole benchmark, use:

- [Baseline comparison report](../artifacts/reports/comparisons/baselines_v1_1/20260320_161852_report_34b3/report.md)
- [Mitigation comparison report](../artifacts/reports/comparisons/phase13_temperature_scaling/20260320_171418_report_b3fb/report.md)
- [Perturbation comparison report](../artifacts/reports/perturbations/phase13_temperature_scaling_perturbations/20260320_172934_perturbation_report_cbd4/report.md)

## Notes On Reproducibility

- The official `v1.1` evidence is single-seed.
- The official DistilBERT evidence uses the constrained tier.
- The benchmark scope is one dataset: CivilComments from WILDS.
- Synthetic perturbation findings are separate from canonical WILDS ID/OOD conclusions.

## Where To Go Next

- For the interpretation layer: [v1.1 findings](v1_1_findings.md)
- For setup-only reference: [runtime setup](runtime-setup.md)
- For cloud execution: [cloud GPU run guide](cloud-gpu-run.md)
- For failures and setup issues: [troubleshooting](troubleshooting.md)
