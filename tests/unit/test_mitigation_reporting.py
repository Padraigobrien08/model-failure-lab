from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from model_failure_lab.models.export import build_prediction_records
from model_failure_lab.reporting import (
    build_mitigation_comparison_table,
    build_report_summary,
    classify_mitigation_verdict,
    load_report_inputs,
    pair_mitigation_candidates_with_parents,
    select_report_candidates,
)
from model_failure_lab.utils.paths import (
    build_baseline_run_dir,
    build_mitigation_run_dir,
    build_prediction_artifact_path,
)
from scripts.run_shift_eval import run_command as run_shift_eval_command


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def _build_prediction_rows(
    *,
    run_id: str,
    model_name: str,
    split: str,
    is_id: bool,
    is_ood: bool,
    group_accuracy: dict[str, float],
    group_support: dict[str, int],
) -> list[dict[str, object]]:
    sample_ids: list[str] = []
    splits: list[str] = []
    true_labels: list[int] = []
    predicted_labels: list[int] = []
    probability_rows: list[list[float]] = []
    group_ids: list[str] = []
    is_id_flags: list[bool] = []
    is_ood_flags: list[bool] = []

    for group_name, support in group_support.items():
        accuracy = float(group_accuracy[group_name])
        correct_count = int(round(support * accuracy))
        for index in range(support):
            true_label = index % 2
            predicted_label = true_label if index < correct_count else 1 - true_label
            confidence = 0.82 if predicted_label == true_label else 0.76
            prob_1 = confidence if predicted_label == 1 else 1.0 - confidence

            sample_ids.append(f"{split}_{group_name}_{index}")
            splits.append(split)
            true_labels.append(true_label)
            predicted_labels.append(predicted_label)
            probability_rows.append([1.0 - prob_1, prob_1])
            group_ids.append(group_name)
            is_id_flags.append(is_id)
            is_ood_flags.append(is_ood)

    return build_prediction_records(
        run_id=run_id,
        model_name=model_name,
        sample_ids=sample_ids,
        splits=splits,
        true_labels=true_labels,
        predicted_labels=predicted_labels,
        probability_rows=probability_rows,
        group_ids=group_ids,
        is_id_flags=is_id_flags,
        is_ood_flags=is_ood_flags,
    )


