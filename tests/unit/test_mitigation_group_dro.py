from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import torch
from torch import nn

from model_failure_lab.config.loader import _load_yaml_file, load_experiment_config
from model_failure_lab.data import CanonicalDataset, CanonicalSample
from model_failure_lab.mitigations import (
    build_inherited_mitigation_config,
    load_parent_run_context,
    train_distilbert_group_dro,
)
from model_failure_lab.models.export import REQUIRED_PREDICTION_COLUMNS
from model_failure_lab.runners.contracts import DispatchResult
from model_failure_lab.tracking import build_run_metadata, write_metadata
from model_failure_lab.utils.paths import (
    build_baseline_run_dir,
    build_mitigation_run_dir,
    config_root,
)
from scripts.run_mitigation import run_command as run_mitigation_command


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


def _canonical_dataset(*, include_unseen_eval_group: bool = False) -> CanonicalDataset:
    eval_group_id = "group_eval_only" if include_unseen_eval_group else "group_b"
    return CanonicalDataset(
        dataset_name="civilcomments",
        samples=[
            _sample(
                sample_id="train_0",
                text="negative calm steady",
                label=0,
                split="train",
                group_id="group_a",
            ),
            _sample(
                sample_id="train_1",
                text="negative calm quiet",
                label=0,
                split="train",
                group_id="group_a",
            ),
            _sample(
                sample_id="train_2",
                text="negative calm safe",
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
                text="negative calm validation_only",
                label=0,
                split="validation",
                group_id="group_a",
            ),
            _sample(
                sample_id="val_1",
                text="positive toxic validation_only",
                label=1,
                split="validation",
                group_id=eval_group_id,
            ),
            _sample(
                sample_id="id_test_0",
                text="negative calm blind_id",
                label=0,
                split="id_test",
                group_id="group_a",
            ),
            _sample(
                sample_id="id_test_1",
                text="positive toxic blind_id",
                label=1,
                split="id_test",
                group_id=eval_group_id,
            ),
            _sample(
                sample_id="ood_test_0",
                text="negative calm blind_ood",
                label=0,
                split="ood_test",
                group_id="group_a",
            ),
            _sample(
                sample_id="ood_test_1",
                text="positive toxic blind_ood",
                label=1,
                split="ood_test",
                group_id=eval_group_id,
            ),
        ],
    )


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
        loss = None if labels is None else self.loss_fn(logits, labels)
        return type("Output", (), {"loss": loss, "logits": logits})


def _write_parent_metadata(
    *,
    run_id: str,
    constrained: bool = False,
    tags: list[str] | None = None,
) -> str:
    resolved_config = load_experiment_config(
        "configs/experiments/civilcomments_distilbert_baseline.yaml"
    )
    resolved_config["run_id"] = run_id
    if constrained:
        resolved_config["model"] = _load_yaml_file(
            config_root() / "model" / "distilbert_constrained.yaml"
        )
        resolved_config["train"] = _load_yaml_file(
            config_root() / "train" / "distilbert_constrained.yaml"
        )

    run_dir = build_baseline_run_dir("distilbert", run_id, create=True)
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
        notes="parent fixture",
        tags=tags or ["baseline", "distilbert"],
        status="completed",
    )
    write_metadata(run_dir, metadata_payload)
    return run_id


def test_group_dro_preset_contains_mitigation_payload():
    config = load_experiment_config(
        "configs/experiments/civilcomments_distilbert_group_dro.yaml"
    )

    assert config["mitigation"]["method"] == "group_dro"
    assert config["mitigation"]["parent_model_name"] == "distilbert"
    assert config["mitigation"]["group_dro"]["grouping_field"] == "group_id"
    assert config["mitigation"]["group_dro"]["adversary_step_size"] == 0.1
    assert config["mitigation"]["group_dro"]["loss_ema"] == 0.2
    assert (
        config["mitigation"]["comparison_tolerances"]["ece_neutral_tolerance"] == 0.005
    )


def test_build_inherited_group_dro_config_preserves_constrained_parent_runtime_and_scout_tags(
    temp_artifact_root,
):
    parent_run_id = _write_parent_metadata(
        run_id="distilbert_parent_group_dro_constrained",
        constrained=True,
        tags=["baseline", "distilbert", "v1.2_baseline", "official", "seed_13"],
    )
    parent_context = load_parent_run_context(parent_run_id)
    mitigation_preset = load_experiment_config(
        "configs/experiments/civilcomments_distilbert_group_dro.yaml"
    )
    mitigation_preset["run_id"] = "group_dro_child_seeded"
    mitigation_preset["experiment_group"] = "group_dro_v1_3"
    mitigation_preset["seed"] = 13
    mitigation_preset["tags"] = [
        "mitigation",
        "group_dro",
        "v1.3_mitigation",
        "scout",
        "seed_13",
        f"parent_{parent_run_id}",
    ]

    child_config = build_inherited_mitigation_config(parent_context, mitigation_preset)

    assert child_config["experiment_group"] == "group_dro_v1_3"
    assert child_config["parent_run_id"] == parent_run_id
    assert child_config["mitigation_method"] == "group_dro"
    assert child_config["seed"] == 13
    assert child_config["model"] == parent_context["resolved_config"]["model"]
    assert child_config["train"] == parent_context["resolved_config"]["train"]
    assert child_config["model"]["execution_tier"] == "constrained"
    assert child_config["train"]["batch_size"] == 8
    assert child_config["train"]["eval_batch_size"] == 16
    assert child_config["train"]["max_epochs"] == 2
    assert child_config["train"]["num_workers"] == 0
    assert "baseline" not in child_config["tags"]
    assert "v1.2_baseline" not in child_config["tags"]
    assert "official" not in child_config["tags"]
    assert set(child_config["tags"]) >= {
        "distilbert",
        "mitigation",
        "group_dro",
        "v1.3_mitigation",
        "scout",
        "seed_13",
        f"parent_{parent_run_id}",
    }


