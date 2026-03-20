# v1.1 Findings

This page is the concise interpretation layer for the real `v1.1` benchmark outputs.

It is grounded in the official saved reports:

- [Baseline comparison report](../artifacts/reports/comparisons/baselines_v1_1/20260320_161852_report_34b3/report.md)
- [Mitigation comparison report](../artifacts/reports/comparisons/phase13_temperature_scaling/20260320_171418_report_b3fb/report.md)
- [Perturbation comparison report](../artifacts/reports/perturbations/phase13_temperature_scaling_perturbations/20260320_172934_perturbation_report_cbd4/report.md)

## Official Evidence Set

The official `v1.1` package is exactly these three report roots:

- `artifacts/reports/comparisons/baselines_v1_1/20260320_161852_report_34b3/`
- `artifacts/reports/comparisons/phase13_temperature_scaling/20260320_171418_report_b3fb/`
- `artifacts/reports/perturbations/phase13_temperature_scaling_perturbations/20260320_172934_perturbation_report_cbd4/`

No exploratory runs are part of the milestone evidence package.

## What We Learned

### 1. DistilBERT Is The Stronger Baseline, But The Robustness Gap Is Still Real

From the official baseline report:

- DistilBERT reaches OOD Macro F1 `0.800`
- Logistic Regression reaches OOD Macro F1 `0.747`
- DistilBERT also leads on overall Macro F1 (`0.843` vs `0.779`) and overall calibration

That is a meaningful baseline win, but it does not remove distribution-shift sensitivity.
DistilBERT still shows an ID-to-OOD Macro F1 drop of `0.071`, which is larger than the logistic
baseline's `0.054`. In other words, the stronger model is better overall, but the benchmark still
exposes a measurable robustness gap under shift.

### 2. Temperature Scaling Improves Calibration, Not Robustness

The official mitigation report classifies `temperature_scaling` as a `win`, but the reason matters.

From the mitigation comparison table:

- `id_macro_f1_delta = 0.0`
- `ood_macro_f1_delta = 0.0`
- `worst_group_f1_delta = 0.0`
- `ece_delta = -0.010935`
- `brier_score_delta = -0.001457`
- `verdict = win`

That is a clean calibration result. The child run is better calibrated than the parent baseline,
but it does not materially improve robustness, worst-group performance, or label accuracy. This is
an important distinction: calibration can improve reliability of scores without fixing failure under
shift.

### 3. Calibration Does Not Reduce Synthetic Brittleness

The official perturbation comparison shows the same pattern under controlled input corruption.

From the perturbation report summary:

- average Macro F1 drop under the suite: `0.063`
- worst family: `typo_noise` with Macro F1 drop `0.103`
- harshest severity: `high` with Macro F1 drop `0.125`

Those findings are unchanged between the parent baseline and the temperature-scaled child. The
practical takeaway is that better-calibrated probabilities do not make the model less brittle to
text corruption. Input sensitivity remains a separate problem from confidence calibration.

## Caveats

- **Single seed**: all official `v1.1` evidence comes from one fixed-seed run path.
- **Constrained DistilBERT tier**: the official transformer evidence was produced with the
  constrained training tier rather than the canonical higher-budget tier.
- **One dataset**: the milestone uses CivilComments only, so none of these findings should be
  generalized beyond this benchmark without more evidence.
- **Synthetic perturbations are not WILDS OOD**: the perturbation report measures controlled text
  brittleness, not real-world distribution shift from the benchmark itself.

## Next Experiment

The clearest next step is to repeat the official baseline-plus-mitigation workflow across multiple
seeds.

That would test whether the three central conclusions are stable:

1. DistilBERT remains the stronger baseline on OOD performance.
2. Temperature scaling continues to improve calibration without changing robustness.
3. Perturbation brittleness remains largely unchanged by calibration.

Secondary future work, after multi-seed validation:

- complete `reweighting` as a fully evaluated mitigation path
- test mitigation ideas that target robustness directly rather than confidence calibration
- add a second dataset only after the current findings show acceptable stability

## Reproduce Or Inspect

- To rerun the full workflow: [v1.1 reproducibility walkthrough](v1_1_reproducibility.md)
- To inspect the raw official reports directly:
  - [baseline report](../artifacts/reports/comparisons/baselines_v1_1/20260320_161852_report_34b3/report.md)
  - [mitigation report](../artifacts/reports/comparisons/phase13_temperature_scaling/20260320_171418_report_b3fb/report.md)
  - [perturbation report](../artifacts/reports/perturbations/phase13_temperature_scaling_perturbations/20260320_172934_perturbation_report_cbd4/report.md)
