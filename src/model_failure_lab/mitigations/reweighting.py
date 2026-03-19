"""DistilBERT group reweighting mitigation built on the baseline training contract."""

from __future__ import annotations

import copy
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import torch
import torch.nn.functional as F
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from transformers import get_linear_schedule_with_warmup

from model_failure_lab.data import CanonicalDataset, prepare_transformer_adapter
from model_failure_lab.models.common import load_baseline_canonical_dataset, set_random_seed
from model_failure_lab.models.distilbert import (
    _checkpoint_paths,
    _device_and_precision,
    _run_validation,
    build_sequence_classifier,
    build_tokenizer,
)
from model_failure_lab.models.export import build_prediction_records, write_prediction_exports

DatasetLoader = Callable[..., CanonicalDataset]
TokenizerFactory = Callable[[str], Any]
ModelFactory = Callable[[str, int], torch.nn.Module]


@dataclass(slots=True)
class DistilBertReweightingArtifacts:
    """Artifacts produced by a completed DistilBERT reweighting run."""

    metrics_payload: dict[str, Any]
    prediction_paths: dict[str, Path]
    checkpoint_dir: Path
    checkpoint_path: Path
    history_path: Path
    tokenizer_config_path: Path
    group_weights_path: Path


class WeightedTokenizedTextDataset(Dataset):
    """Tokenizer-backed dataset that carries sample weights for training."""

    def __init__(
        self,
        records: list[dict[str, Any]],
        tokenizer: Any,
        *,
        max_length: int,
        sample_weights: list[float] | None = None,
    ) -> None:
        self.records = records
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.sample_weights = sample_weights

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> dict[str, Any]:
        record = self.records[index]
        encoded = self.tokenizer(
            record["text"],
            truncation=True,
            max_length=self.max_length,
            padding=False,
        )
        payload = {
            "input_ids": list(encoded["input_ids"]),
            "attention_mask": list(encoded["attention_mask"]),
            "labels": int(record["label"]),
            "sample_id": str(record["sample_id"]),
            "split": str(record["split"]),
            "group_id": str(record["group_id"]),
            "is_id": bool(
                record["group_attributes"].get("is_id", record["split"] in {"train", "id_test"})
            ),
            "is_ood": bool(
                record["group_attributes"].get(
                    "is_ood",
                    record["split"] in {"validation", "ood_test"},
                )
            ),
        }
        if self.sample_weights is not None:
            payload["sample_weight"] = float(self.sample_weights[index])
        return payload


def _pad_sequences(sequences: list[list[int]], pad_token_id: int) -> torch.Tensor:
    max_length = max(len(sequence) for sequence in sequences)
    padded = [sequence + [pad_token_id] * (max_length - len(sequence)) for sequence in sequences]
    return torch.tensor(padded, dtype=torch.long)


def _build_collate_fn(pad_token_id: int, *, include_sample_weight: bool):
    def collate_fn(examples: list[dict[str, Any]]) -> dict[str, Any]:
        batch = {
            "input_ids": _pad_sequences(
                [example["input_ids"] for example in examples],
                pad_token_id,
            ),
            "attention_mask": _pad_sequences(
                [example["attention_mask"] for example in examples],
                0,
            ),
            "labels": torch.tensor(
                [example["labels"] for example in examples],
                dtype=torch.long,
            ),
            "sample_id": [example["sample_id"] for example in examples],
            "split": [example["split"] for example in examples],
            "group_id": [example["group_id"] for example in examples],
            "is_id": [example["is_id"] for example in examples],
            "is_ood": [example["is_ood"] for example in examples],
        }
        if include_sample_weight:
            batch["sample_weight"] = torch.tensor(
                [float(example["sample_weight"]) for example in examples],
                dtype=torch.float32,
            )
        return batch

    return collate_fn


