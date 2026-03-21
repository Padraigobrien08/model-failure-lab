from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import joblib
import pandas as pd
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from torch import nn

from model_failure_lab.config import load_experiment_config
from model_failure_lab.config.loader import _load_yaml_file
from model_failure_lab.data import CanonicalDataset, CanonicalSample
from model_failure_lab.models.export import build_prediction_records
from model_failure_lab.tracking import build_run_metadata, write_metadata
from model_failure_lab.utils.paths import (
    build_baseline_run_dir,
    build_prediction_artifact_path,
    config_root,
)
from scripts.build_perturbation_report import run_command as run_build_perturbation_report_command
from scripts.build_report import run_command as run_build_report_command
from scripts.check_environment import run_command as run_check_environment_command
from scripts.download_data import run_command as run_download_data_command
from scripts.run_baseline import run_command as run_baseline_command
from scripts.run_mitigation import run_command as run_mitigation_command
from scripts.run_perturbation_eval import run_command as run_perturbation_eval_command
from scripts.run_shift_eval import run_command as run_shift_eval_command

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class _FakeDataset:
    split_dict: dict[str, int]
    data_dir: str
    version: str
    metadata_fields: list[str]
    source_records: list[dict[str, object]]


def _fake_materialize(config: dict[str, object], *, download: bool):
    from model_failure_lab.data import materialize_civilcomments

    def fake_get_dataset(**_: object) -> _FakeDataset:
        return _FakeDataset(
            split_dict={"train": 0, "val": 1, "test": 2},
            data_dir="/tmp/fake_civilcomments",
            version="1.0",
            metadata_fields=["male", "female", "y"],
            source_records=[
                {
                    "raw_index": 0,
                    "raw_split": "train",
                    "comment_text": "sample train zero",
                    "toxicity": 0,
                    "male": 1,
                    "female": 0,
                    "LGBTQ": 0,
                    "christian": 0,
                    "muslim": 0,
                    "other_religions": 0,
                    "black": 0,
                    "white": 1,
                    "identity_any": 1,
                    "severe_toxicity": 0,
                    "obscene": 0,
                    "threat": 0,
                    "insult": 0,
                    "identity_attack": 0,
                    "sexual_explicit": 0,
                },
                {
                    "raw_index": 1,
                    "raw_split": "val",
                    "comment_text": "sample val one",
                    "toxicity": 1,
                    "male": 0,
                    "female": 1,
                    "LGBTQ": 0,
                    "christian": 1,
                    "muslim": 0,
                    "other_religions": 0,
                    "black": 1,
                    "white": 0,
                    "identity_any": 1,
                    "severe_toxicity": 0,
                    "obscene": 1,
                    "threat": 0,
                    "insult": 1,
                    "identity_attack": 0,
                    "sexual_explicit": 0,
                },
                {
                    "raw_index": 2,
                    "raw_split": "test",
                    "comment_text": "sample test two",
                    "toxicity": 0,
                    "male": 0,
                    "female": 0,
                    "LGBTQ": 1,
                    "christian": 0,
                    "muslim": 1,
                    "other_religions": 0,
                    "black": 0,
                    "white": 1,
                    "identity_any": 1,
                    "severe_toxicity": 0,
                    "obscene": 0,
                    "threat": 0,
                    "insult": 0,
                    "identity_attack": 0,
                    "sexual_explicit": 0,
                },
            ],
        )

    assert download is True
    return materialize_civilcomments(config, get_dataset_fn=fake_get_dataset)


