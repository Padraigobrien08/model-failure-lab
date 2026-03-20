from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
import torch

from model_failure_lab.config.loader import load_experiment_config
from model_failure_lab.mitigations import (
    apply_temperature_scaling,
    build_inherited_mitigation_config,
    fit_temperature_scaler,
    load_parent_run_context,
    run_temperature_scaling,
)
from model_failure_lab.models.export import REQUIRED_PREDICTION_COLUMNS, build_prediction_records
from model_failure_lab.tracking import build_run_metadata, write_metadata
from model_failure_lab.utils.paths import (
    build_baseline_run_dir,
    build_mitigation_run_dir,
    build_prediction_artifact_path,
)


def _write_parent_bundle(run_id: str) -> tuple[str, list[list[float]], list[int]]:
    resolved_config = load_experiment_config(
        "configs/experiments/civilcomments_distilbert_baseline.yaml"
    )
    resolved_config["run_id"] = run_id
    run_dir = build_baseline_run_dir("distilbert", run_id, create=True)
    checkpoint_path = run_dir / "checkpoint" / "best_model.pt"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text("checkpoint", encoding="utf-8")

    train_logits = [[2.0, -1.0], [1.5, -0.5], [-0.3, 1.4], [-0.8, 1.9]]
    train_labels = [0, 0, 1, 1]
    validation_logits = [[2.6, -0.4], [-0.1, 1.1]]
    validation_labels = [0, 1]
    id_test_logits = [[1.8, -0.2], [-0.3, 1.5]]
    id_test_labels = [0, 1]
    ood_test_logits = [[1.2, 0.1], [0.2, 1.0]]
    ood_test_labels = [0, 1]

    split_payloads = {
        "train": {
            "sample_ids": ["train_0", "train_1", "train_2", "train_3"],
            "splits": ["train"] * 4,
            "labels": train_labels,
            "group_ids": ["group_a", "group_a", "group_b", "group_b"],
            "is_id": [True, True, True, True],
            "is_ood": [False, False, False, False],
            "logits": train_logits,
        },
        "validation": {
            "sample_ids": ["val_0", "val_1"],
            "splits": ["validation", "validation"],
            "labels": validation_labels,
            "group_ids": ["group_a", "group_b"],
            "is_id": [False, False],
            "is_ood": [True, True],
            "logits": validation_logits,
        },
        "id_test": {
            "sample_ids": ["id_test_0", "id_test_1"],
            "splits": ["id_test", "id_test"],
            "labels": id_test_labels,
            "group_ids": ["group_a", "group_b"],
            "is_id": [True, True],
            "is_ood": [False, False],
            "logits": id_test_logits,
        },
        "ood_test": {
            "sample_ids": ["ood_test_0", "ood_test_1"],
            "splits": ["ood_test", "ood_test"],
            "labels": ood_test_labels,
            "group_ids": ["group_a", "group_b"],
            "is_id": [False, False],
            "is_ood": [True, True],
            "logits": ood_test_logits,
        },
    }

    prediction_paths: dict[str, str] = {}
    for split, payload in split_payloads.items():
        probabilities = torch.softmax(
            torch.tensor(payload["logits"], dtype=torch.float32),
            dim=-1,
        ).tolist()
        predicted_labels = [int(row[1] >= row[0]) for row in probabilities]
        records = build_prediction_records(
            run_id=run_id,
            model_name="distilbert",
            sample_ids=payload["sample_ids"],
            splits=payload["splits"],
            true_labels=payload["labels"],
            predicted_labels=predicted_labels,
            probability_rows=probabilities,
            group_ids=payload["group_ids"],
            is_id_flags=payload["is_id"],
            is_ood_flags=payload["is_ood"],
            logits_rows=payload["logits"],
        )
        output_path = build_prediction_artifact_path(run_dir, split)
        pd.DataFrame(records).to_parquet(output_path, index=False)
        prediction_paths[split] = str(output_path)

    metadata_payload = build_run_metadata(
        run_id=run_id,
        experiment_type="baseline",
        model_name="distilbert",
        dataset_name=resolved_config["dataset_name"],
        split_details=resolved_config["split_details"],
        random_seed=int(resolved_config["seed"]),
        resolved_config=resolved_config,
        command="python scripts/run_baseline.py --model distilbert",
        run_dir=run_dir,
        artifact_paths={
            "checkpoint": str(run_dir / "checkpoint"),
            "predictions": prediction_paths,
            "metrics_json": str(run_dir / "metrics.json"),
            "plots": str(run_dir / "figures"),
            "selected_checkpoint": str(checkpoint_path),
        },
        notes="temperature scaling parent fixture",
        tags=["baseline", "distilbert"],
        status="completed",
    )
    write_metadata(run_dir, metadata_payload)
    return run_id, validation_logits, validation_labels