def build_group_weight_table(
    train_records: list[dict[str, Any]],
    *,
    grouping_field: str = "group_id",
    strategy: str = "inverse_sqrt_frequency",
    max_weight: float = 5.0,
    normalize_mean: float = 1.0,
) -> pd.DataFrame:
    """Build the saved group-weight table for a mitigation run."""
    if strategy != "inverse_sqrt_frequency":
        raise ValueError(f"Unsupported reweighting strategy: {strategy}")

    group_counts = Counter(str(record[grouping_field]) for record in train_records)
    if not group_counts:
        raise ValueError("Cannot build group weights from an empty training set.")

    raw_weights = {
        group_name: 1.0 / math.sqrt(float(count))
        for group_name, count in group_counts.items()
    }
    clipped_weights = {
        group_name: min(weight, float(max_weight))
        for group_name, weight in raw_weights.items()
    }
    sample_count = sum(group_counts.values())
    mean_sample_weight = sum(
        clipped_weights[group_name] * count
        for group_name, count in group_counts.items()
    ) / float(sample_count)
    scale_factor = float(normalize_mean) / mean_sample_weight

    rows = []
    for group_name in sorted(group_counts):
        clipped_weight = clipped_weights[group_name]
        scaled_weight = min(clipped_weight * scale_factor, float(max_weight))
        rows.append(
            {
                "group_id": group_name,
                "support": int(group_counts[group_name]),
                "raw_weight": float(raw_weights[group_name]),
                "clipped_weight": float(clipped_weight),
                "sample_weight": float(scaled_weight),
                "grouping_field": grouping_field,
                "strategy": strategy,
                "max_weight": float(max_weight),
                "normalize_mean": float(normalize_mean),
            }
        )

    return pd.DataFrame(rows)


def _write_group_weights(run_dir: Path, group_weights: pd.DataFrame) -> Path:
    output_path = run_dir / "group_weights.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    group_weights.to_csv(output_path, index=False)
    return output_path


