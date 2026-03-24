# v1.4 Closeout

This document is the authoritative closeout for the saved `v1.4` evidence package.

Start with the read-only UI:

- [run_results_ui.py](../scripts/run_results_ui.py)

The final closeout artifacts are:

- [Phase 20 seeded stability package](../artifacts/reports/comparisons/phase20_stability/20260322_164903_report_d7d4/report.md)
- [Phase 26 final robustness package](../artifacts/reports/comparisons/phase26_robustness_final/20260324_221348_report_bfbb/report.md)
- [Phase 27 final gate JSON](../artifacts/reports/closeout/phase27_gate/final_gate.json)

Exploratory, non-promoted evidence remains inspectable:

- [Phase 23 `group_dro` scout](../artifacts/reports/comparisons/phase23_group_dro_scout_seed_13/20260324_130155_report_f6a8/report.md)
- [Phase 25 `group_balanced_sampling` scout](../artifacts/reports/comparisons/phase25_group_balanced_sampling_scout_seed_13/20260324_212920_report_7c22/report.md)
- [Phase 25 promotion audit](../artifacts/reports/robustness_promotion_audit/phase25_group_balanced_sampling.md)

## Final Outcome

The full research cycle reached a real conclusion:

- baseline shift findings: `stable`
- calibration lane: `stable`
- robustness lane: `still_mixed`
- exploratory challengers: rejected
- expansion gate: `defer_now_reopen_under_conditions`

That is enough to close the current research question honestly. The project showed that the
benchmark failure story survives seeded validation and that calibration can be improved reliably,
but it did not produce a robustness mitigation that is both clearly stronger and consistently easy
to interpret.

## What Held Up

### 1. The benchmark failure story is real

The seeded baseline cohorts stayed stable across seeds, and DistilBERT still beat Logistic TF-IDF
on OOD Macro F1 while retaining a stable robustness gap. The distribution-shift problem in this
repo is therefore not a one-run artifact.

Supporting evidence:

- [Phase 20 seeded stability package](../artifacts/reports/comparisons/phase20_stability/20260322_164903_report_d7d4/report.md)

### 2. Temperature scaling is a solved calibration lane

`temperature_scaling` remains the cleanest mitigation result in the repo:

- `3/3` seeded wins
- stable ECE improvement
- stable Brier improvement
- no meaningful robustness upside

This is the strongest mitigation conclusion in the project because it is both reproducible and
easy to explain.

Supporting evidence:

- [Phase 18 seeded temperature-scaling package](../artifacts/reports/comparisons/phase18_temperature_scaling_seeded/20260321_143714_report_0eea/report.md)
- [Phase 20 seeded stability package](../artifacts/reports/comparisons/phase20_stability/20260322_164903_report_d7d4/report.md)

### 3. Reweighting is still the best current robustness lane, but it is not resolved

`reweighting` remains the best official robustness-oriented lane, but the final robustness package
keeps it at `still_mixed`:

- seeded outcome: `2/3` wins, `1/3` tradeoff
- mean worst-group F1 delta: `+0.060`
- mean OOD Macro F1 delta: effectively flat
- mean ID Macro F1 delta: negative
- calibration regressed instead of improved

That is a real signal, but not a clean robustness win.

Supporting evidence:

- [Phase 19 seeded reweighting package](../artifacts/reports/comparisons/phase19_reweighting_seeded/20260321_224830_report_12f3/report.md)
- [Phase 26 final robustness package](../artifacts/reports/comparisons/phase26_robustness_final/20260324_221348_report_bfbb/report.md)

## What Did Not Survive Promotion

Two bounded challenger scouts were run and kept exploratory:

### `group_dro`

`group_dro` failed the scout path and was stopped immediately. It worsened OOD and worst-group
behavior enough that there was no case for promotion.

### `group_balanced_sampling`

`group_balanced_sampling` improved worst-group F1 on the scout, but it regressed ID Macro F1, OOD
Macro F1, ECE, and Brier hard enough to fail the promotion bar. That made it a worse and less
interpretable story than `reweighting`, so it was explicitly marked `do_not_promote`.

Supporting evidence:

- [Phase 23 `group_dro` scout](../artifacts/reports/comparisons/phase23_group_dro_scout_seed_13/20260324_130155_report_f6a8/report.md)
- [Phase 25 `group_balanced_sampling` scout](../artifacts/reports/comparisons/phase25_group_balanced_sampling_scout_seed_13/20260324_212920_report_7c22/report.md)
- [Phase 25 promotion audit](../artifacts/reports/robustness_promotion_audit/phase25_group_balanced_sampling.md)

## Expansion Gate

The final dataset-expansion decision is:

- `defer_now_reopen_under_conditions`

Reason:

- calibration is solved more cleanly than robustness
- the best official robustness lane is still mixed
- the final challenger scouts did not produce a clearer replacement

The gate should reopen only when all of these are true:

1. Robustness lane achieves stable improvement instead of remaining mixed.
2. At least one mitigation shows consistent gains across seeds.
3. Robustness versus calibration tradeoffs are materially reduced or better understood.

The machine-readable gate is here:

- [final_gate.json](../artifacts/reports/closeout/phase27_gate/final_gate.json)

## Limits

This closeout still reflects a narrow but deliberate benchmark scope:

- one dataset: CivilComments
- one stronger neural baseline family: DistilBERT
- one stable calibration mitigation
- one mixed robustness mitigation
- two rejected exploratory challengers

That is enough for a credible first research cycle, but not enough for confident second-dataset
expansion.

## Practical Next Step

The research project can now be treated as complete for this cycle. The next substantial product
move should be presentation and usability, not more hidden experimental sprawl:

- preserve the artifact index as the stable evidence contract
- keep the Streamlit UI as the reference explorer
- build a proper React frontend later if the project shifts from research closeout to presentation
