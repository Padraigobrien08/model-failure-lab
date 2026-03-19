from __future__ import annotations

import json

import joblib

from model_failure_lab.config.loader import load_experiment_config
from model_failure_lab.data import CanonicalDataset, CanonicalSample
from model_failure_lab.models.logistic_tfidf import train_logistic_baseline
from model_failure_lab.utils.paths import build_baseline_run_dir
from scripts.run_baseline import run_command as run_baseline_command


def _sample(
    *,
    sample_id: str,
    text: str,
    label: int,
    split: str,
    group_id: str,
) -> CanonicalSample:
    return CanonicalSample(
        sample_id=sample_id,
        text=text,
        label=label,
        split=split,
        is_id=split in {"train", "id_test"},
        is_ood=split in {"validation", "ood_test"},
        group_id=group_id,
        group_attributes={"identity_any": 1},
        dataset_name="civilcomments",
        raw_split="train" if split == "train" else "val",
        raw_index=sample_id,
        source_metadata={},
    )


def _canonical_dataset() -> CanonicalDataset:
    samples = [
        _sample(
            sample_id="train_0",
            text="common_token negative_marker shared_context",
            label=0,
            split="train",
            group_id="group_a",
        ),
        _sample(
            sample_id="train_1",
            text="common_token negative_marker repeated_context",
            label=0,
            split="train",
            group_id="group_a",
        ),
        _sample(
            sample_id="train_2",
            text="common_token negative_marker shared_context",
            label=0,
            split="train",
            group_id="group_a",
        ),
        _sample(
            sample_id="train_3",
            text="common_token positive_marker shared_context",
            label=1,
            split="train",
            group_id="group_b",
        ),
        _sample(
            sample_id="train_4",
            text="common_token positive_marker repeated_context",
            label=1,
            split="train",
            group_id="group_b",
        ),
        _sample(
            sample_id="train_5",
            text="common_token positive_marker shared_context",
            label=1,
            split="train",
            group_id="group_b",
        ),
        _sample(
            sample_id="val_0",
            text="validation_only_token safe common_token",
            label=0,
            split="validation",
            group_id="group_a",
        ),
        _sample(
            sample_id="val_1",
            text="validation_only_token harmful repeated",
            label=1,
            split="validation",
            group_id="group_b",
        ),
    ]
    return CanonicalDataset(dataset_name="civilcomments", samples=samples)


def test_train_logistic_baseline_writes_artifacts_without_validation_vocab_leakage(
    temp_artifact_root,
):
    config = load_experiment_config("configs/experiments/civilcomments_logistic_baseline.yaml")
    config["run_id"] = "logistic_artifacts_test"
    run_dir = build_baseline_run_dir(config["model_name"], config["run_id"], create=True)

    artifacts = train_logistic_baseline(
        config,
        run_dir,
        dataset_loader=lambda *_args, **_kwargs: _canonical_dataset(),
    )

    vectorizer = joblib.load(artifacts.vectorizer_path)
    assert "validation_only_token" not in vectorizer.vocabulary_
    assert artifacts.model_path.exists()
    assert artifacts.prediction_paths["train"].exists()
    assert artifacts.prediction_paths["validation"].exists()
    assert artifacts.metrics_payload["primary_metric"]["name"] == "macro_f1"
    assert artifacts.metrics_payload["validation_metrics"]["macro_f1"] is not None


def test_run_baseline_command_executes_real_logistic_path(temp_artifact_root, monkeypatch):
    dataset = _canonical_dataset()
    monkeypatch.setattr(
        "model_failure_lab.models.logistic_tfidf.load_baseline_canonical_dataset",
        lambda *_args, **_kwargs: dataset,
    )

    result = run_baseline_command(
        ["--model", "logistic_tfidf", "--run-id", "logistic_command_test"]
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    metrics = json.loads(result.metrics_path.read_text(encoding="utf-8"))

    assert result.status == "completed"
    assert metadata["status"] == "completed"
    assert metadata["artifact_paths"]["predictions"]["train"].endswith(
        "predictions_train.parquet"
    )
    assert metadata["artifact_paths"]["predictions"]["validation"].endswith(
        "predictions_val.parquet"
    )
    assert metrics["primary_metric"]["value"] is not None
    assert (result.run_dir / "checkpoint" / "vectorizer.joblib").exists()
    assert (result.run_dir / "checkpoint" / "logistic_model.joblib").exists()
