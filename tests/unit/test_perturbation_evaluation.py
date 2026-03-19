from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
import pytest
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from torch import nn

from model_failure_lab.models.export import build_prediction_records
from model_failure_lab.perturbations import (
    build_family_severity_matrix,
    build_family_summary,
    build_severity_summary,
    build_source_delta_summary,
    build_suite_summary,
    generate_perturbation_suite,
    load_clean_source_predictions,
    load_saved_run_scorer,
    score_perturbation_suite,
    write_perturbation_bundle,
)
from model_failure_lab.tracking import build_run_metadata, write_metadata
from model_failure_lab.utils.paths import (
    build_baseline_run_dir,
    build_mitigation_run_dir,
    build_perturbation_run_dir,
    build_prediction_artifact_path,
)


class _FakeTokenizer:
    pad_token_id = 0

    def __call__(
        self,
        text: str,
        *,
        truncation: bool,
        max_length: int,
        padding: bool,
    ) -> dict[str, list[int]]:
        del truncation, padding
        token_ids = [min(len(token) + 1, 20) for token in text.split()[:max_length]]
        return {"input_ids": token_ids, "attention_mask": [1] * len(token_ids)}


class _TinyClassifier(nn.Module):
    def __init__(self, vocab_size: int = 32, hidden_size: int = 8, num_labels: int = 2) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, hidden_size)
        self.classifier = nn.Linear(hidden_size, num_labels)
        self.loss_fn = nn.CrossEntropyLoss()

    def forward(
        self,
        *,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: torch.Tensor | None = None,
    ):
        embedded = self.embedding(input_ids)
        pooled = (embedded * attention_mask.unsqueeze(-1)).sum(dim=1) / attention_mask.sum(
            dim=1,
            keepdim=True,
        ).clamp_min(1)
        logits = self.classifier(pooled)
        loss = None if labels is None else self.loss_fn(logits, labels)
        return type("Output", (), {"loss": loss, "logits": logits})


def _source_samples() -> list[dict[str, object]]:
    return [
        {
            "sample_id": "train_0",
            "text": "steady calm example",
            "label": 0,
            "split": "train",
            "group_id": "group_a",
            "is_id": True,
            "is_ood": False,
            "dataset_name": "civilcomments",
            "group_attributes": {"identity_any": 1},
            "raw_split": "train",
            "raw_index": 0,
        },
        {
            "sample_id": "train_1",
            "text": "steady quiet example",
            "label": 0,
            "split": "train",
            "group_id": "group_a",
            "is_id": True,
            "is_ood": False,
            "dataset_name": "civilcomments",
            "group_attributes": {"identity_any": 1},
            "raw_split": "train",
            "raw_index": 1,
        },
        {
            "sample_id": "train_2",
            "text": "toxic loud example",
            "label": 1,
            "split": "train",
            "group_id": "group_b",
            "is_id": True,
            "is_ood": False,
            "dataset_name": "civilcomments",
            "group_attributes": {"identity_any": 1},
            "raw_split": "train",
            "raw_index": 2,
        },
        {
            "sample_id": "train_3",
            "text": "toxic sharp example",
            "label": 1,
            "split": "train",
            "group_id": "group_b",
            "is_id": True,
            "is_ood": False,
            "dataset_name": "civilcomments",
            "group_attributes": {"identity_any": 1},
            "raw_split": "train",
            "raw_index": 3,
        },
        {
            "sample_id": "val_0",
            "text": "calm validation sample",
            "label": 0,
            "split": "validation",
            "group_id": "group_a",
            "is_id": False,
            "is_ood": True,
            "dataset_name": "civilcomments",
            "group_attributes": {"identity_any": 1},
            "raw_split": "val",
            "raw_index": 4,
        },
        {
            "sample_id": "val_1",
            "text": "toxic validation sample",
            "label": 1,
            "split": "validation",
            "group_id": "group_b",
            "is_id": False,
            "is_ood": True,
            "dataset_name": "civilcomments",
            "group_attributes": {"identity_any": 1},
            "raw_split": "val",
            "raw_index": 5,
        },
    ]