def _baseline_sample(
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


def _baseline_dataset() -> CanonicalDataset:
    return CanonicalDataset(
        dataset_name="civilcomments",
        samples=[
            _baseline_sample(
                sample_id="train_0",
                text="negative calm steady",
                label=0,
                split="train",
                group_id="group_a",
            ),
            _baseline_sample(
                sample_id="train_1",
                text="negative calm quiet",
                label=0,
                split="train",
                group_id="group_a",
            ),
            _baseline_sample(
                sample_id="train_2",
                text="negative calm safe",
                label=0,
                split="train",
                group_id="group_a",
            ),
            _baseline_sample(
                sample_id="train_3",
                text="positive toxic loud",
                label=1,
                split="train",
                group_id="group_b",
            ),
            _baseline_sample(
                sample_id="train_4",
                text="positive toxic sharp",
                label=1,
                split="train",
                group_id="group_b",
            ),
            _baseline_sample(
                sample_id="train_5",
                text="positive toxic blunt",
                label=1,
                split="train",
                group_id="group_b",
            ),
            _baseline_sample(
                sample_id="val_0",
                text="negative calm validation_only",
                label=0,
                split="validation",
                group_id="group_a",
            ),
            _baseline_sample(
                sample_id="val_1",
                text="positive toxic validation_only",
                label=1,
                split="validation",
                group_id="group_b",
            ),
            _baseline_sample(
                sample_id="id_test_0",
                text="negative calm blind_id",
                label=0,
                split="id_test",
                group_id="group_a",
            ),
            _baseline_sample(
                sample_id="id_test_1",
                text="positive toxic blind_id",
                label=1,
                split="id_test",
                group_id="group_b",
            ),
            _baseline_sample(
                sample_id="ood_test_0",
                text="negative calm blind_ood",
                label=0,
                split="ood_test",
                group_id="group_a",
            ),
            _baseline_sample(
                sample_id="ood_test_1",
                text="positive toxic blind_ood",
                label=1,
                split="ood_test",
                group_id="group_b",
            ),
        ],
    )


def _write_distilbert_parent_run(
    run_id: str,
    *,
    with_saved_logits: bool = False,
    constrained: bool = False,
    tags: list[str] | None = None,
) -> None:
    baseline_config = load_experiment_config(
        "configs/experiments/civilcomments_distilbert_baseline.yaml"
    )
    baseline_config["run_id"] = run_id
    if constrained:
        baseline_config["model"] = _load_yaml_file(
            config_root() / "model" / "distilbert_constrained.yaml"
        )
        baseline_config["train"] = _load_yaml_file(
            config_root() / "train" / "distilbert_constrained.yaml"
        )
    run_dir = build_baseline_run_dir("distilbert", run_id, create=True)
    checkpoint_path = run_dir / "checkpoint" / "best_model.pt"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text("checkpoint", encoding="utf-8")

    artifact_paths = {
        "checkpoint": str(run_dir / "checkpoint"),
        "predictions": {},
        "metrics_json": str(run_dir / "metrics.json"),
        "plots": str(run_dir / "figures"),
        "selected_checkpoint": str(checkpoint_path),
    }

    if with_saved_logits:
        dataset = _baseline_dataset()
        samples_by_split = {
            split: [sample for sample in dataset.samples if sample.split == split]
            for split in ("train", "validation", "id_test", "ood_test")
        }
        for split, samples in samples_by_split.items():
            logits_rows = []
            for index, sample in enumerate(samples):
                if sample.label == 0:
                    logits_rows.append([2.0 + (0.1 * index), -0.4])
                else:
                    logits_rows.append([-0.4, 1.2 + (0.1 * index)])
            probability_rows = torch.softmax(
                torch.tensor(logits_rows, dtype=torch.float32),
                dim=-1,
            ).tolist()
            predicted_labels = [int(row[1] >= row[0]) for row in probability_rows]
            records = build_prediction_records(
                run_id=run_id,
                model_name="distilbert",
                sample_ids=[sample.sample_id for sample in samples],
                splits=[sample.split for sample in samples],
                true_labels=[sample.label for sample in samples],
                predicted_labels=predicted_labels,
                probability_rows=probability_rows,
                group_ids=[sample.group_id for sample in samples],
                is_id_flags=[sample.is_id for sample in samples],
                is_ood_flags=[sample.is_ood for sample in samples],
                logits_rows=logits_rows,
            )
            prediction_path = build_prediction_artifact_path(run_dir, split)
            pd.DataFrame(records).to_parquet(prediction_path, index=False)
            artifact_paths["predictions"][split] = str(prediction_path)

    parent_metadata = build_run_metadata(
        run_id=run_id,
        experiment_type="baseline",
        model_name="distilbert",
        dataset_name=baseline_config["dataset_name"],
        split_details=baseline_config["split_details"],
        random_seed=int(baseline_config["seed"]),
        resolved_config=baseline_config,
        command="python scripts/run_baseline.py --model distilbert",
        run_dir=run_dir,
        artifact_paths=artifact_paths,
        notes="parent fixture",
        tags=tags or ["baseline", "distilbert"],
        status="completed",
    )
    write_metadata(run_dir, parent_metadata)


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

    def save_pretrained(self, path):
        path.mkdir(parents=True, exist_ok=True)
        (path / "tokenizer.json").write_text("{}", encoding="utf-8")


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


def _saved_prediction_row(
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


def _create_saved_evaluation_source_run() -> str:
    run_id = "shift_eval_source"
    run_dir = build_baseline_run_dir("logistic_tfidf", run_id, create=True)
    checkpoint_dir = run_dir / "checkpoint"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    validation_path = build_prediction_artifact_path(run_dir, "validation")
    test_path = build_prediction_artifact_path(run_dir, "test")

    dataset = _baseline_dataset()
    train_samples = [sample for sample in dataset.samples if sample.split == "train"]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
    train_matrix = vectorizer.fit_transform([sample.text for sample in train_samples])
    classifier = LogisticRegression(max_iter=1000, solver="liblinear", random_state=13)
    classifier.fit(train_matrix, [sample.label for sample in train_samples])
    joblib.dump(vectorizer, checkpoint_dir / "vectorizer.joblib")
    joblib.dump(classifier, checkpoint_dir / "logistic_model.joblib")

    pd.DataFrame(
        [
            _saved_prediction_row(
                run_id=run_id,
                sample_id="val_0",
                split="validation",
                true_label=0,
                pred_label=0,
                prob_1=0.2,
                group_id="group_a",
                is_id=False,
                is_ood=True,
            ),
            _saved_prediction_row(
                run_id=run_id,
                sample_id="val_1",
                split="validation",
                true_label=1,
                pred_label=1,
                prob_1=0.8,
                group_id="group_b",
                is_id=False,
                is_ood=True,
            ),
        ]
    ).to_parquet(validation_path, index=False)
    pd.DataFrame(
        [
            _saved_prediction_row(
                run_id=run_id,
                sample_id="test_0",
                split="test",
                true_label=1,
                pred_label=0,
                prob_1=0.1,
                group_id="group_b",
                is_id=False,
                is_ood=True,
            )
        ]
    ).to_parquet(test_path, index=False)

    metadata_payload = {
        "run_id": run_id,
        "model_name": "logistic_tfidf",
        "dataset_name": "civilcomments",
        "split_details": {
            "train": "train",
            "validation": "validation",
            "id_test": "id_test",
            "ood_test": "ood_test",
        },
        "resolved_config": {
            "experiment_name": "civilcomments_logistic_baseline",
            "experiment_group": "baselines",
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
            "parent_run_id": None,
            "data": {
                "dataset_name": "civilcomments",
                "wilds_dataset_name": "civilcomments",
                "wilds_root_dir": "data/wilds",
                "split_scheme": "official",
                "text_field": "comment_text",
                "label_field": "toxicity",
                "group_fields": ["male", "female"],
                "auxiliary_fields": [],
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
                "validation": {"subgroup_min_samples_warning": 25, "preview_samples": 5},
            },
            "model": {"model_name": "logistic_tfidf"},
            "train": {"seed": 13},
            "eval": {
                "primary_metric": "macro_f1",
                "worst_group_metric": "accuracy",
                "robustness_gap_metric": "accuracy_delta",
                "calibration_metric": "ece",
                "prediction_filename": "predictions.parquet",
                "tracked_metrics": ["accuracy", "macro_f1", "auroc", "loss"],
                "min_group_support": 100,
                "calibration_bins": 10,
                "calibration_strategy": "uniform",
                "requested_splits": None,
                "output_tag": None,
            },
            "perturbation": None,
        },
        "artifact_paths": {
            "checkpoint": str(checkpoint_dir),
            "selected_checkpoint": str(checkpoint_dir / "logistic_model.joblib"),
            "predictions": {
                "validation": str(validation_path),
                "test": str(test_path),
            }
        },
    }
    write_metadata(run_dir, metadata_payload)
    return run_id


def _create_saved_report_evaluation_bundle(
    *,
    model_name: str,
    source_run_id: str,
    eval_id: str,
    experiment_group: str = "baselines_v1",
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
        from model_failure_lab.utils.paths import build_mitigation_run_dir

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
    prediction_records = {}
    for split_name, is_id, is_ood, accuracy_lookup in (
        ("id_test", True, False, id_group_accuracy),
        ("ood_test", False, True, ood_group_accuracy),
    ):
        sample_ids: list[str] = []
        splits: list[str] = []
        true_labels: list[int] = []
        predicted_labels: list[int] = []
        probability_rows: list[list[float]] = []
        group_ids: list[str] = []
        is_id_flags: list[bool] = []
        is_ood_flags: list[bool] = []
        for group_name, support in group_support.items():
            accuracy = float(accuracy_lookup[group_name])
            correct_count = int(round(support * accuracy))
            for index in range(support):
                true_label = index % 2
                predicted_label = true_label if index < correct_count else 1 - true_label
                confidence = 0.83 if predicted_label == true_label else 0.76
                prob_1 = confidence if predicted_label == 1 else 1.0 - confidence

                sample_ids.append(f"{split_name}_{group_name}_{index}")
                splits.append(split_name)
                true_labels.append(true_label)
                predicted_labels.append(predicted_label)
                probability_rows.append([1.0 - prob_1, prob_1])
                group_ids.append(group_name)
                is_id_flags.append(is_id)
                is_ood_flags.append(is_ood)

        prediction_records[split_name] = build_prediction_records(
            run_id=source_run_id,
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

    artifact_paths = {"predictions": {}}
    for split_name, records in prediction_records.items():
        output_path = build_prediction_artifact_path(source_run_dir, split_name)
        pd.DataFrame(records).to_parquet(output_path, index=False)
        artifact_paths["predictions"][split_name] = str(output_path)

    metadata_payload: dict[str, object] = {
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
    (source_run_dir / "metadata.json").write_text(json.dumps(metadata_payload), encoding="utf-8")

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


def test_run_logistic_baseline_writes_completed_artifacts(temp_artifact_root, monkeypatch):
    monkeypatch.setattr(
        "model_failure_lab.models.logistic_tfidf.load_baseline_canonical_dataset",
        lambda *_args, **_kwargs: _baseline_dataset(),
    )

    result = run_baseline_command(
        [
            "--model",
            "logistic_tfidf",
            "--run-id",
            "logistic_tfidf_baseline",
            "--experiment-group",
            "baselines_v1_1",
            "--tag",
            "v1.1_baseline",
        ]
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "artifacts/baselines/logistic_tfidf" in result.run_dir.as_posix()
    assert metadata["model_name"] == "logistic_tfidf"
    assert metadata["experiment_group"] == "baselines_v1_1"
    assert metadata["resolved_config"]["experiment_group"] == "baselines_v1_1"
    assert metadata["tags"] == ["baseline", "logistic_tfidf", "v1.1_baseline"]
    assert metadata["status"] == "completed"
    assert metadata["artifact_paths"]["predictions"]["train"].endswith(
        "predictions_train.parquet"
    )
    assert metadata["artifact_paths"]["predictions"]["validation"].endswith(
        "predictions_val.parquet"
    )
    assert metadata["artifact_paths"]["predictions"]["id_test"].endswith(
        "predictions_id_test.parquet"
    )
    assert metadata["artifact_paths"]["predictions"]["ood_test"].endswith(
        "predictions_ood_test.parquet"
    )
    assert result.metadata_path.name == "metadata.json"


def test_run_distilbert_baseline_writes_completed_artifacts(temp_artifact_root, monkeypatch):
    monkeypatch.setattr(
        "model_failure_lab.models.distilbert.load_baseline_canonical_dataset",
        lambda *_args, **_kwargs: _baseline_dataset(),
    )
    monkeypatch.setattr(
        "model_failure_lab.models.distilbert.build_tokenizer",
        lambda _name: _FakeTokenizer(),
    )
    monkeypatch.setattr(
        "model_failure_lab.models.distilbert.build_sequence_classifier",
        lambda _name, num_labels: _TinyClassifier(num_labels=num_labels),
    )

    result = run_baseline_command(
        [
            "--model",
            "distilbert",
            "--run-id",
            "distilbert_baseline",
            "--tier",
            "constrained",
            "--experiment-group",
            "baselines_v1_1",
            "--tag",
            "v1.1_baseline",
        ]
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "artifacts/baselines/distilbert" in result.run_dir.as_posix()
    assert metadata["model_name"] == "distilbert"
    assert metadata["experiment_group"] == "baselines_v1_1"
    assert metadata["execution_tier"] == "constrained"
    assert metadata["effective_batch_size"] == 8
    assert metadata["max_length"] == 128
    assert metadata["status"] == "completed"
    assert metadata["artifact_paths"]["predictions"]["train"].endswith(
        "predictions_train.parquet"
    )
    assert metadata["artifact_paths"]["predictions"]["validation"].endswith(
        "predictions_val.parquet"
    )
    assert metadata["artifact_paths"]["predictions"]["id_test"].endswith(
        "predictions_id_test.parquet"
    )
    assert metadata["artifact_paths"]["predictions"]["ood_test"].endswith(
        "predictions_ood_test.parquet"
    )
    assert result.metadata_path.name == "metadata.json"


def test_run_mitigation_reweighting_writes_completed_artifacts(
    temp_artifact_root,
    monkeypatch,
):
    parent_run_id = "distilbert_parent_runtime"
    _write_distilbert_parent_run(parent_run_id)

    monkeypatch.setattr(
        "model_failure_lab.mitigations.reweighting.load_baseline_canonical_dataset",
        lambda *_args, **_kwargs: _baseline_dataset(),
    )
    monkeypatch.setattr(
        "model_failure_lab.mitigations.reweighting.build_tokenizer",
        lambda _name: _FakeTokenizer(),
    )
    monkeypatch.setattr(
        "model_failure_lab.mitigations.reweighting.build_sequence_classifier",
        lambda _name, num_labels: _TinyClassifier(num_labels=num_labels),
    )

    result = run_mitigation_command(
        [
            "--run-id",
            parent_run_id,
            "--method",
            "reweighting",
            "--output-run-id",
            "reweighting_runtime",
        ]
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "artifacts/mitigations/reweighting" in result.run_dir.as_posix()
    assert metadata["status"] == "completed"
    assert metadata["parent_run_id"] == parent_run_id
    assert metadata["mitigation_method"] == "reweighting"
    assert metadata["artifact_paths"]["group_weights_csv"].endswith("group_weights.csv")
    assert Path(metadata["artifact_paths"]["group_weights_csv"]).exists()
    assert metadata["artifact_paths"]["predictions"]["train"].endswith(
        "predictions_train.parquet"
    )
    assert metadata["artifact_paths"]["predictions"]["validation"].endswith(
        "predictions_val.parquet"
    )
    assert metadata["artifact_paths"]["predictions"]["id_test"].endswith(
        "predictions_id_test.parquet"
    )
    assert metadata["artifact_paths"]["predictions"]["ood_test"].endswith(
        "predictions_ood_test.parquet"
    )


def test_run_mitigation_reweighting_supports_official_seeded_metadata(
    temp_artifact_root,
    monkeypatch,
):
    parent_run_id = "distilbert_parent_reweighting_seeded"
    _write_distilbert_parent_run(
        parent_run_id,
        constrained=True,
        tags=["baseline", "distilbert", "v1.2_baseline", "official", "seed_13"],
    )

    monkeypatch.setattr(
        "model_failure_lab.mitigations.reweighting.load_baseline_canonical_dataset",
        lambda *_args, **_kwargs: _baseline_dataset(),
    )
    monkeypatch.setattr(
        "model_failure_lab.mitigations.reweighting.build_tokenizer",
        lambda _name: _FakeTokenizer(),
    )
    monkeypatch.setattr(
        "model_failure_lab.mitigations.reweighting.build_sequence_classifier",
        lambda _name, num_labels: _TinyClassifier(num_labels=num_labels),
    )

    result = run_mitigation_command(
        [
            "--run-id",
            parent_run_id,
            "--method",
            "reweighting",
            "--seed",
            "13",
            "--experiment-group",
            "reweighting_v1_2",
            "--tag",
            "mitigation",
            "--tag",
            "reweighting",
            "--tag",
            "v1.2_mitigation",
            "--tag",
            "official",
            "--tag",
            "seed_13",
            "--tag",
            f"parent_{parent_run_id}",
            "--output-run-id",
            "reweighting_seeded_runtime",
        ]
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert metadata["experiment_group"] == "reweighting_v1_2"
    assert metadata["resolved_config"]["experiment_group"] == "reweighting_v1_2"
    assert metadata["parent_run_id"] == parent_run_id
    assert metadata["resolved_config"]["parent_run_id"] == parent_run_id
    assert metadata["resolved_config"]["parent_model_name"] == "distilbert"
    assert metadata["resolved_config"]["seed"] == 13
    assert metadata["resolved_config"]["model"]["execution_tier"] == "constrained"
    assert metadata["resolved_config"]["train"]["batch_size"] == 8
    assert metadata["resolved_config"]["train"]["eval_batch_size"] == 16
    assert metadata["resolved_config"]["train"]["max_epochs"] == 2
    assert metadata["resolved_config"]["train"]["num_workers"] == 0
    assert "baseline" not in metadata["tags"]
    assert "v1.2_baseline" not in metadata["tags"]
    assert set(metadata["tags"]) >= {
        "distilbert",
        "mitigation",
        "reweighting",
        "v1.2_mitigation",
        "official",
        "seed_13",
        f"parent_{parent_run_id}",
    }


def test_run_mitigation_temperature_scaling_writes_completed_artifacts(temp_artifact_root):
    parent_run_id = "distilbert_parent_temperature"
    _write_distilbert_parent_run(parent_run_id, with_saved_logits=True)

    result = run_mitigation_command(
        [
            "--run-id",
            parent_run_id,
            "--method",
            "temperature_scaling",
            "--output-run-id",
            "temperature_scaling_runtime",
        ]
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "artifacts/mitigations/temperature_scaling" in result.run_dir.as_posix()
    assert metadata["status"] == "completed"
    assert metadata["parent_run_id"] == parent_run_id
    assert metadata["mitigation_method"] == "temperature_scaling"
    assert metadata["learned_temperature"] > 0.0
    assert metadata["artifact_paths"]["temperature_scaler_json"].endswith(
        "temperature_scaler.json"
    )
    assert Path(metadata["artifact_paths"]["temperature_scaler_json"]).exists()
    assert metadata["artifact_paths"]["predictions"]["train"].endswith(
        "predictions_train.parquet"
    )
    assert metadata["artifact_paths"]["predictions"]["validation"].endswith(
        "predictions_val.parquet"
    )
    assert metadata["artifact_paths"]["predictions"]["id_test"].endswith(
        "predictions_id_test.parquet"
    )
    assert metadata["artifact_paths"]["predictions"]["ood_test"].endswith(
        "predictions_ood_test.parquet"
    )


def test_run_mitigation_temperature_scaling_supports_official_seeded_metadata(
    temp_artifact_root,
):
    parent_run_id = "distilbert_parent_temperature_seeded"
    _write_distilbert_parent_run(parent_run_id, with_saved_logits=True)

    result = run_mitigation_command(
        [
            "--run-id",
            parent_run_id,
            "--method",
            "temperature_scaling",
            "--seed",
            "13",
            "--experiment-group",
            "temperature_scaling_v1_2",
            "--tag",
            "mitigation",
            "--tag",
            "temperature_scaling",
            "--tag",
            "v1.2_mitigation",
            "--tag",
            "official",
            "--tag",
            "seed_13",
            "--tag",
            f"parent_{parent_run_id}",
            "--output-run-id",
            "temperature_scaling_seeded_runtime",
        ]
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert metadata["experiment_group"] == "temperature_scaling_v1_2"
    assert metadata["resolved_config"]["experiment_group"] == "temperature_scaling_v1_2"
    assert metadata["parent_run_id"] == parent_run_id
    assert metadata["resolved_config"]["parent_run_id"] == parent_run_id
    assert metadata["resolved_config"]["parent_model_name"] == "distilbert"
    assert metadata["resolved_config"]["seed"] == 13
    assert "baseline" not in metadata["tags"]
    assert "v1.2_baseline" not in metadata["tags"]
    assert set(metadata["tags"]) >= {
        "distilbert",
        "mitigation",
        "temperature_scaling",
        "v1.2_mitigation",
        "official",
        "seed_13",
        f"parent_{parent_run_id}",
    }


def test_run_perturbation_eval_materializes_suite_bundle(temp_artifact_root, monkeypatch):
    source_run_id = _create_saved_evaluation_source_run()
    monkeypatch.setattr(
        "scripts.run_perturbation_eval.prepare_civilcomments_runtime_dataset",
        lambda *_args, **_kwargs: _baseline_dataset(),
    )

    result = run_perturbation_eval_command(
        [
            "--run-id",
            source_run_id,
            "--output-run-id",
            "perturbation_suite",
            "--max-source-samples",
            "2",
        ]
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "artifacts/baselines/logistic_tfidf/shift_eval_source/perturbations" in (
        result.run_dir.as_posix()
    )
    assert metadata["experiment_type"] == "perturbation_eval"
    assert metadata["status"] == "completed"
    assert metadata["source_run_id"] == source_run_id
    assert metadata["selected_source_count"] == 2
    assert metadata["perturbed_sample_count"] == 18
    assert metadata["artifact_paths"]["suite_manifest_json"].endswith("suite_manifest.json")
    assert Path(metadata["artifact_paths"]["perturbed_samples_jsonl"]).exists()
    assert Path(metadata["artifact_paths"]["sample_preview_jsonl"]).exists()
    assert Path(metadata["artifact_paths"]["predictions_perturbed_parquet"]).exists()
    assert Path(metadata["artifact_paths"]["suite_summary_csv"]).exists()
    assert Path(metadata["artifact_paths"]["family_summary_csv"]).exists()
    assert result.metrics_path.name == "suite_summary.csv"


def test_shift_eval_writes_completed_evaluation_bundle(temp_artifact_root):
    source_run_id = _create_saved_evaluation_source_run()
    result = run_shift_eval_command(
        [
            "--run-id",
            source_run_id,
            "--splits",
            "val,test",
            "--min-group-support",
            "1",
            "--calibration-bins",
            "5",
            "--output-tag",
            "debug",
        ]
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "/evaluations/" in result.run_dir.as_posix()
    assert metadata["experiment_type"] == "shift_eval"
    assert metadata["status"] == "completed"
    assert metadata["source_run_id"] == source_run_id
    assert metadata["experiment_group"] == "baselines"
    assert metadata["resolved_config"]["experiment_group"] == "baselines"
    assert metadata["evaluation_schema_version"] == "shift_eval_v1"
    assert metadata["output_tag"] == "debug"
    assert result.metrics_path.name == "overall_metrics.json"


def test_build_report_writes_completed_report_package(temp_artifact_root):
    _create_saved_report_evaluation_bundle(
        model_name="distilbert",
        source_run_id="baseline_b",
        eval_id="eval_b",
    )
    _create_saved_report_evaluation_bundle(
        model_name="logistic_tfidf",
        source_run_id="baseline_a",
        eval_id="eval_a",
    )

    result = run_build_report_command(
        [
            "--experiment-group",
            "baselines_v1",
            "--report-name",
            "baseline_report",
            "--top-k-subgroups",
            "2",
            "--min-group-support",
            "100",
        ]
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "artifacts/reports/comparisons/baselines_v1" in result.run_dir.as_posix()
    assert metadata["experiment_type"] == "report"
    assert metadata["status"] == "completed"
    assert metadata["selection_mode"] == "experiment_group"
    assert metadata["source_eval_ids"] == ["eval_b", "eval_a"]
    assert (result.run_dir / "report.md").exists()
    assert (result.run_dir / "figures" / "id_vs_ood_primary_metric.png").exists()
    assert result.metrics_path.name == "report_summary.json"
    assert result.metadata_path.exists()


def test_build_report_writes_mitigation_comparison_table(temp_artifact_root):
    _create_saved_report_evaluation_bundle(
        model_name="distilbert",
        source_run_id="baseline_parent",
        eval_id="eval_parent",
        experiment_group="mitigation_suite",
    )
    _create_saved_report_evaluation_bundle(
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

    result = run_build_report_command(
        [
            "--experiment-group",
            "mitigation_suite",
            "--report-name",
            "mitigation_report",
            "--top-k-subgroups",
            "2",
            "--min-group-support",
            "100",
        ]
    )

    mitigation_table_path = result.run_dir / "tables" / "mitigation_comparison_table.csv"
    markdown = (result.run_dir / "report.md").read_text(encoding="utf-8")

    assert mitigation_table_path.exists()
    assert "tradeoff" not in markdown
    assert "verdict win" in markdown


def test_build_perturbation_report_writes_completed_report_package(temp_artifact_root, monkeypatch):
    source_run_id = _create_saved_evaluation_source_run()
    monkeypatch.setattr(
        "scripts.run_perturbation_eval.prepare_civilcomments_runtime_dataset",
        lambda *_args, **_kwargs: _baseline_dataset(),
    )
    run_perturbation_eval_command(
        [
            "--run-id",
            source_run_id,
            "--output-run-id",
            "perturbation_suite",
            "--max-source-samples",
            "2",
        ]
    )

    result = run_build_perturbation_report_command(
        [
            "--experiment-group",
            "baselines",
            "--report-name",
            "synthetic_stress_report",
        ]
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "artifacts/reports/perturbations/baselines" in result.run_dir.as_posix()
    assert metadata["experiment_type"] == "perturbation_report"
    assert metadata["status"] == "completed"
    assert metadata["selection_mode"] == "experiment_group"
    assert (result.run_dir / "report.md").exists()
    assert (result.run_dir / "figures" / "clean_vs_perturbed_primary_metric.png").exists()
    assert (result.run_dir / "tables" / "suite_summary.csv").exists()
    assert result.metrics_path.name == "report_summary.json"


def test_download_data_bootstrap_writes_metadata(temp_artifact_root):
    result = run_download_data_command([], materialize_fn=_fake_materialize)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "artifacts/data/runs" in result.run_dir.as_posix()
    assert metadata["experiment_type"] == "data_download"
    assert metadata["status"] == "materialized"
    assert metadata["artifact_paths"]["manifest_json"].endswith("civilcomments_manifest.json")
    assert result.metadata_path.exists()


def test_direct_script_help_runs_without_manual_pythonpath():
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)

    commands = [
        [sys.executable, "scripts/check_environment.py", "--help"],
        [sys.executable, "scripts/download_data.py", "--help"],
        [sys.executable, "scripts/run_baseline.py", "--help"],
        [sys.executable, "scripts/build_report.py", "--help"],
    ]
    for command in commands:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "usage:" in result.stdout.lower()


def test_check_environment_command_supports_json_output(tmp_path):
    payload = run_check_environment_command(
        ["--json"],
        dependency_checker=lambda package: {
            "package": package,
            "available": True,
            "version": "1.0",
            "error": None,
        },
        matplotlib_dir_resolver=lambda: tmp_path / "mplconfig",
        config_loader=lambda _preset: {
            "model": {"pretrained_name": "distilbert-base-uncased"},
        },
        transformer_asset_checker=lambda pretrained_name: {
            "pretrained_name": pretrained_name,
            "local_cache_available": False,
            "message": (
                "Local cache not detected. The first DistilBERT run will require "
                "network access or a pre-populated local cache."
            ),
        },
    )

    assert payload["overall_ok"] is True
    assert payload["distilbert"]["pretrained_name"] == "distilbert-base-uncased"
