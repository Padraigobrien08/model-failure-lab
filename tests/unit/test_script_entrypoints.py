from __future__ import annotations

import json
from dataclasses import dataclass

import pytest
import torch
from torch import nn

from model_failure_lab.data import CanonicalDataset, CanonicalSample
from scripts.build_report import run_command as run_build_report_command
from scripts.download_data import run_command as run_download_data_command
from scripts.run_baseline import run_command as run_baseline_command
from scripts.run_mitigation import run_command as run_mitigation_command
from scripts.run_shift_eval import run_command as run_shift_eval_command


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
        ],
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


def test_run_logistic_baseline_writes_completed_artifacts(temp_artifact_root, monkeypatch):
    monkeypatch.setattr(
        "model_failure_lab.models.logistic_tfidf.load_baseline_canonical_dataset",
        lambda *_args, **_kwargs: _baseline_dataset(),
    )

    result = run_baseline_command(
        ["--model", "logistic_tfidf", "--run-id", "logistic_tfidf_baseline"]
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "artifacts/baselines/logistic_tfidf" in result.run_dir.as_posix()
    assert metadata["model_name"] == "logistic_tfidf"
    assert metadata["status"] == "completed"
    assert metadata["artifact_paths"]["predictions"]["train"].endswith(
        "predictions_train.parquet"
    )
    assert metadata["artifact_paths"]["predictions"]["validation"].endswith(
        "predictions_val.parquet"
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

    result = run_baseline_command(["--model", "distilbert", "--run-id", "distilbert_baseline"])
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "artifacts/baselines/distilbert" in result.run_dir.as_posix()
    assert metadata["model_name"] == "distilbert"
    assert metadata["status"] == "completed"
    assert metadata["artifact_paths"]["predictions"]["train"].endswith(
        "predictions_train.parquet"
    )
    assert metadata["artifact_paths"]["predictions"]["validation"].endswith(
        "predictions_val.parquet"
    )
    assert result.metadata_path.name == "metadata.json"


@pytest.mark.parametrize(
    ("method_name", "expected_segment"),
    [
        ("reweighting", "artifacts/mitigations/reweighting"),
        ("calibration", "artifacts/mitigations/calibration"),
    ],
)
def test_run_mitigation_bootstrap_uses_separate_root(
    temp_artifact_root,
    method_name,
    expected_segment,
):
    result = run_mitigation_command(
        ["--run-id", "baseline_parent_001", "--method", method_name, "--output-run-id", method_name]
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert expected_segment in result.run_dir.as_posix()
    assert metadata["parent_run_id"] == "baseline_parent_001"
    assert metadata["status"] == "scaffold_ready"
    assert "artifacts/baselines" not in result.run_dir.as_posix()


def test_shift_eval_bootstrap_writes_metadata(temp_artifact_root):
    result = run_shift_eval_command(["--run-id", "baseline_parent_002"])
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "artifacts/reports/comparisons/baseline_parent_002" in result.run_dir.as_posix()
    assert metadata["experiment_type"] == "shift_eval"
    assert metadata["parent_run_id"] == "baseline_parent_002"


def test_build_report_bootstrap_writes_metadata(temp_artifact_root):
    result = run_build_report_command(["--experiment-group", "mvp_summary"])
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "artifacts/reports/comparisons/mvp_summary" in result.run_dir.as_posix()
    assert metadata["experiment_type"] == "report"
    assert result.metadata_path.exists()


def test_download_data_bootstrap_writes_metadata(temp_artifact_root):
    result = run_download_data_command([], materialize_fn=_fake_materialize)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "artifacts/data/runs" in result.run_dir.as_posix()
    assert metadata["experiment_type"] == "data_download"
    assert metadata["status"] == "materialized"
    assert metadata["artifact_paths"]["manifest_json"].endswith("civilcomments_manifest.json")
    assert result.metadata_path.exists()