def _create_evaluation_bundle(
    *,
    model_name: str,
    source_run_id: str,
    eval_id: str,
    experiment_group: str,
    root_kind: str = "baseline",
    mitigation_method: str | None = None,
    source_parent_run_id: str | None = None,
    id_score: float = 0.8,
    ood_score: float = 0.62,
    overall_score: float = 0.68,
    worst_group_score: float = 0.44,
    ece: float = 0.07,
    brier_score: float = 0.12,
) -> None:
    del overall_score, ece, brier_score
    if root_kind == "mitigation":
        source_run_dir = build_mitigation_run_dir(
            mitigation_method or "reweighting",
            model_name,
            source_run_id,
            create=True,
        )
    else:
        source_run_dir = build_baseline_run_dir(model_name, source_run_id, create=True)

    group_support = {"group_low": 150, "group_mid": 140}
    id_group_accuracy = {
        "group_low": max(min(id_score - 0.03, 0.99), 0.0),
        "group_mid": max(min(id_score + 0.03, 0.99), 0.0),
    }
    ood_group_accuracy = {
        "group_low": max(min(worst_group_score, 0.99), 0.0),
        "group_mid": max(min((2 * ood_score) - worst_group_score, 0.99), 0.0),
    }
    prediction_records = {
        "id_test": _build_prediction_rows(
            run_id=source_run_id,
            model_name=model_name,
            split="id_test",
            is_id=True,
            is_ood=False,
            group_accuracy=id_group_accuracy,
            group_support=group_support,
        ),
        "ood_test": _build_prediction_rows(
            run_id=source_run_id,
            model_name=model_name,
            split="ood_test",
            is_id=False,
            is_ood=True,
            group_accuracy=ood_group_accuracy,
            group_support=group_support,
        ),
    }

    artifact_paths = {"predictions": {}}
    for split, records in prediction_records.items():
        output_path = build_prediction_artifact_path(source_run_dir, split)
        pd.DataFrame(records).to_parquet(output_path, index=False)
        artifact_paths["predictions"][split] = str(output_path)

    metadata_payload: dict[str, object] = {
        "source_run_id": source_run_id,
        "run_id": source_run_id,
        "experiment_type": root_kind,
        "model_name": model_name,
        "dataset_name": "civilcomments",
        "experiment_group": experiment_group,
        "split_details": {
            "train": "train",
            "validation": "validation",
            "id_test": "id_test",
            "ood_test": "ood_test",
        },
        "resolved_config": {
            "experiment_group": experiment_group,
            "seed": 13,
            "tags": [experiment_group, root_kind, model_name],
            "data": {
                "dataset_name": "civilcomments",
                "label_field": "toxicity",
                "text_field": "comment_text",
                "group_fields": ["male", "female"],
                "raw_splits": {"train": "train", "val": "val", "test": "test"},
                "split_details": {
                    "train": "train",
                    "validation": "validation",
                    "id_test": "id_test",
                    "ood_test": "ood_test",
                },
                "split_role_policy": {
                    "train": {
                        "raw_split": "train",
                        "selector": "train_remainder",
                        "is_id": True,
                        "is_ood": False,
                    },
                    "validation": {
                        "raw_split": "val",
                        "selector": "full_split",
                        "is_id": False,
                        "is_ood": True,
                    },
                    "id_test": {
                        "raw_split": "train",
                        "selector": "deterministic_holdout",
                        "is_id": True,
                        "is_ood": False,
                        "holdout_fraction": 0.1,
                        "holdout_seed": 13,
                    },
                    "ood_test": {
                        "raw_split": "test",
                        "selector": "full_split",
                        "is_id": False,
                        "is_ood": True,
                    },
                },
                "validation": {
                    "subgroup_min_samples_warning": 25,
                    "preview_samples": 5,
                },
            },
            "eval": {"primary_metric": "macro_f1"},
        },
        "artifact_paths": artifact_paths,
    }
    if source_parent_run_id is not None:
        metadata_payload["parent_run_id"] = source_parent_run_id
        metadata_payload["mitigation_method"] = mitigation_method
        metadata_payload["mitigation_config"] = {
            "comparison_tolerances": {
                "id_macro_f1_max_drop": 0.01,
                "overall_macro_f1_max_drop": 0.01,
                "ece_neutral_tolerance": 0.005,
            }
        }
        metadata_payload["resolved_config"] = {
            **dict(metadata_payload["resolved_config"]),
            "mitigation": {
                "method": mitigation_method,
                "comparison_tolerances": {
                    "id_macro_f1_max_drop": 0.01,
                    "overall_macro_f1_max_drop": 0.01,
                    "ece_neutral_tolerance": 0.005,
                },
            },
        }
    _write_json(source_run_dir / "metadata.json", metadata_payload)

    with patch("scripts.run_shift_eval.generate_run_id", return_value=eval_id):
        run_shift_eval_command(
            [
                "--run-id",
                source_run_id,
                "--splits",
                "id_test,ood_test",
                "--min-group-support",
                "100",
                "--calibration-bins",
                "5",
            ]
        )


def test_build_mitigation_comparison_table_pairs_parent_and_child(temp_artifact_root):
    _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="baseline_parent",
        eval_id="eval_parent",
        experiment_group="mitigation_suite",
    )
    _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="reweight_child",
        eval_id="eval_reweight",
        experiment_group="mitigation_suite",
        root_kind="mitigation",
        mitigation_method="reweighting",
        source_parent_run_id="baseline_parent",
        id_score=0.795,
        ood_score=0.66,
        overall_score=0.69,
        worst_group_score=0.48,
        ece=0.069,
        brier_score=0.119,
    )

    candidates = select_report_candidates(load_report_inputs(experiment_group="mitigation_suite"))
    table = build_mitigation_comparison_table(candidates)

    assert table["parent_eval_id"].tolist() == ["eval_parent"]
    assert table["mitigation_eval_id"].tolist() == ["eval_reweight"]
    assert table["ood_macro_f1_delta"].iloc[0] > 0.0
    assert table["worst_group_f1_delta"].iloc[0] > 0.0
    assert table["verdict"].iloc[0] == "win"


