from __future__ import annotations

import json

import pandas as pd

from model_failure_lab.evaluation import (
    build_split_metrics_rows,
    build_worst_group_summary,
    compute_aggregate_metrics,
    compute_subgroup_metrics,
    load_saved_predictions,
)
from model_failure_lab.utils.paths import build_baseline_run_dir, build_prediction_artifact_path


def _prediction_row(
    *,
    run_id: str = "eval_run",
    sample_id: str,
    split: str,
    true_label: int,
    pred_label: int,
    prob_1: float,
    group_id: str,
    is_id: bool,
    is_ood: bool,
    **extras,
) -> dict[str, object]:
    row: dict[str, object] = {
        "run_id": run_id,
        "sample_id": sample_id,
        "split": split,
        "model_name": "distilbert",
        "true_label": true_label,
        "pred_label": pred_label,
        "pred_score": prob_1,
        "prob_0": 1.0 - prob_1,
        "prob_1": prob_1,
        "is_correct": int(true_label == pred_label),
        "group_id": group_id,
        "is_id": is_id,
        "is_ood": is_ood,
    }
    row.update(extras)
    return row


def test_load_saved_predictions_reads_metadata_paths_and_alias_filters(temp_artifact_root):
    run_dir = build_baseline_run_dir("distilbert", "eval_loader_fixture", create=True)
    train_path = build_prediction_artifact_path(run_dir, "train")
    validation_path = build_prediction_artifact_path(run_dir, "validation")

    pd.DataFrame(
        [
            _prediction_row(
                sample_id="train_0",
                split="train",
                true_label=0,
                pred_label=0,
                prob_1=0.1,
                group_id="group_a",
                is_id=True,
                is_ood=False,
            )
        ]
    ).to_parquet(train_path, index=False)
    pd.DataFrame(
        [
            _prediction_row(
                sample_id="val_0",
                split="validation",
                true_label=1,
                pred_label=1,
                prob_1=0.9,
                group_id="group_b",
                is_id=False,
                is_ood=True,
                slice_identity_any=1,
            )
        ]
    ).to_parquet(validation_path, index=False)

    metadata_path = run_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "run_id": "eval_loader_fixture",
                "artifact_paths": {
                    "predictions": {
                        "train": str(train_path),
                        "validation": str(validation_path),
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    metadata, frame = load_saved_predictions(metadata_path, splits=["val"])

    assert metadata["run_id"] == "eval_loader_fixture"
    assert list(frame["sample_id"]) == ["val_0"]
    assert list(frame["split"]) == ["validation"]


def test_compute_aggregate_metrics_handles_degenerate_auroc():
    frame = pd.DataFrame(
        [
            _prediction_row(
                sample_id="deg_0",
                split="validation",
                true_label=0,
                pred_label=0,
                prob_1=0.2,
                group_id="group_a",
                is_id=False,
                is_ood=True,
            ),
            _prediction_row(
                sample_id="deg_1",
                split="validation",
                true_label=0,
                pred_label=1,
                prob_1=0.8,
                group_id="group_a",
                is_id=False,
                is_ood=True,
            ),
        ]
    )

    metrics = compute_aggregate_metrics(frame)

    assert metrics["sample_count"] == 2
    assert metrics["accuracy"] == 0.5
    assert metrics["auroc"] is None
    assert metrics["confusion_matrix"] == {"tn": 1, "fp": 1, "fn": 0, "tp": 0}


def test_build_split_metrics_rows_uses_explicit_id_ood_flags():
    frame = pd.DataFrame(
        [
            _prediction_row(
                sample_id="id_like_validation",
                split="validation",
                true_label=0,
                pred_label=0,
                prob_1=0.1,
                group_id="group_a",
                is_id=True,
                is_ood=False,
            ),
            _prediction_row(
                sample_id="ood_like_train",
                split="train",
                true_label=1,
                pred_label=1,
                prob_1=0.9,
                group_id="group_b",
                is_id=False,
                is_ood=True,
            ),
        ]
    )

    rows = build_split_metrics_rows(frame)
    rows_by_name = {row["slice_name"]: row for row in rows}

    assert rows_by_name["id"]["sample_count"] == 1
    assert rows_by_name["ood"]["sample_count"] == 1
    assert rows_by_name["validation"]["sample_count"] == 1
    assert rows_by_name["train"]["sample_count"] == 1


def test_compute_subgroup_metrics_preserves_low_support_and_attribute_slices():
    rows: list[dict[str, object]] = []
    for index in range(4):
        rows.append(
            _prediction_row(
                sample_id=f"group_a_{index}",
                split="validation",
                true_label=index % 2,
                pred_label=index % 2,
                prob_1=0.9 if index % 2 else 0.1,
                group_id="group_a",
                is_id=False,
                is_ood=True,
                slice_identity_any=1,
            )
        )
    rows.extend(
        [
            _prediction_row(
                sample_id="group_b_0",
                split="validation",
                true_label=0,
                pred_label=0,
                prob_1=0.2,
                group_id="group_b",
                is_id=False,
                is_ood=True,
                slice_identity_any=0,
            ),
            _prediction_row(
                sample_id="group_b_1",
                split="validation",
                true_label=0,
                pred_label=1,
                prob_1=0.8,
                group_id="group_b",
                is_id=False,
                is_ood=True,
                slice_identity_any=0,
            ),
            _prediction_row(
                sample_id="group_b_2",
                split="validation",
                true_label=1,
                pred_label=1,
                prob_1=0.9,
                group_id="group_b",
                is_id=False,
                is_ood=True,
                slice_identity_any=0,
            ),
            _prediction_row(
                sample_id="group_b_3",
                split="validation",
                true_label=1,
                pred_label=0,
                prob_1=0.2,
                group_id="group_b",
                is_id=False,
                is_ood=True,
                slice_identity_any=0,
            ),
        ]
    )
    rows.extend(
        [
            _prediction_row(
                sample_id="low_support_0",
                split="validation",
                true_label=1,
                pred_label=0,
                prob_1=0.1,
                group_id="low_support",
                is_id=False,
                is_ood=True,
                slice_identity_any=1,
            ),
            _prediction_row(
                sample_id="low_support_1",
                split="validation",
                true_label=1,
                pred_label=0,
                prob_1=0.2,
                group_id="low_support",
                is_id=False,
                is_ood=True,
                slice_identity_any=1,
            ),
        ]
    )

    subgroup_rows = compute_subgroup_metrics(
        pd.DataFrame(rows),
        min_support=3,
        attribute_columns=["slice_identity_any"],
    )
    rows_by_name = {row["group_name"]: row for row in subgroup_rows}
    summary = build_worst_group_summary(subgroup_rows, min_support=3)

    assert rows_by_name["low_support"]["eligible_for_worst_group"] is False
    assert rows_by_name["group_b"]["eligible_for_worst_group"] is True
    assert "identity_any=1" in rows_by_name
    assert summary["minimum_support"] == 3
    assert summary["worst_group_f1"]["group_id"] == "group_b"
    assert summary["worst_group_accuracy"]["group_id"] == "group_b"