def _create_logistic_source_run() -> tuple[Path, dict[str, object], list[dict[str, object]]]:
    run_id = "logistic_source"
    samples = _source_samples()
    run_dir = build_baseline_run_dir("logistic_tfidf", run_id, create=True)
    checkpoint_dir = run_dir / "checkpoint"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    train_samples = [sample for sample in samples if sample["split"] == "train"]
    validation_samples = [sample for sample in samples if sample["split"] == "validation"]

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
    train_matrix = vectorizer.fit_transform([str(sample["text"]) for sample in train_samples])
    classifier = LogisticRegression(max_iter=1000, solver="liblinear", random_state=13)
    classifier.fit(train_matrix, [int(sample["label"]) for sample in train_samples])

    joblib.dump(vectorizer, checkpoint_dir / "vectorizer.joblib")
    joblib.dump(classifier, checkpoint_dir / "logistic_model.joblib")

    validation_matrix = vectorizer.transform([str(sample["text"]) for sample in validation_samples])
    probability_rows = classifier.predict_proba(validation_matrix).tolist()
    predicted_labels = classifier.predict(validation_matrix).tolist()
    validation_records = build_prediction_records(
        run_id=run_id,
        model_name="logistic_tfidf",
        sample_ids=[str(sample["sample_id"]) for sample in validation_samples],
        splits=[str(sample["split"]) for sample in validation_samples],
        true_labels=[int(sample["label"]) for sample in validation_samples],
        predicted_labels=[int(label) for label in predicted_labels],
        probability_rows=[[float(row[0]), float(row[1])] for row in probability_rows],
        group_ids=[str(sample["group_id"]) for sample in validation_samples],
        is_id_flags=[bool(sample["is_id"]) for sample in validation_samples],
        is_ood_flags=[bool(sample["is_ood"]) for sample in validation_samples],
    )
    validation_path = build_prediction_artifact_path(run_dir, "validation")
    pd.DataFrame(validation_records).to_parquet(validation_path, index=False)

    metadata = build_run_metadata(
        run_id=run_id,
        experiment_type="baseline",
        model_name="logistic_tfidf",
        dataset_name="civilcomments",
        split_details={
            "train": "train",
            "validation": "validation",
            "id_test": "id_test",
            "ood_test": "ood_test",
        },
        random_seed=13,
        resolved_config={
            "run_id": run_id,
            "experiment_group": "baselines_v1",
            "experiment_type": "baseline",
            "model_name": "logistic_tfidf",
            "dataset_name": "civilcomments",
            "split_details": {
                "train": "train",
                "validation": "validation",
                "id_test": "id_test",
                "ood_test": "ood_test",
            },
            "seed": 13,
            "tags": ["baseline", "logistic_tfidf"],
            "notes": "",
            "data": {"group_fields": ["male", "female"]},
            "eval": {"primary_metric": "macro_f1"},
        },
        command="python scripts/run_baseline.py --model logistic_tfidf",
        run_dir=run_dir,
        artifact_paths={
            "checkpoint": str(checkpoint_dir),
            "selected_checkpoint": str(checkpoint_dir / "logistic_model.joblib"),
            "predictions": {"validation": str(validation_path)},
        },
        notes="fixture",
        tags=["baseline", "logistic_tfidf"],
        status="completed",
    )
    metadata_path = write_metadata(run_dir, metadata)
    return metadata_path, metadata, validation_samples


def _create_distilbert_metadata(
    *,
    run_id: str,
    mitigation_method: str | None = None,
    learned_temperature: float | None = None,
) -> dict[str, object]:
    if mitigation_method == "temperature_scaling":
        run_dir = build_mitigation_run_dir("temperature_scaling", "distilbert", run_id, create=True)
    else:
        run_dir = build_baseline_run_dir("distilbert", run_id, create=True)

    checkpoint_dir = run_dir / "checkpoint"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    model = _TinyClassifier()
    torch.save(model.state_dict(), checkpoint_dir / "best_model.pt")
    (checkpoint_dir / "tokenizer_config.json").write_text(
        json.dumps({"pretrained_name": "tiny-distilbert", "max_length": 32}),
        encoding="utf-8",
    )

    artifact_paths = {
        "checkpoint": str(checkpoint_dir),
        "selected_checkpoint": str(checkpoint_dir / "best_model.pt"),
    }
    if mitigation_method == "temperature_scaling":
        scaler_path = checkpoint_dir / "temperature_scaler.json"
        scaler_path.write_text(
            json.dumps({"learned_temperature": float(learned_temperature or 2.0)}),
            encoding="utf-8",
        )
        artifact_paths["temperature_scaler_json"] = str(scaler_path)

    metadata = {
        "run_id": run_id,
        "model_name": "distilbert",
        "dataset_name": "civilcomments",
        "artifact_paths": artifact_paths,
        "resolved_config": {
            "model_name": "distilbert",
            "model": {
                "pretrained_name": "tiny-distilbert",
                "max_length": 32,
                "batch_size": {"eval": 2},
            },
            "train": {"eval_batch_size": 2},
        },
    }
    if mitigation_method is not None:
        metadata["mitigation_method"] = mitigation_method
    return metadata


def _perturbation_samples() -> list[dict[str, object]]:
    return [
        {
            "perturbed_sample_id": "perturbed_a",
            "source_sample_id": "val_0",
            "perturbation_family": "typo_noise",
            "severity": "low",
            "perturbation_seed": 13,
            "text": "calm validation smaple",
            "true_label": 0,
            "source_split": "validation",
            "source_group_id": "group_a",
            "source_is_id": False,
            "source_is_ood": True,
            "dataset_name": "civilcomments",
            "applied_operations": [{"type": "substitute"}],
        },
        {
            "perturbed_sample_id": "perturbed_b",
            "source_sample_id": "val_1",
            "perturbation_family": "format_degradation",
            "severity": "high",
            "perturbation_seed": 13,
            "text": "toxicvalidation sample",
            "true_label": 1,
            "source_split": "validation",
            "source_group_id": "group_b",
            "source_is_id": False,
            "source_is_ood": True,
            "dataset_name": "civilcomments",
            "applied_operations": [{"type": "merge_token_boundaries"}],
        },
    ]