def _rewrite_parent_metadata_as_imported_paths(run_id: str) -> None:
    run_dir = build_baseline_run_dir("distilbert", run_id, create=False)
    metadata_path = run_dir / "metadata.json"
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    payload["artifact_paths"]["checkpoint"] = (
        f"/workspace/model-failure-lab/artifacts/baselines/distilbert/{run_id}/checkpoint"
    )
    payload["artifact_paths"]["selected_checkpoint"] = (
        f"/workspace/model-failure-lab/artifacts/baselines/distilbert/{run_id}/checkpoint/"
        "best_model.pt"
    )
    payload["artifact_paths"]["predictions"] = {
        split: f"/workspace/model-failure-lab/artifacts/baselines/distilbert/{run_id}/"
        f"predictions_{suffix}.parquet"
        for split, suffix in {
            "train": "train",
            "validation": "val",
            "id_test": "id_test",
            "ood_test": "ood_test",
        }.items()
    }
    metadata_path.write_text(json.dumps(payload), encoding="utf-8")


def test_temperature_scaling_preset_contains_mitigation_payload():
    config = load_experiment_config(
        "configs/experiments/civilcomments_distilbert_temperature_scaling.yaml"
    )

    assert config["mitigation"]["method"] == "temperature_scaling"
    assert config["mitigation"]["temperature_scaling"]["fitting_split"] == "validation"
    assert config["mitigation"]["temperature_scaling"]["allow_checkpoint_regeneration"] is True


def test_fit_temperature_scaler_returns_positive_temperature():
    temperature = fit_temperature_scaler(
        [[3.0, -2.0], [-0.5, 1.0], [0.2, -0.1]],
        [0, 1, 0],
    )
    scaled_logits = apply_temperature_scaling([[1.0, -1.0], [-2.0, 2.0]], temperature)

    assert temperature > 0.0
    assert tuple(scaled_logits.shape) == (2, 2)


def test_run_temperature_scaling_uses_validation_logits_only_and_writes_predictions(
    temp_artifact_root,
):
    parent_run_id, validation_logits, validation_labels = _write_parent_bundle(
        "distilbert_temperature_parent"
    )
    parent_context = load_parent_run_context(parent_run_id)
    preset_config = load_experiment_config(
        "configs/experiments/civilcomments_distilbert_temperature_scaling.yaml"
    )
    preset_config["run_id"] = "temperature_scaling_child"
    config = build_inherited_mitigation_config(parent_context, preset_config)
    run_dir = build_mitigation_run_dir(
        "temperature_scaling",
        "distilbert",
        "temperature_scaling_child",
        create=True,
    )

    artifacts = run_temperature_scaling(config, run_dir)

    assert artifacts.logit_provenance == {
        "train": "saved_predictions",
        "validation": "saved_predictions",
        "id_test": "saved_predictions",
        "ood_test": "saved_predictions",
    }
    assert artifacts.learned_temperature == pytest.approx(
        fit_temperature_scaler(validation_logits, validation_labels),
        rel=1.0e-4,
    )
    scaler_payload = json.loads(artifacts.temperature_scaler_path.read_text(encoding="utf-8"))
    assert scaler_payload["fitting_split"] == "validation"
    assert scaler_payload["selected_checkpoint"].endswith("best_model.pt")

    validation_frame = pd.read_parquet(artifacts.prediction_paths["validation"])
    assert (
        list(validation_frame.columns[: len(REQUIRED_PREDICTION_COLUMNS)])
        == REQUIRED_PREDICTION_COLUMNS
    )
    assert validation_frame["run_id"].tolist() == ["temperature_scaling_child"] * 2
    assert Path(artifacts.prediction_paths["train"]).exists()
    assert Path(artifacts.prediction_paths["validation"]).exists()
    assert Path(artifacts.prediction_paths["id_test"]).exists()
    assert Path(artifacts.prediction_paths["ood_test"]).exists()


def test_run_temperature_scaling_relocates_imported_parent_artifacts(temp_artifact_root):
    parent_run_id, validation_logits, validation_labels = _write_parent_bundle(
        "distilbert_imported_temperature_parent"
    )
    _rewrite_parent_metadata_as_imported_paths(parent_run_id)
    parent_context = load_parent_run_context(parent_run_id)
    preset_config = load_experiment_config(
        "configs/experiments/civilcomments_distilbert_temperature_scaling.yaml"
    )
    preset_config["run_id"] = "temperature_scaling_imported_child"
    config = build_inherited_mitigation_config(parent_context, preset_config)
    run_dir = build_mitigation_run_dir(
        "temperature_scaling",
        "distilbert",
        "temperature_scaling_imported_child",
        create=True,
    )

    artifacts = run_temperature_scaling(config, run_dir)

    assert artifacts.learned_temperature == pytest.approx(
        fit_temperature_scaler(validation_logits, validation_labels),
        rel=1.0e-4,
    )
    assert artifacts.selected_checkpoint_path.exists()
    assert Path(artifacts.prediction_paths["validation"]).exists()
