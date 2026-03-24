# v1.3 Findings

This document is the authoritative narrative layer for the saved `v1.3` evidence package.

The default-visible milestone story is grounded in these saved reports:

- [Phase 18 seeded temperature-scaling package](../artifacts/reports/comparisons/phase18_temperature_scaling_seeded/20260321_143714_report_0eea/report.md)
- [Phase 19 seeded reweighting package](../artifacts/reports/comparisons/phase19_reweighting_seeded/20260321_224830_report_12f3/report.md)
- [Phase 20 seeded stability package](../artifacts/reports/comparisons/phase20_stability/20260322_164903_report_d7d4/report.md)

Exploratory, non-promoted evidence:

- [Phase 23 `group_dro` scout report](../artifacts/reports/comparisons/phase23_group_dro_scout_seed_13/20260324_130155_report_f6a8/report.md)

## Official Evidence Set

The official/default-visible `v1.3` package is the seeded baseline and mitigation story:

- Logistic TF-IDF seeded baseline cohort
- DistilBERT seeded baseline cohort
- DistilBERT plus `temperature_scaling`
- DistilBERT plus `reweighting`
- the aggregate Phase 20 stability package

The `group_dro` scout exists for auditability, but it is exploratory-only and intentionally excluded
from the default UI views and official milestone package.

## What We Learned

### 1. The Baseline Shift Story Survived Seed Variation

Phase 20 shows that both official baseline cohorts are stable across seeds. The DistilBERT baseline
remains the stronger OOD model, beating Logistic Regression on OOD Macro F1 by a mean `0.053`
across matched seeds. That model advantage does not remove the central benchmark problem: the
DistilBERT robustness gap remains stable across seeds, so failure under shift is still a real part
of the benchmark story rather than a one-off run artifact.

Supporting report:

- [Phase 20 seeded stability package](../artifacts/reports/comparisons/phase20_stability/20260322_164903_report_d7d4/report.md)

### 2. Temperature Scaling Is A Stable Calibration Win

`temperature_scaling` remains the cleanest mitigation result in the repo. Across the three official
DistilBERT seeds it finishes `win=3`, `tradeoff=0`, `failure=0`, and the Phase 20 package labels it
`stable`. The mean ECE delta is `-0.011`, with matching Brier improvement, while OOD and worst-group
metrics stay effectively unchanged.

That makes the calibration conclusion stronger than it was in `v1.1`: the original story was not
just true for one run, it held across the seeded cohort.

Supporting reports:

- [Phase 18 seeded temperature-scaling package](../artifacts/reports/comparisons/phase18_temperature_scaling_seeded/20260321_143714_report_0eea/report.md)
- [Phase 20 seeded stability package](../artifacts/reports/comparisons/phase20_stability/20260322_164903_report_d7d4/report.md)

### 3. Reweighting Is Still The Best Current Robustness Lane, But It Is Mixed

`reweighting` did produce the strongest robustness-oriented signal we have so far, but not a clean
or fully stable one. Across the official seeded cohort it landed `win=2`, `tradeoff=1`,
`failure=0`, and the Phase 20 package labels it `mixed`.

The best summary of the lane is:

- mean worst-group F1 delta `+0.060`
- mean OOD Macro F1 delta approximately flat (`+0.0002`)
- mean ID Macro F1 delta `-0.011`
- calibration regressed modestly instead of improving

So the repo now has evidence that robustness-targeted mitigation can move the right metric, but not
yet with the same clarity or reliability as the calibration lane.

Supporting reports:

- [Phase 19 seeded reweighting package](../artifacts/reports/comparisons/phase19_reweighting_seeded/20260321_224830_report_12f3/report.md)
- [Phase 20 seeded stability package](../artifacts/reports/comparisons/phase20_stability/20260322_164903_report_d7d4/report.md)

### 4. The Challenger Scout Was Worth Running, But Not Worth Promoting

Phase 23 tested `group_dro` as a robustness-focused challenger on the seed-13 scout path. The
scout failed relative to the seeded DistilBERT parent:

- OOD Macro F1 delta `-0.037`
- worst-group F1 delta `-0.215`
- ECE delta `+0.033`

That was enough to stop the lane cleanly without spending more GPU time on seeds `42` and `87`.
This is an important part of the milestone story: the repo did not cherry-pick only positive
results. It ran a plausible challenger, evaluated it honestly, and kept the failure available for
inspection without promoting it into official evidence.

Supporting report:

- [Phase 23 `group_dro` scout report](../artifacts/reports/comparisons/phase23_group_dro_scout_seed_13/20260324_130155_report_f6a8/report.md)

## Final Interpretation

The comparative `v1.3` conclusion is:

- calibration story: `stable`
- robustness story: `mixed`
- challenger scout: rejected

That is stronger than the old single-seed story, but it is not yet strong enough to justify
broader benchmark expansion. The repo now has a credible seeded mitigation reference lane
(`temperature_scaling`) and a plausible but still unstable robustness lane (`reweighting`), but it
does not yet have a robustness mitigation that is both strong and easy to interpret.

## Recommendation

Dataset expansion remains `defer`.

Reason:

- the robustness-oriented mitigation story is still mixed
- `reweighting` is useful but not yet reliably clean
- the tested `group_dro` challenger was not worth promotion

The next milestone should improve interpretability and auditability around the saved evidence, then
either tighten the robustness lane further or introduce one new bounded robustness challenger before
adding a second dataset.

## Inspect Or Reproduce

- Launch the read-only UI: [run_results_ui.py](../scripts/run_results_ui.py)
- Re-read the seeded stability synthesis: [Phase 20 report](../artifacts/reports/comparisons/phase20_stability/20260322_164903_report_d7d4/report.md)
- Compare the two official mitigation lanes directly:
  - [Phase 18 temperature scaling](../artifacts/reports/comparisons/phase18_temperature_scaling_seeded/20260321_143714_report_0eea/report.md)
  - [Phase 19 reweighting](../artifacts/reports/comparisons/phase19_reweighting_seeded/20260321_224830_report_12f3/report.md)
- Review the rejected exploratory challenger:
  - [Phase 23 `group_dro` scout](../artifacts/reports/comparisons/phase23_group_dro_scout_seed_13/20260324_130155_report_f6a8/report.md)