def test_load_clean_source_predictions_fails_when_selected_ids_are_missing(temp_artifact_root):
    metadata_path, _, _ = _create_logistic_source_run()

    with pytest.raises(ValueError, match="missing required source samples"):
        load_clean_source_predictions(
            metadata_path,
            split="validation",
            source_sample_ids=["val_0", "missing_sample"],
        )


def test_logistic_saved_run_scoring_builds_completed_summary_bundle(temp_artifact_root):
    metadata_path, metadata, validation_samples = _create_logistic_source_run()
    suite = generate_perturbation_suite(
        validation_samples,
        source_run_id=str(metadata["run_id"]),
        model_name="logistic_tfidf",
        families=["typo_noise", "format_degradation"],
        severities=["low", "high"],
        selection_seed=13,
        perturbation_seed=13,
    )
    clean_frame = load_clean_source_predictions(
        metadata_path,
        split="validation",
        source_sample_ids=[str(sample["sample_id"]) for sample in validation_samples],
    )
    scorer = load_saved_run_scorer(metadata)
    perturbed_frame = score_perturbation_suite(
        suite.to_records(),
        run_id="perturb_eval",
        scorer=scorer,
    )

    suite_summary = build_suite_summary(clean_frame, perturbed_frame)
    family_summary = build_family_summary(clean_frame, perturbed_frame)
    severity_summary = build_severity_summary(clean_frame, perturbed_frame)
    family_severity_matrix = build_family_severity_matrix(clean_frame, perturbed_frame)
    source_delta_summary = build_source_delta_summary(clean_frame, perturbed_frame)

    assert set(["source_sample_id", "perturbation_family", "severity"]).issubset(
        perturbed_frame.columns
    )
    assert suite_summary.loc[0, "source_sample_count"] == 2
    assert len(family_summary) == 2
    assert len(severity_summary) == 2
    assert len(family_severity_matrix) == 4
    assert len(source_delta_summary) == 2

    perturbation_dir = build_perturbation_run_dir(metadata_path.parent, "perturb_eval", create=True)
    artifact_paths = write_perturbation_bundle(
        perturbation_dir,
        suite=suite,
        source_run_metadata=metadata,
        resolved_config={"perturbation": {"max_source_samples": 2, "output_tag": "debug"}},
        perturbed_predictions=perturbed_frame,
        suite_summary=suite_summary,
        family_summary=family_summary,
        severity_summary=severity_summary,
        family_severity_matrix=family_severity_matrix,
        source_delta_summary=source_delta_summary,
    )

    assert Path(artifact_paths["predictions_perturbed_parquet"]).exists()
    assert Path(artifact_paths["suite_summary_csv"]).exists()
    assert Path(artifact_paths["family_summary_csv"]).exists()
    assert Path(artifact_paths["source_delta_summary_csv"]).exists()


def test_temperature_scaling_saved_run_scorer_applies_learned_temperature(temp_artifact_root):
    perturbation_samples = _perturbation_samples()
    baseline_metadata = _create_distilbert_metadata(run_id="distilbert_baseline")
    scaled_metadata = _create_distilbert_metadata(
        run_id="distilbert_temp_scaled",
        mitigation_method="temperature_scaling",
        learned_temperature=3.0,
    )

    baseline_scorer = load_saved_run_scorer(
        baseline_metadata,
        tokenizer_factory=lambda _name: _FakeTokenizer(),
        model_factory=lambda _name, _num_labels: _TinyClassifier(),
    )
    scaled_scorer = load_saved_run_scorer(
        scaled_metadata,
        tokenizer_factory=lambda _name: _FakeTokenizer(),
        model_factory=lambda _name, _num_labels: _TinyClassifier(),
    )

    baseline_frame = score_perturbation_suite(
        perturbation_samples,
        run_id="baseline_eval",
        scorer=baseline_scorer,
    )
    scaled_frame = score_perturbation_suite(
        perturbation_samples,
        run_id="scaled_eval",
        scorer=scaled_scorer,
    )

    assert {"logit_0", "logit_1"}.issubset(baseline_frame.columns)
    assert baseline_frame["prob_1"].round(6).tolist() != scaled_frame["prob_1"].round(6).tolist()
    assert all(
        abs(prob_0 + prob_1 - 1.0) < 1.0e-6
        for prob_0, prob_1 in zip(
            scaled_frame["prob_0"].astype(float),
            scaled_frame["prob_1"].astype(float),
            strict=True,
        )
    )