def test_train_distilbert_group_dro_writes_group_state_and_predictions(temp_artifact_root):
    config = load_experiment_config("configs/experiments/civilcomments_distilbert_group_dro.yaml")
    config["run_id"] = "distilbert_group_dro_test"
    config["parent_run_id"] = "distilbert_parent"
    config["parent_model_name"] = "distilbert"
    config["mitigation_method"] = "group_dro"
    run_dir = build_mitigation_run_dir(
        "group_dro",
        config["model_name"],
        config["run_id"],
        create=True,
    )

    artifacts = train_distilbert_group_dro(
        config,
        run_dir,
        dataset_loader=lambda *_args, **_kwargs: _canonical_dataset(),
        tokenizer_factory=lambda _name: FakeTokenizer(),
        model_factory=lambda _name, num_labels: TinyClassifier(num_labels=num_labels),
    )

    assert artifacts.group_dro_weights_path.exists()
    assert artifacts.checkpoint_path.exists()
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
    assert artifacts.metrics_payload["group_dro"]["group_count"] == 2


def test_train_distilbert_group_dro_tolerates_unseen_eval_groups(temp_artifact_root):
    config = load_experiment_config("configs/experiments/civilcomments_distilbert_group_dro.yaml")
    config["run_id"] = "distilbert_group_dro_unseen_eval_group"
    config["parent_run_id"] = "distilbert_parent"
    config["parent_model_name"] = "distilbert"
    config["mitigation_method"] = "group_dro"
    run_dir = build_mitigation_run_dir(
        "group_dro",
        config["model_name"],
        config["run_id"],
        create=True,
    )

    artifacts = train_distilbert_group_dro(
        config,
        run_dir,
        dataset_loader=lambda *_args, **_kwargs: _canonical_dataset(
            include_unseen_eval_group=True
        ),
        tokenizer_factory=lambda _name: FakeTokenizer(),
        model_factory=lambda _name, num_labels: TinyClassifier(num_labels=num_labels),
    )

    validation_frame = pd.read_parquet(artifacts.prediction_paths["validation"])
    id_test_frame = pd.read_parquet(artifacts.prediction_paths["id_test"])
    ood_test_frame = pd.read_parquet(artifacts.prediction_paths["ood_test"])

    assert "group_eval_only" in set(validation_frame["group_id"])
    assert "group_eval_only" in set(id_test_frame["group_id"])
    assert "group_eval_only" in set(ood_test_frame["group_id"])
    assert artifacts.metrics_payload["group_dro"]["group_count"] == 2


def test_run_mitigation_group_dro_uses_inherited_parent_config(
    temp_artifact_root,
    monkeypatch,
):
    parent_run_id = _write_parent_metadata(run_id="distilbert_parent_group_dro_runtime")
    captured: dict[str, object] = {}

    def fake_dispatch(**kwargs):
        captured.update(kwargs)
        return DispatchResult(
            status="scaffold_ready",
            message="stubbed group_dro dispatch",
            run_dir=kwargs["run_dir"],
            metadata_path=kwargs["metadata_path"],
            metrics_path=kwargs["metrics_path"],
            preset_name=kwargs["preset_name"],
        )

    monkeypatch.setattr("scripts.run_mitigation.dispatch_mitigation", fake_dispatch)

    result = run_mitigation_command(
        [
            "--run-id",
            parent_run_id,
            "--method",
            "group_dro",
            "--seed",
            "13",
            "--experiment-group",
            "group_dro_v1_3",
            "--tag",
            "mitigation",
            "--tag",
            "group_dro",
            "--tag",
            "v1.3_mitigation",
            "--tag",
            "scout",
            "--tag",
            "seed_13",
            "--tag",
            f"parent_{parent_run_id}",
            "--output-run-id",
            "group_dro_child_runtime",
        ]
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    dispatched_config = captured["config"]

    assert result.run_dir.as_posix().endswith(
        "artifacts/mitigations/group_dro/distilbert/group_dro_child_runtime"
    )
    assert dispatched_config["parent_run_id"] == parent_run_id
    assert dispatched_config["parent_model_name"] == "distilbert"
    assert dispatched_config["mitigation_method"] == "group_dro"
    assert dispatched_config["mitigation_config"]["group_dro"]["grouping_field"] == "group_id"
    assert dispatched_config["preset_path"].endswith("civilcomments_distilbert_baseline.yaml")
    assert metadata["resolved_config"]["mitigation_method"] == "group_dro"
    assert metadata["resolved_config"]["parent_model_name"] == "distilbert"
    assert metadata["parent_run_id"] == parent_run_id
    assert "official" not in metadata["tags"]
    assert set(metadata["tags"]) >= {
        "distilbert",
        "mitigation",
        "group_dro",
        "v1.3_mitigation",
        "scout",
        "seed_13",
        f"parent_{parent_run_id}",
    }