def train_distilbert_reweighting(
    config: dict[str, Any],
    run_dir: Path,
    *,
    dataset_loader: DatasetLoader | None = None,
    tokenizer_factory: TokenizerFactory | None = None,
    model_factory: ModelFactory | None = None,
) -> DistilBertReweightingArtifacts:
    """Train the DistilBERT reweighting mitigation from the inherited parent config."""
    set_random_seed(int(config["seed"]))
    resolved_loader = dataset_loader or load_baseline_canonical_dataset
    resolved_tokenizer_factory = tokenizer_factory or build_tokenizer
    resolved_model_factory = model_factory or build_sequence_classifier

    dataset = resolved_loader(config, download=True)
    model_config = dict(config.get("model", {}))
    train_config = dict(config.get("train", {}))
    eval_config = dict(config.get("eval", {}))
    mitigation_config = dict(config.get("mitigation_config") or config.get("mitigation") or {})
    reweighting_config = dict(mitigation_config.get("reweighting", {}))

    pretrained_name = str(model_config.get("pretrained_name", "distilbert-base-uncased"))
    max_length = int(model_config.get("max_length", 256))
    tokenizer = resolved_tokenizer_factory(pretrained_name)
    train_view = prepare_transformer_adapter(
        dataset.samples,
        split="train",
        tokenizer_name=pretrained_name,
        max_length=max_length,
    )
    validation_view = prepare_transformer_adapter(
        dataset.samples,
        split="validation",
        tokenizer_name=pretrained_name,
        max_length=max_length,
    )

    group_weights = build_group_weight_table(
        train_view.records,
        grouping_field=str(reweighting_config.get("grouping_field", "group_id")),
        strategy=str(reweighting_config.get("strategy", "inverse_sqrt_frequency")),
        max_weight=float(reweighting_config.get("max_weight", 5.0)),
        normalize_mean=float(reweighting_config.get("normalize_mean", 1.0)),
    )
    weight_lookup = {
        str(row["group_id"]): float(row["sample_weight"])
        for row in group_weights.to_dict(orient="records")
    }
    sample_weights = [
        float(weight_lookup[str(record["group_id"])]) for record in train_view.records
    ]

    train_dataset = WeightedTokenizedTextDataset(
        train_view.records,
        tokenizer,
        max_length=max_length,
        sample_weights=sample_weights,
    )
    validation_dataset = WeightedTokenizedTextDataset(
        validation_view.records,
        tokenizer,
        max_length=max_length,
    )
    pad_token_id = int(getattr(tokenizer, "pad_token_id", 0) or 0)

    batch_size_config = dict(model_config.get("batch_size", {}))
    train_batch_size = int(batch_size_config.get("train", train_config.get("batch_size", 16)))
    eval_batch_size = int(batch_size_config.get("eval", train_config.get("eval_batch_size", 32)))

    train_loader = DataLoader(
        train_dataset,
        batch_size=train_batch_size,
        shuffle=True,
        num_workers=int(train_config.get("num_workers", 0)),
        collate_fn=_build_collate_fn(pad_token_id, include_sample_weight=True),
    )
    train_eval_loader = DataLoader(
        train_dataset,
        batch_size=eval_batch_size,
        shuffle=False,
        num_workers=int(train_config.get("num_workers", 0)),
        collate_fn=_build_collate_fn(pad_token_id, include_sample_weight=False),
    )
    validation_loader = DataLoader(
        validation_dataset,
        batch_size=eval_batch_size,
        shuffle=False,
        num_workers=int(train_config.get("num_workers", 0)),
        collate_fn=_build_collate_fn(pad_token_id, include_sample_weight=False),
    )

    model = resolved_model_factory(pretrained_name, 2)
    device, use_mixed_precision = _device_and_precision(config)
    model.to(device)

    optimizer_config = dict(model_config.get("optimizer", {}))
    learning_rate = float(optimizer_config.get("learning_rate", 2.0e-5))
    weight_decay = float(optimizer_config.get("weight_decay", 0.01))
    warmup_ratio = float(optimizer_config.get("warmup_ratio", 0.1))
    gradient_clip_norm = float(optimizer_config.get("gradient_clip_norm", 1.0))
    optimizer = AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    total_steps = max(len(train_loader) * int(train_config.get("max_epochs", 3)), 1)
    warmup_steps = int(total_steps * warmup_ratio)
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps,
    )
    scaler = torch.amp.GradScaler("cuda", enabled=use_mixed_precision)

    primary_metric_name = str(eval_config.get("primary_metric", "macro_f1"))
    early_stopping_config = dict(model_config.get("early_stopping", {}))
    early_stopping_enabled = bool(early_stopping_config.get("enabled", True))
    patience_limit = int(
        early_stopping_config.get(
            "patience",
            train_config.get("early_stopping_patience", 1),
        )
    )

    best_metric = float("-inf")
    epochs_without_improvement = 0
    best_state_dict: dict[str, torch.Tensor] | None = None
    best_validation_result: dict[str, Any] | None = None
    history: list[dict[str, Any]] = []

    max_epochs = int(train_config.get("max_epochs", 3))
    for epoch in range(max_epochs):
        model.train()
        total_train_loss = 0.0
        for batch in train_loader:
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)
            sample_weight = batch["sample_weight"].to(device)
            with torch.amp.autocast("cuda", enabled=use_mixed_precision):
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                )
                per_sample_loss = F.cross_entropy(
                    outputs.logits,
                    labels,
                    reduction="none",
                )
                loss = (per_sample_loss * sample_weight).mean()

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), gradient_clip_norm)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()

            total_train_loss += float(loss.detach().cpu().item())

        validation_result = _run_validation(model, validation_loader, device=device)
        epoch_metrics = dict(validation_result["metrics"])
        selector_value = epoch_metrics.get(primary_metric_name)
        history.append(
            {
                "epoch": epoch + 1,
                "train_loss": total_train_loss / max(len(train_loader), 1),
                "validation_metrics": epoch_metrics,
            }
        )

        if selector_value is not None and float(selector_value) > best_metric:
            best_metric = float(selector_value)
            best_state_dict = copy.deepcopy(model.state_dict())
            best_validation_result = validation_result
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1

        if early_stopping_enabled and epochs_without_improvement > patience_limit:
            break

    if best_state_dict is None or best_validation_result is None:
        raise RuntimeError(
            "DistilBERT reweighting did not produce a selectable validation checkpoint."
        )

    checkpoint_dir, checkpoint_path, history_path, tokenizer_config_path = _checkpoint_paths(
        run_dir
    )
    group_weights_path = _write_group_weights(run_dir, group_weights)
    torch.save(best_state_dict, checkpoint_path)
    history_path.write_text(json.dumps(history, indent=2, sort_keys=True), encoding="utf-8")
    tokenizer_config = {
        "pretrained_name": pretrained_name,
        "max_length": max_length,
        "truncation": bool(model_config.get("truncation", True)),
        "dynamic_padding": bool(model_config.get("dynamic_padding", True)),
        "mixed_precision_used": use_mixed_precision,
    }
    tokenizer_config_path.write_text(
        json.dumps(tokenizer_config, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    if hasattr(tokenizer, "save_pretrained"):
        tokenizer.save_pretrained(checkpoint_dir / "tokenizer")

    model.load_state_dict(best_state_dict)
    train_export_result = _run_validation(model, train_eval_loader, device=device)
    validation_export_result = _run_validation(model, validation_loader, device=device)
    prediction_paths = write_prediction_exports(
        run_dir,
        {
            "train": build_prediction_records(
                run_id=str(config["run_id"]),
                model_name=str(config["model_name"]),
                sample_ids=train_export_result["metadata"]["sample_id"],
                splits=train_export_result["metadata"]["split"],
                true_labels=train_export_result["labels"],
                predicted_labels=train_export_result["predictions"],
                probability_rows=train_export_result["probabilities"],
                group_ids=train_export_result["metadata"]["group_id"],
                is_id_flags=train_export_result["metadata"]["is_id"],
                is_ood_flags=train_export_result["metadata"]["is_ood"],
                logits_rows=train_export_result["logits"],
            ),
            "validation": build_prediction_records(
                run_id=str(config["run_id"]),
                model_name=str(config["model_name"]),
                sample_ids=validation_export_result["metadata"]["sample_id"],
                splits=validation_export_result["metadata"]["split"],
                true_labels=validation_export_result["labels"],
                predicted_labels=validation_export_result["predictions"],
                probability_rows=validation_export_result["probabilities"],
                group_ids=validation_export_result["metadata"]["group_id"],
                is_id_flags=validation_export_result["metadata"]["is_id"],
                is_ood_flags=validation_export_result["metadata"]["is_ood"],
                logits_rows=validation_export_result["logits"],
            ),
        },
    )

    validation_metrics = dict(best_validation_result["metrics"])
    metrics_payload = {
        "primary_metric": {
            "name": primary_metric_name,
            "value": validation_metrics.get(primary_metric_name),
        },
        "worst_group_metric": {
            "name": str(eval_config.get("worst_group_metric", "accuracy")),
            "value": None,
        },
        "robustness_gap": {
            "name": str(eval_config.get("robustness_gap_metric", "accuracy_delta")),
            "value": None,
        },
        "calibration_metric": {
            "name": str(eval_config.get("calibration_metric", "ece")),
            "value": None,
        },
        "validation_metrics": validation_metrics,
        "training_history": history,
        "selected_checkpoint": {
            "path": str(checkpoint_path),
            "source": "best_validation_checkpoint",
            "mixed_precision_used": use_mixed_precision,
        },
        "group_weighting": {
            "group_count": int(len(group_weights)),
            "max_sample_weight": float(group_weights["sample_weight"].max()),
            "min_sample_weight": float(group_weights["sample_weight"].min()),
        },
    }

    return DistilBertReweightingArtifacts(
        metrics_payload=metrics_payload,
        prediction_paths=prediction_paths,
        checkpoint_dir=checkpoint_dir,
        checkpoint_path=checkpoint_path,
        history_path=history_path,
        tokenizer_config_path=tokenizer_config_path,
        group_weights_path=group_weights_path,
    )
