"""DistilBERT Group DRO mitigation built on the inherited parent training contract."""

from __future__ import annotations

import copy
import json
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
class DistilBertGroupDroArtifacts:
    """Artifacts produced by a completed DistilBERT Group DRO run."""

    metrics_payload: dict[str, Any]
    prediction_paths: dict[str, Path]
    checkpoint_dir: Path
    checkpoint_path: Path
    history_path: Path
    tokenizer_config_path: Path
    group_dro_weights_path: Path
    training_summary: dict[str, Any]


class GroupDroTokenizedTextDataset(Dataset):
    """Tokenizer-backed dataset that carries group indices for robust training."""

    def __init__(
        self,
        records: list[dict[str, Any]],
        tokenizer: Any,
        *,
        max_length: int,
        group_to_index: dict[str, int],
    ) -> None:
        self.records = records
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.group_to_index = group_to_index

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
        group_id = str(record["group_id"])
        return {
            "input_ids": list(encoded["input_ids"]),
            "attention_mask": list(encoded["attention_mask"]),
            "labels": int(record["label"]),
            "sample_id": str(record["sample_id"]),
            "split": str(record["split"]),
            "group_id": group_id,
            "group_index": int(self.group_to_index[group_id]),
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


def _pad_sequences(sequences: list[list[int]], pad_token_id: int) -> torch.Tensor:
    max_length = max(len(sequence) for sequence in sequences)
    padded = [sequence + [pad_token_id] * (max_length - len(sequence)) for sequence in sequences]
    return torch.tensor(padded, dtype=torch.long)


def _build_collate_fn(pad_token_id: int):
    def collate_fn(examples: list[dict[str, Any]]) -> dict[str, Any]:
        return {
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
            "group_index": torch.tensor(
                [example["group_index"] for example in examples],
                dtype=torch.long,
            ),
            "sample_id": [example["sample_id"] for example in examples],
            "split": [example["split"] for example in examples],
            "group_id": [example["group_id"] for example in examples],
            "is_id": [example["is_id"] for example in examples],
            "is_ood": [example["is_ood"] for example in examples],
        }

    return collate_fn


def build_group_dro_state_table(
    train_records: list[dict[str, Any]],
    *,
    grouping_field: str = "group_id",
) -> pd.DataFrame:
    """Build the persisted group-state table for a Group DRO run."""
    group_counts = Counter(str(record[grouping_field]) for record in train_records)
    if not group_counts:
        raise ValueError("Cannot build Group DRO state from an empty training set.")

    uniform_weight = 1.0 / float(len(group_counts))
    rows = []
    for group_id in sorted(group_counts):
        rows.append(
            {
                "group_id": group_id,
                "support": int(group_counts[group_id]),
                "initial_weight": uniform_weight,
                "final_weight": uniform_weight,
                "ema_loss": 0.0,
                "visit_count": 0,
            }
        )
    return pd.DataFrame(rows)


def _write_group_dro_weights(run_dir: Path, group_state: pd.DataFrame) -> Path:
    output_path = run_dir / "group_dro_weights.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    group_state.to_csv(output_path, index=False)
    return output_path


def train_distilbert_group_dro(
    config: dict[str, Any],
    run_dir: Path,
    *,
    dataset_loader: DatasetLoader | None = None,
    tokenizer_factory: TokenizerFactory | None = None,
    model_factory: ModelFactory | None = None,
) -> DistilBertGroupDroArtifacts:
    """Train the DistilBERT Group DRO mitigation from the inherited parent config."""
    set_random_seed(int(config["seed"]))
    resolved_loader = dataset_loader or load_baseline_canonical_dataset
    resolved_tokenizer_factory = tokenizer_factory or build_tokenizer
    resolved_model_factory = model_factory or build_sequence_classifier

    dataset = resolved_loader(config, download=True)
    model_config = dict(config.get("model", {}))
    train_config = dict(config.get("train", {}))
    eval_config = dict(config.get("eval", {}))
    mitigation_config = dict(config.get("mitigation_config") or config.get("mitigation") or {})
    group_dro_config = dict(mitigation_config.get("group_dro", {}))

    pretrained_name = str(model_config.get("pretrained_name", "distilbert-base-uncased"))
    max_length = int(model_config.get("max_length", 256))
    grouping_field = str(group_dro_config.get("grouping_field", "group_id"))
    adversary_step_size = float(group_dro_config.get("adversary_step_size", 0.1))
    loss_ema = float(group_dro_config.get("loss_ema", 0.2))

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

    group_state = build_group_dro_state_table(
        train_view.records,
        grouping_field=grouping_field,
    )
    group_rows = group_state.to_dict(orient="records")
    group_ids = [str(row["group_id"]) for row in group_rows]
    group_to_index = {group_id: idx for idx, group_id in enumerate(group_ids)}
    group_support = {str(row["group_id"]): int(row["support"]) for row in group_rows}

    train_dataset = GroupDroTokenizedTextDataset(
        train_view.records,
        tokenizer,
        max_length=max_length,
        group_to_index=group_to_index,
    )
    validation_dataset = GroupDroTokenizedTextDataset(
        validation_view.records,
        tokenizer,
        max_length=max_length,
        group_to_index=group_to_index,
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
        collate_fn=_build_collate_fn(pad_token_id),
    )
    train_eval_loader = DataLoader(
        train_dataset,
        batch_size=eval_batch_size,
        shuffle=False,
        num_workers=int(train_config.get("num_workers", 0)),
        collate_fn=_build_collate_fn(pad_token_id),
    )
    validation_loader = DataLoader(
        validation_dataset,
        batch_size=eval_batch_size,
        shuffle=False,
        num_workers=int(train_config.get("num_workers", 0)),
        collate_fn=_build_collate_fn(pad_token_id),
    )
    if bool(train_config.get("export_blind_test_predictions", False)):
        id_test_view = prepare_transformer_adapter(
            dataset.samples,
            split="id_test",
            tokenizer_name=pretrained_name,
            max_length=max_length,
        )
        id_test_dataset = GroupDroTokenizedTextDataset(
            id_test_view.records,
            tokenizer,
            max_length=max_length,
            group_to_index=group_to_index,
        )
        id_test_loader = DataLoader(
            id_test_dataset,
            batch_size=eval_batch_size,
            shuffle=False,
            num_workers=int(train_config.get("num_workers", 0)),
            collate_fn=_build_collate_fn(pad_token_id),
        )
        ood_test_view = prepare_transformer_adapter(
            dataset.samples,
            split="ood_test",
            tokenizer_name=pretrained_name,
            max_length=max_length,
        )
        ood_test_dataset = GroupDroTokenizedTextDataset(
            ood_test_view.records,
            tokenizer,
            max_length=max_length,
            group_to_index=group_to_index,
        )
        ood_test_loader = DataLoader(
            ood_test_dataset,
            batch_size=eval_batch_size,
            shuffle=False,
            num_workers=int(train_config.get("num_workers", 0)),
            collate_fn=_build_collate_fn(pad_token_id),
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

    adversarial_logits = torch.zeros(len(group_ids), dtype=torch.float32, device=device)
    ema_losses = torch.zeros(len(group_ids), dtype=torch.float32, device=device)
    visit_counts = torch.zeros(len(group_ids), dtype=torch.long, device=device)

    best_metric = float("-inf")
    epochs_without_improvement = 0
    best_state_dict: dict[str, torch.Tensor] | None = None
    best_validation_result: dict[str, Any] | None = None
    best_group_state: list[dict[str, Any]] | None = None
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
            group_index = batch["group_index"].to(device)

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
                unique_groups = torch.unique(group_index)
                group_losses: list[torch.Tensor] = []
                active_indices: list[int] = []
                for index_tensor in unique_groups:
                    index_value = int(index_tensor.item())
                    mask = group_index == index_value
                    if not bool(mask.any()):
                        continue
                    group_loss = per_sample_loss[mask].mean()
                    ema_losses[index_value] = (
                        (1.0 - loss_ema) * ema_losses[index_value]
                        + (loss_ema * group_loss.detach())
                    )
                    adversarial_logits[index_value] = (
                        adversarial_logits[index_value]
                        + (adversary_step_size * ema_losses[index_value].detach())
                    )
                    visit_counts[index_value] += 1
                    group_losses.append(group_loss)
                    active_indices.append(index_value)

                if not group_losses:
                    loss = per_sample_loss.mean()
                else:
                    active_index_tensor = torch.tensor(
                        active_indices,
                        device=device,
                        dtype=torch.long,
                    )
                    active_weights = torch.softmax(adversarial_logits, dim=0)[active_index_tensor]
                    active_weights = active_weights / active_weights.sum().clamp_min(1e-8)
                    loss = (torch.stack(group_losses) * active_weights).sum()

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
        current_weights = torch.softmax(adversarial_logits, dim=0).detach().cpu().tolist()
        history.append(
            {
                "epoch": epoch + 1,
                "train_loss": total_train_loss / max(len(train_loader), 1),
                "validation_metrics": epoch_metrics,
                "group_weights": {
                    group_id: float(current_weights[group_to_index[group_id]])
                    for group_id in group_ids
                },
            }
        )

        if selector_value is not None and float(selector_value) > best_metric:
            best_metric = float(selector_value)
            best_state_dict = copy.deepcopy(model.state_dict())
            best_validation_result = validation_result
            best_group_state = [
                {
                    "group_id": group_id,
                    "support": int(group_support[group_id]),
                    "initial_weight": float(1.0 / len(group_ids)),
                    "final_weight": float(current_weights[group_to_index[group_id]]),
                    "ema_loss": float(ema_losses[group_to_index[group_id]].detach().cpu().item()),
                    "visit_count": int(
                        visit_counts[group_to_index[group_id]].detach().cpu().item()
                    ),
                }
                for group_id in group_ids
            ]
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1

        if early_stopping_enabled and epochs_without_improvement > patience_limit:
            break

    if best_state_dict is None or best_validation_result is None or best_group_state is None:
        raise RuntimeError(
            "DistilBERT Group DRO did not produce a selectable validation checkpoint."
        )

    checkpoint_dir, checkpoint_path, history_path, tokenizer_config_path = _checkpoint_paths(
        run_dir
    )
    group_dro_weights_path = _write_group_dro_weights(
        run_dir,
        pd.DataFrame(best_group_state),
    )
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
    export_loaders = {
        "train": train_eval_loader,
        "validation": validation_loader,
    }
    if bool(train_config.get("export_blind_test_predictions", False)):
        export_loaders["id_test"] = id_test_loader
        export_loaders["ood_test"] = ood_test_loader
    prediction_exports = {}
    for split_name, export_loader in export_loaders.items():
        export_result = _run_validation(model, export_loader, device=device)
        prediction_exports[split_name] = build_prediction_records(
            run_id=str(config["run_id"]),
            model_name=str(config["model_name"]),
            sample_ids=export_result["metadata"]["sample_id"],
            splits=export_result["metadata"]["split"],
            true_labels=export_result["labels"],
            predicted_labels=export_result["predictions"],
            probability_rows=export_result["probabilities"],
            group_ids=export_result["metadata"]["group_id"],
            is_id_flags=export_result["metadata"]["is_id"],
            is_ood_flags=export_result["metadata"]["is_ood"],
            logits_rows=export_result["logits"],
        )
    prediction_paths = write_prediction_exports(run_dir, prediction_exports)

    validation_metrics = dict(best_validation_result["metrics"])
    final_weights_frame = pd.DataFrame(best_group_state)
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
        "group_dro": {
            "group_count": int(len(final_weights_frame)),
            "max_group_weight": float(final_weights_frame["final_weight"].max()),
            "min_group_weight": float(final_weights_frame["final_weight"].min()),
            "max_ema_loss": float(final_weights_frame["ema_loss"].max()),
        },
    }

    return DistilBertGroupDroArtifacts(
        metrics_payload=metrics_payload,
        prediction_paths=prediction_paths,
        checkpoint_dir=checkpoint_dir,
        checkpoint_path=checkpoint_path,
        history_path=history_path,
        tokenizer_config_path=tokenizer_config_path,
        group_dro_weights_path=group_dro_weights_path,
        training_summary={
            "best_epoch": max(
                (
                    int(item["epoch"])
                    for item in history
                    if item.get("validation_metrics", {}).get(primary_metric_name)
                    == validation_metrics.get(primary_metric_name)
                ),
                default=1,
            ),
            "best_validation_metric_name": primary_metric_name,
            "best_validation_metric_value": validation_metrics.get(primary_metric_name),
            "selected_checkpoint_path": str(checkpoint_path),
            "train_sample_count": len(train_view.records),
            "validation_sample_count": len(validation_view.records),
            "completed_epochs": len(history),
        },
    )
