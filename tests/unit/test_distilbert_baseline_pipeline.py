from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import torch
from torch import nn

from model_failure_lab.config.loader import load_experiment_config
from model_failure_lab.data import CanonicalDataset, CanonicalSample
from model_failure_lab.models.distilbert import train_distilbert_baseline
from model_failure_lab.models.export import REQUIRED_PREDICTION_COLUMNS
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
            text="negative safe calm",
            label=0,
            split="train",
            group_id="group_a",
        ),
        _sample(
            sample_id="train_1",
            text="negative quiet calm",
            label=0,
            split="train",
            group_id="group_a",
        ),
        _sample(
            sample_id="train_2",
            text="negative steady calm",
            label=0,
            split="train",
            group_id="group_a",
        ),
        _sample(
            sample_id="train_3",
            text="positive toxic loud",
            label=1,
            split="train",
            group_id="group_b",
        ),
        _sample(
            sample_id="train_4",
            text="positive toxic sharp",
            label=1,
            split="train",
            group_id="group_b",
        ),
        _sample(
            sample_id="train_5",
            text="positive toxic blunt",
            label=1,
            split="train",
            group_id="group_b",
        ),
        _sample(
            sample_id="val_0",
            text="negative calm quiet",
            label=0,
            split="validation",
            group_id="group_a",
        ),
        _sample(
            sample_id="val_1",
            text="positive toxic loud",
            label=1,
            split="validation",
            group_id="group_b",
        ),
        _sample(
            sample_id="id_test_0",
            text="negative calm blind id",
            label=0,
            split="id_test",
            group_id="group_a",
        ),
        _sample(
            sample_id="id_test_1",
            text="positive toxic blind id",
            label=1,
            split="id_test",
            group_id="group_b",
        ),
        _sample(
            sample_id="ood_test_0",
            text="negative calm blind ood",
            label=0,
            split="ood_test",
            group_id="group_a",
        ),
        _sample(
            sample_id="ood_test_1",
            text="positive toxic blind ood",
            label=1,
            split="ood_test",
            group_id="group_b",
        ),
    ]
    return CanonicalDataset(dataset_name="civilcomments", samples=samples)


class FakeTokenizer:
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
        return {
            "input_ids": token_ids,
            "attention_mask": [1] * len(token_ids),
        }

    def save_pretrained(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        (path / "tokenizer.json").write_text("{}", encoding="utf-8")


class TinyClassifier(nn.Module):
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
        if labels is None:
            loss = None
        else:
            loss = self.loss_fn(logits, labels)
        return type("Output", (), {"loss": loss, "logits": logits})


def test_train_distilbert_baseline_writes_checkpoint_and_history(temp_artifact_root):
    config = load_experiment_config("configs/experiments/civilcomments_distilbert_baseline.yaml")
    config["run_id"] = "distilbert_artifacts_test"
    run_dir = build_baseline_run_dir(config["model_name"], config["run_id"], create=True)

    artifacts = train_distilbert_baseline(
        config,
        run_dir,
        dataset_loader=lambda *_args, **_kwargs: _canonical_dataset(),
        tokenizer_factory=lambda _name: FakeTokenizer(),
        model_factory=lambda _name, num_labels: TinyClassifier(num_labels=num_labels),
    )

    assert artifacts.checkpoint_path.exists()
    assert artifacts.history_path.exists()
    assert artifacts.tokenizer_config_path.exists()
    assert artifacts.prediction_paths["train"].exists()
    assert artifacts.prediction_paths["validation"].exists()
    assert artifacts.prediction_paths["id_test"].exists()
    assert artifacts.prediction_paths["ood_test"].exists()
    id_test_frame = pd.read_parquet(artifacts.prediction_paths["id_test"])
    ood_test_frame = pd.read_parquet(artifacts.prediction_paths["ood_test"])
    assert (
        list(id_test_frame.columns[: len(REQUIRED_PREDICTION_COLUMNS)])
        == REQUIRED_PREDICTION_COLUMNS
    )
    assert (
        list(ood_test_frame.columns[: len(REQUIRED_PREDICTION_COLUMNS)])
        == REQUIRED_PREDICTION_COLUMNS
    )
    assert set(id_test_frame["split"]) == {"id_test"}
    assert set(ood_test_frame["split"]) == {"ood_test"}
    assert artifacts.metrics_payload["primary_metric"]["name"] == "macro_f1"
    assert (
        artifacts.metrics_payload["selected_checkpoint"]["source"]
        == "best_validation_checkpoint"
    )


def test_run_baseline_command_executes_real_distilbert_path(temp_artifact_root, monkeypatch):
    dataset = _canonical_dataset()
    monkeypatch.setattr(
        "model_failure_lab.models.distilbert.load_baseline_canonical_dataset",
        lambda *_args, **_kwargs: dataset,
    )
    monkeypatch.setattr(
        "model_failure_lab.models.distilbert.build_tokenizer",
        lambda _name: FakeTokenizer(),
    )
    monkeypatch.setattr(
        "model_failure_lab.models.distilbert.build_sequence_classifier",
        lambda _name, num_labels: TinyClassifier(num_labels=num_labels),
    )

    result = run_baseline_command(
        [
            "--model",
            "distilbert",
            "--run-id",
            "distilbert_command_test",
            "--tier",
            "constrained",
            "--experiment-group",
            "baselines_v1_1",
            "--tag",
            "v1.1_baseline",
        ]
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    metrics = json.loads(result.metrics_path.read_text(encoding="utf-8"))

    assert result.status == "completed"
    assert metadata["status"] == "completed"
    assert metadata["experiment_group"] == "baselines_v1_1"
    assert metadata["resolved_config"]["experiment_group"] == "baselines_v1_1"
    assert metadata["resolved_config"]["model"]["execution_tier"] == "constrained"
    assert metadata["execution_tier"] == "constrained"
    assert metadata["effective_batch_size"] == 8
    assert metadata["max_length"] == 128
    assert metadata["hardware"]["device_type"] in {"cpu", "cuda", "mps"}
    assert metadata["tags"] == ["baseline", "distilbert", "constrained", "v1.1_baseline"]
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
    assert metrics["primary_metric"]["value"] is not None
    assert Path(metadata["artifact_paths"]["predictions"]["id_test"]).exists()
    assert Path(metadata["artifact_paths"]["predictions"]["ood_test"]).exists()
    assert (result.run_dir / "checkpoint" / "best_model.pt").exists()
    assert (result.run_dir / "checkpoint" / "training_history.json").exists()