def test_pair_mitigation_candidates_with_parents_fails_without_parent(temp_artifact_root):
    _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="temperature_child",
        eval_id="eval_temperature",
        experiment_group="mitigation_missing_parent",
        root_kind="mitigation",
        mitigation_method="temperature_scaling",
        source_parent_run_id="baseline_parent_missing",
        ece=0.03,
        brier_score=0.08,
    )

    candidates = load_report_inputs(experiment_group="mitigation_missing_parent")
    with pytest.raises(ValueError, match="missing its parent baseline evaluation"):
        pair_mitigation_candidates_with_parents(candidates)


def test_classify_mitigation_verdict_covers_tradeoff_and_failure_cases():
    tradeoff = classify_mitigation_verdict(
        mitigation_method="reweighting",
        deltas={
            "id_macro_f1_delta": -0.03,
            "overall_macro_f1_delta": 0.0,
            "ood_macro_f1_delta": 0.05,
            "worst_group_f1_delta": 0.02,
        },
    )
    failure = classify_mitigation_verdict(
        mitigation_method="temperature_scaling",
        deltas={
            "id_macro_f1_delta": 0.0,
            "overall_macro_f1_delta": 0.0,
            "ood_macro_f1_delta": 0.0,
            "worst_group_f1_delta": 0.0,
            "ece_delta": 0.0,
            "brier_score_delta": 0.0,
        },
    )

    assert tradeoff == "tradeoff"
    assert failure == "failure"


def test_classify_mitigation_verdict_supports_group_dro():
    win = classify_mitigation_verdict(
        mitigation_method="group_dro",
        deltas={
            "id_macro_f1_delta": 0.0,
            "overall_macro_f1_delta": 0.0,
            "ood_macro_f1_delta": 0.01,
            "worst_group_f1_delta": 0.03,
            "ece_delta": 0.0,
        },
    )
    tradeoff = classify_mitigation_verdict(
        mitigation_method="group_dro",
        deltas={
            "id_macro_f1_delta": -0.02,
            "overall_macro_f1_delta": 0.0,
            "ood_macro_f1_delta": 0.02,
            "worst_group_f1_delta": 0.01,
            "ece_delta": 0.006,
        },
    )

    assert win == "win"
    assert tradeoff == "tradeoff"


def test_classify_mitigation_verdict_supports_group_balanced_sampling():
    win = classify_mitigation_verdict(
        mitigation_method="group_balanced_sampling",
        deltas={
            "id_macro_f1_delta": 0.0,
            "overall_macro_f1_delta": 0.0,
            "ood_macro_f1_delta": 0.02,
            "worst_group_f1_delta": 0.01,
            "ece_delta": 0.0,
            "brier_score_delta": 0.0,
        },
    )
    tradeoff = classify_mitigation_verdict(
        mitigation_method="group_balanced_sampling",
        deltas={
            "id_macro_f1_delta": 0.0,
            "overall_macro_f1_delta": -0.02,
            "ood_macro_f1_delta": 0.02,
            "worst_group_f1_delta": 0.01,
            "ece_delta": 0.002,
            "brier_score_delta": 0.01,
        },
    )

    assert win == "win"
    assert tradeoff == "tradeoff"


def test_build_report_summary_computes_seeded_verdict_counts():
    mitigation_comparison_table = pd.DataFrame(
        [
            {
                "parent_eval_id": "eval_parent_13",
                "parent_label": "distilbert:seed13_parent",
                "mitigation_label": "temperature_scaling:seed13_child",
                "mitigation_method": "temperature_scaling",
                "verdict": "win",
                "ood_macro_f1_delta": 0.0,
                "worst_group_f1_delta": 0.0,
                "ece_delta": -0.01,
            },
            {
                "parent_eval_id": "eval_parent_42",
                "parent_label": "distilbert:seed42_parent",
                "mitigation_label": "temperature_scaling:seed42_child",
                "mitigation_method": "temperature_scaling",
                "verdict": "win",
                "ood_macro_f1_delta": 0.0,
                "worst_group_f1_delta": 0.0,
                "ece_delta": -0.02,
            },
            {
                "parent_eval_id": "eval_parent_87",
                "parent_label": "distilbert:seed87_parent",
                "mitigation_label": "temperature_scaling:seed87_child",
                "mitigation_method": "temperature_scaling",
                "verdict": "tradeoff",
                "ood_macro_f1_delta": -0.01,
                "worst_group_f1_delta": -0.01,
                "ece_delta": -0.01,
            },
        ]
    )

    report_summary = build_report_summary(
        [],
        comparison_table=pd.DataFrame(),
        subgroup_table=pd.DataFrame(),
        calibration_table=pd.DataFrame(),
        mitigation_comparison_table=mitigation_comparison_table,
        report_title="Phase 18 Seeded Temperature Scaling",
    )

    assert report_summary["mitigation_verdict_counts"] == {
        "win": 2,
        "tradeoff": 1,
        "failure": 0,
    }
    assert report_summary["seeded_interpretation"] == "stable"
    assert report_summary["mitigation_method_summaries"] is None


