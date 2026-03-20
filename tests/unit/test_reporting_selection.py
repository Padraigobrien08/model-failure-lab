from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from model_failure_lab.models.export import build_prediction_records
from model_failure_lab.reporting import (
    discover_evaluation_bundles,
    load_report_inputs,
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
        accuracy = 0.8 if split == "id_test" else (0.45 if group_name == "group_low" else 0.72)
        correct_count = int(round(support * accuracy))
        for index in range(support):
            true_label = index % 2
            predicted_label = true_label if index < correct_count else 1 - true_label
            confidence = 0.84 if predicted_label == true_label else 0.77
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
    dataset_name: str = "civilcomments",
    label_field: str = "toxicity",
    text_field: str = "comment_text",
    evaluator_version: str = "eval-schema-v1",
    subgroup_fields: list[str] | None = None,
    min_group_support: int = 100,
) -> Path:
    del evaluator_version
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
    prediction_records = {
        "id_test": _build_prediction_rows(
            run_id=source_run_id,
            model_name=model_name,
            split="id_test",
            is_id=True,
            is_ood=False,
            group_support=group_support,
        ),
        "ood_test": _build_prediction_rows(
            run_id=source_run_id,
            model_name=model_name,
            split="ood_test",
            is_id=False,
            is_ood=True,
            group_support=group_support,
        ),
    }
    artifact_paths = {"predictions": {}}
    for split, records in prediction_records.items():
        output_path = build_prediction_artifact_path(source_run_dir, split)
        pd.DataFrame(records).to_parquet(output_path, index=False)
        artifact_paths["predictions"][split] = str(output_path)

    metadata_payload = {
        "run_id": source_run_id,
        "experiment_type": root_kind,
        "model_name": model_name,
        "dataset_name": dataset_name,
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
                "dataset_name": dataset_name,
                "label_field": label_field,
                "text_field": text_field,
                "group_fields": subgroup_fields or ["male", "female"],
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
    _write_json(source_run_dir / "metadata.json", metadata_payload)

    with patch("scripts.run_shift_eval.generate_run_id", return_value=eval_id):
        result = run_shift_eval_command(
            [
                "--run-id",
                source_run_id,
                "--splits",
                "id_test,ood_test",
                "--min-group-support",
                str(min_group_support),
                "--calibration-bins",
                "5",
            ]
        )
    return result.metadata_path


def test_discover_evaluation_bundles_by_experiment_group(temp_artifact_root):
    first_path = _create_evaluation_bundle(
        model_name="logistic_tfidf",
        source_run_id="baseline_a",
        eval_id="eval_a",
        experiment_group="baselines_v1",
    )
    second_path = _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="baseline_b",
        eval_id="eval_b",
        experiment_group="baselines_v1",
    )
    _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="baseline_c",
        eval_id="eval_c",
        experiment_group="different_group",
    )

    discovered = discover_evaluation_bundles(experiment_group="baselines_v1")

    assert discovered == sorted([first_path.resolve(), second_path.resolve()])


def test_discover_evaluation_bundles_by_experiment_group_for_mitigation_root(
    temp_artifact_root,
):
    parent_path = _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="baseline_parent",
        eval_id="eval_parent",
        experiment_group="mitigation_suite",
    )
    child_path = _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="reweight_child",
        eval_id="eval_child",
        experiment_group="mitigation_suite",
        root_kind="mitigation",
        mitigation_method="reweighting",
    )

    discovered = discover_evaluation_bundles(experiment_group="mitigation_suite")

    assert discovered == sorted([parent_path.resolve(), child_path.resolve()])


def test_load_report_inputs_by_explicit_eval_ids(temp_artifact_root):
    _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="baseline_c",
        eval_id="eval_c",
        experiment_group="different_group",
    )
    _create_evaluation_bundle(
        model_name="logistic_tfidf",
        source_run_id="baseline_a",
        eval_id="eval_a",
        experiment_group="baselines_v1",
    )

    candidates = load_report_inputs(eval_ids=["eval_a"])

    assert len(candidates) == 1
    assert candidates[0].eval_id == "eval_a"
    assert candidates[0].overall_metrics["headline_metrics"]["macro_f1"] is not None


def test_select_report_candidates_rejects_non_comparable_runs(temp_artifact_root):
    _create_evaluation_bundle(
        model_name="logistic_tfidf",
        source_run_id="baseline_a",
        eval_id="eval_a",
        experiment_group="baselines_v1",
        dataset_name="civilcomments",
    )
    _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="baseline_b",
        eval_id="eval_b",
        experiment_group="baselines_v1",
        dataset_name="other_dataset",
    )

    candidates = load_report_inputs(experiment_group="baselines_v1")

    with pytest.raises(ValueError, match="not comparable: dataset mismatch"):
        select_report_candidates(candidates)


def test_select_report_candidates_orders_by_model_and_source_run(temp_artifact_root):
    _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="baseline_b",
        eval_id="eval_b",
        experiment_group="baselines_v1",
    )
    _create_evaluation_bundle(
        model_name="logistic_tfidf",
        source_run_id="baseline_a",
        eval_id="eval_a",
        experiment_group="baselines_v1",
    )

    selected = select_report_candidates(load_report_inputs(experiment_group="baselines_v1"))

    assert [candidate.eval_id for candidate in selected] == ["eval_b", "eval_a"]
