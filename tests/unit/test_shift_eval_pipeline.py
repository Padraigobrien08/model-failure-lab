from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from model_failure_lab.config import load_experiment_config
from model_failure_lab.evaluation.bundle import (
    build_evaluation_metadata,
    write_evaluation_bundle,
)
from model_failure_lab.runners.dispatch import dispatch_shift_eval
from model_failure_lab.tracking import write_metadata
from model_failure_lab.utils.paths import (
    build_baseline_run_dir,
    build_evaluation_artifact_paths,
    build_evaluation_run_dir,
    build_prediction_artifact_path,
)


def _prediction_row(
    *,
    run_id: str,
    sample_id: str,
    split: str,
    true_label: int,
    pred_label: int,
    prob_1: float,
    group_id: str,
    is_id: bool,
    is_ood: bool,
) -> dict[str, object]:
    return {
        "run_id": run_id,
        "sample_id": sample_id,
        "split": split,
        "model_name": "logistic_tfidf",
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


def _create_saved_source_run(temp_artifact_root) -> tuple[Path, dict[str, object]]:
    source_run_id = "saved_source_run"
    source_run_dir = build_baseline_run_dir("logistic_tfidf", source_run_id, create=True)
    train_path = build_prediction_artifact_path(source_run_dir, "train")
    validation_path = build_prediction_artifact_path(source_run_dir, "validation")
    test_path = build_prediction_artifact_path(source_run_dir, "test")

    pd.DataFrame(
        [
            _prediction_row(
                run_id=source_run_id,
                sample_id="train_0",
                split="train",
                true_label=0,
                pred_label=0,
                prob_1=0.1,
                group_id="group_a",
                is_id=True,
                is_ood=False,
            ),
            _prediction_row(
                run_id=source_run_id,
                sample_id="train_1",
                split="train",
                true_label=1,
                pred_label=1,
                prob_1=0.9,
                group_id="group_b",
                is_id=True,
                is_ood=False,
            ),
        ]
    ).to_parquet(train_path, index=False)
    pd.DataFrame(
        [
            _prediction_row(
                run_id=source_run_id,
                sample_id="val_0",
                split="validation",
                true_label=0,
                pred_label=0,
                prob_1=0.2,
                group_id="group_a",
                is_id=False,
                is_ood=True,
            ),
            _prediction_row(
                run_id=source_run_id,
                sample_id="val_1",
                split="validation",
                true_label=1,
                pred_label=0,
                prob_1=0.2,
                group_id="group_b",
                is_id=False,
                is_ood=True,
            ),
        ]
    ).to_parquet(validation_path, index=False)
    pd.DataFrame(
        [
            _prediction_row(
                run_id=source_run_id,
                sample_id="test_0",
                split="test",
                true_label=1,
                pred_label=1,
                prob_1=0.8,
                group_id="group_b",
                is_id=False,
                is_ood=True,
            )
        ]
    ).to_parquet(test_path, index=False)

    source_metadata = {
        "run_id": source_run_id,
        "model_name": "logistic_tfidf",
        "dataset_name": "civilcomments",
        "experiment_group": "baselines_v1",
        "split_details": {
            "train": "train",
            "validation": "validation",
            "id_test": "id_test",
            "ood_test": "ood_test",
        },
        "resolved_config": {
            "experiment_group": "baselines_v1",
            "seed": 13,
            "tags": ["baseline", "logistic_tfidf"],
            "data": {"group_fields": ["male", "female"]},
            "eval": {"primary_metric": "macro_f1"},
        },
        "artifact_paths": {
            "predictions": {
                "train": str(train_path),
                "validation": str(validation_path),
                "test": str(test_path),
            }
        },
    }
    metadata_path = source_run_dir / "metadata.json"
    metadata_path.write_text(json.dumps(source_metadata), encoding="utf-8")
    return metadata_path, source_metadata


def test_write_evaluation_bundle_persists_expected_files(temp_artifact_root):
    source_run_dir = build_baseline_run_dir("logistic_tfidf", "bundle_source", create=True)
    eval_dir = build_evaluation_run_dir(source_run_dir, "eval_bundle", create=True)

    artifact_paths = write_evaluation_bundle(
        eval_dir,
        split_metric_rows=[
            {
                "slice_type": "overall",
                "slice_name": "overall",
                "sample_count": 4,
                "support": 4,
                "accuracy": 0.75,
                "macro_f1": 0.73,
                "precision": 0.8,
                "recall": 0.7,
                "binary_f1": 0.75,
                "auroc": 0.9,
                "avg_predicted_score": 0.55,
                "avg_negative_score": 0.45,
                "mean_confidence": 0.8,
                "score_std": 0.2,
                "positive_label_rate": 0.5,
                "positive_prediction_rate": 0.5,
                "tn": 1,
                "fp": 0,
                "fn": 1,
                "tp": 2,
            }
        ],
        id_ood_comparison_rows=[
            {
                "metric": "accuracy",
                "id_value": 0.9,
                "ood_value": 0.6,
                "delta": 0.3,
                "id_support": 2,
                "ood_support": 2,
            }
        ],
        subgroup_rows=[
            {
                "grouping_type": "group_id",
                "group_column": "group_id",
                "group_name": "group_a",
                "attribute_name": None,
                "support": 2,
                "eligible_for_worst_group": True,
                "accuracy": 1.0,
                "macro_f1": 1.0,
                "binary_f1": 1.0,
                "precision": 1.0,
                "recall": 1.0,
                "auroc": 1.0,
                "avg_predicted_score": 0.5,
                "mean_confidence": 0.8,
                "error_rate": 0.0,
                "minimum_support": 2,
            }
        ],
        worst_group_summary={
            "minimum_support": 2,
            "reported_group_count": 1,
            "eligible_group_count": 1,
            "low_support_group_count": 0,
            "worst_group_f1": {"group_id": "group_a", "value": 1.0, "support": 2},
            "worst_group_accuracy": {"group_id": "group_a", "value": 1.0, "support": 2},
        },
        robustness_gaps={
            "robustness_gap_accuracy": 0.3,
            "robustness_gap_f1": 0.2,
            "robustness_gap_auroc": 0.1,
        },
        calibration_summary_rows=[
            {
                "slice_name": "overall",
                "sample_count": 4,
                "ece": 0.1,
                "brier_score": 0.08,
                "bin_count": 5,
                "non_empty_bin_count": 3,
            }
        ],
        calibration_bin_rows=[
            {
                "slice_name": "overall",
                "bin_index": 0,
                "bin_lower": 0.0,
                "bin_upper": 0.2,
                "count": 1,
                "avg_confidence": 0.1,
                "empirical_accuracy": 0.0,
                "calibration_gap": 0.1,
            }
        ],
        confidence_summary={"overall": {"all": {"count": 4}}},
        diagnostics_payload={"score_distribution": {"count": 4}},
    )

    assert Path(artifact_paths["overall_metrics_json"]).exists()
    assert Path(artifact_paths["split_metrics_csv"]).exists()
    assert Path(artifact_paths["calibration_bins_csv"]).exists()
    assert Path(artifact_paths["confidence_summary_json"]).exists()


def test_dispatch_shift_eval_completes_and_writes_bundle(temp_artifact_root):
    source_metadata_path, source_metadata = _create_saved_source_run(temp_artifact_root)
    config = load_experiment_config("civilcomments_logistic_baseline")
    config["experiment_type"] = "shift_eval"
    config["run_id"] = "evaluation_bundle"
    config["experiment_group"] = source_metadata["resolved_config"]["experiment_group"]
    config["eval"]["requested_splits"] = ["validation", "test"]
    config["eval"]["min_group_support"] = 1
    config["eval"]["calibration_bins"] = 5

    eval_dir = build_evaluation_run_dir(
        source_metadata_path.parent,
        str(config["run_id"]),
        create=True,
    )
    initial_metadata = build_evaluation_metadata(
        eval_id=str(config["run_id"]),
        source_run_metadata=source_metadata,
        source_metadata_path=source_metadata_path,
        resolved_config=config,
        command="python scripts/run_shift_eval.py --run-id saved_source_run",
        eval_dir=eval_dir,
        evaluated_splits=["validation", "test"],
        min_group_support=1,
        calibration_bins=5,
        status="running",
    )
    metadata_path = write_metadata(eval_dir, initial_metadata, create_checkpoint_dir=False)

    result = dispatch_shift_eval(
        config=config,
        target_run_id=str(source_metadata["run_id"]),
        source_metadata_path=source_metadata_path,
        run_dir=eval_dir,
        metadata_path=metadata_path,
        metrics_path=eval_dir / "overall_metrics.json",
        preset_name="civilcomments_logistic_baseline",
    )

    final_metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    artifact_paths = build_evaluation_artifact_paths(eval_dir)

    assert result.status == "completed"
    assert result.metrics_path == Path(artifact_paths["overall_metrics_json"])
    assert final_metadata["status"] == "completed"
    assert final_metadata["source_run_id"] == source_metadata["run_id"]
    assert final_metadata["experiment_group"] == "baselines_v1"
    assert final_metadata["source_experiment_group"] == "baselines_v1"
    assert final_metadata["resolved_config"]["experiment_group"] == "baselines_v1"
    assert final_metadata["evaluated_splits"] == ["validation", "test"]
    assert Path(artifact_paths["overall_metrics_json"]).exists()
    assert Path(artifact_paths["subgroup_metrics_csv"]).exists()