def test_build_report_summary_computes_method_aware_seeded_mitigation_summaries():
    mitigation_comparison_table = pd.DataFrame(
        [
            {
                "parent_eval_id": "eval_parent_13",
                "parent_label": "distilbert:seed13_parent",
                "mitigation_label": "temperature_scaling:seed13_child",
                "mitigation_method": "temperature_scaling",
                "verdict": "win",
                "ood_macro_f1_delta": 0.0,
                "worst_group_f1_delta": 0.0,
                "ece_delta": -0.01,
            },
            {
                "parent_eval_id": "eval_parent_42",
                "parent_label": "distilbert:seed42_parent",
                "mitigation_label": "temperature_scaling:seed42_child",
                "mitigation_method": "temperature_scaling",
                "verdict": "win",
                "ood_macro_f1_delta": 0.0,
                "worst_group_f1_delta": 0.0,
                "ece_delta": -0.01,
            },
            {
                "parent_eval_id": "eval_parent_87",
                "parent_label": "distilbert:seed87_parent",
                "mitigation_label": "temperature_scaling:seed87_child",
                "mitigation_method": "temperature_scaling",
                "verdict": "win",
                "ood_macro_f1_delta": 0.0,
                "worst_group_f1_delta": 0.0,
                "ece_delta": -0.01,
            },
            {
                "parent_eval_id": "eval_parent_13",
                "parent_label": "distilbert:seed13_parent",
                "mitigation_label": "reweighting:seed13_child",
                "mitigation_method": "reweighting",
                "verdict": "tradeoff",
                "ood_macro_f1_delta": 0.02,
                "worst_group_f1_delta": 0.01,
                "ece_delta": 0.0,
            },
            {
                "parent_eval_id": "eval_parent_42",
                "parent_label": "distilbert:seed42_parent",
                "mitigation_label": "reweighting:seed42_child",
                "mitigation_method": "reweighting",
                "verdict": "win",
                "ood_macro_f1_delta": 0.03,
                "worst_group_f1_delta": 0.02,
                "ece_delta": 0.0,
            },
            {
                "parent_eval_id": "eval_parent_87",
                "parent_label": "distilbert:seed87_parent",
                "mitigation_label": "reweighting:seed87_child",
                "mitigation_method": "reweighting",
                "verdict": "failure",
                "ood_macro_f1_delta": 0.0,
                "worst_group_f1_delta": 0.0,
                "ece_delta": 0.0,
            },
        ]
    )

    report_summary = build_report_summary(
        [],
        comparison_table=pd.DataFrame(),
        subgroup_table=pd.DataFrame(),
        calibration_table=pd.DataFrame(),
        mitigation_comparison_table=mitigation_comparison_table,
        report_title="Phase 19 Seeded Reweighting",
    )

    assert report_summary["mitigation_verdict_counts"] == {
        "win": 4,
        "tradeoff": 1,
        "failure": 1,
    }
    assert report_summary["seeded_interpretation"] == "mixed"
    assert report_summary["mitigation_method_summaries"] == {
        "temperature_scaling": {
            "comparison_count": 3,
            "verdict_counts": {"win": 3, "tradeoff": 0, "failure": 0},
            "seeded_interpretation": "stable",
        },
        "reweighting": {
            "comparison_count": 3,
            "verdict_counts": {"win": 1, "tradeoff": 1, "failure": 1},
            "seeded_interpretation": "mixed",
        },
    }
