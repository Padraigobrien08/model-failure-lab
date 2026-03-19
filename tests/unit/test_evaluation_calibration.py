from __future__ import annotations

import pandas as pd

from model_failure_lab.evaluation import (
    build_calibration_bins,
    build_confidence_summary,
    build_diagnostics_payload,
    build_id_ood_comparison,
    compute_calibration_summary,
    compute_robustness_gaps,
)


def _prediction_row(
    *,
    sample_id: str,
    split: str,
    true_label: int,
    pred_label: int,
    prob_1: float,
    is_id: bool,
    is_ood: bool,
) -> dict[str, object]:
    return {
        "run_id": "eval_run",
        "sample_id": sample_id,
        "split": split,
        "model_name": "distilbert",
        "true_label": true_label,
        "pred_label": pred_label,
        "pred_score": prob_1,
        "prob_0": 1.0 - prob_1,
        "prob_1": prob_1,
        "is_correct": int(true_label == pred_label),
        "group_id": "group_a" if is_id else "group_b",
        "is_id": is_id,
        "is_ood": is_ood,
    }


def test_build_id_ood_comparison_and_robustness_gaps():
    split_metric_rows = [
        {"slice_name": "id", "accuracy": 0.8, "macro_f1": 0.75, "auroc": 0.9, "support": 100},
        {"slice_name": "ood", "accuracy": 0.5, "macro_f1": 0.4, "auroc": 0.6, "support": 80},
    ]

    comparison_rows = build_id_ood_comparison(split_metric_rows)
    gaps = compute_robustness_gaps(split_metric_rows)
    rows_by_metric = {row["metric"]: row for row in comparison_rows}

    assert rows_by_metric["accuracy"]["delta"] == 0.3
    assert rows_by_metric["macro_f1"]["delta"] == 0.35
    assert rows_by_metric["auroc"]["delta"] == 0.3
    assert gaps["robustness_gap_accuracy"] == 0.3
    assert gaps["robustness_gap_f1"] == 0.35
    assert gaps["robustness_gap_auroc"] == 0.3


def test_build_id_ood_comparison_is_explicit_when_ood_is_missing():
    split_metric_rows = [
        {"slice_name": "id", "accuracy": 0.8, "macro_f1": 0.75, "auroc": 0.9, "support": 100},
    ]

    comparison_rows = build_id_ood_comparison(split_metric_rows)
    rows_by_metric = {row["metric"]: row for row in comparison_rows}

    assert rows_by_metric["accuracy"]["ood_value"] is None
    assert rows_by_metric["accuracy"]["delta"] is None


def test_compute_calibration_summary_returns_fixed_bins_for_all_slices():
    frame = pd.DataFrame(
        [
            _prediction_row(
                sample_id="id_0",
                split="train",
                true_label=0,
                pred_label=0,
                prob_1=0.1,
                is_id=True,
                is_ood=False,
            ),
            _prediction_row(
                sample_id="id_1",
                split="validation",
                true_label=1,
                pred_label=1,
                prob_1=0.9,
                is_id=True,
                is_ood=False,
            ),
            _prediction_row(
                sample_id="ood_0",
                split="test",
                true_label=0,
                pred_label=1,
                prob_1=0.8,
                is_id=False,
                is_ood=True,
            ),
            _prediction_row(
                sample_id="ood_1",
                split="test",
                true_label=1,
                pred_label=0,
                prob_1=0.2,
                is_id=False,
                is_ood=True,
            ),
        ]
    )

    calibration = compute_calibration_summary(frame, n_bins=4)
    summary_by_slice = {row["slice_name"]: row for row in calibration["summary_rows"]}
    overall_bins = [row for row in calibration["bin_rows"] if row["slice_name"] == "overall"]

    assert {"overall", "id", "ood"} == set(summary_by_slice)
    assert summary_by_slice["overall"]["ece"] is not None
    assert summary_by_slice["overall"]["brier_score"] is not None
    assert len(overall_bins) == 4
    assert {
        "bin_lower",
        "bin_upper",
        "count",
        "avg_confidence",
        "empirical_accuracy",
        "calibration_gap",
    } <= set(overall_bins[0])


def test_build_calibration_bins_preserves_empty_bins():
    frame = pd.DataFrame(
        [
            _prediction_row(
                sample_id="sample_0",
                split="validation",
                true_label=1,
                pred_label=1,
                prob_1=0.9,
                is_id=False,
                is_ood=True,
            )
        ]
    )

    rows = build_calibration_bins(frame, n_bins=3, slice_name="overall")

    assert len(rows) == 3
    assert sum(row["count"] for row in rows) == 1
    assert any(row["count"] == 0 for row in rows)


def test_build_confidence_summary_and_diagnostics_payload():
    frame = pd.DataFrame(
        [
            _prediction_row(
                sample_id="correct_low",
                split="train",
                true_label=0,
                pred_label=0,
                prob_1=0.1,
                is_id=True,
                is_ood=False,
            ),
            _prediction_row(
                sample_id="incorrect_high",
                split="test",
                true_label=0,
                pred_label=1,
                prob_1=0.9,
                is_id=False,
                is_ood=True,
            ),
        ]
    )

    confidence_summary = build_confidence_summary(frame, bins=5)
    diagnostics = build_diagnostics_payload(frame)

    assert confidence_summary["overall"]["correct"]["count"] == 1
    assert confidence_summary["overall"]["incorrect"]["count"] == 1
    assert len(confidence_summary["overall"]["all"]["histogram"]) == 5
    assert diagnostics["score_distribution"]["count"] == 2
    assert diagnostics["prediction_rate_by_split"][0]["split"] == "test"
