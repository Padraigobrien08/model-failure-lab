"""DistilBERT baseline training with explicit best-checkpoint selection."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)

from model_failure_lab.data import CanonicalDataset, prepare_transformer_adapter

from .common import (
    compute_binary_classification_metrics,
    load_baseline_canonical_dataset,
    set_random_seed,
)
from .export import build_prediction_records, write_prediction_exports

DatasetLoader = Callable[..., CanonicalDataset]
TokenizerFactory = Callable[[str], Any]
ModelFactory = Callable[[str, int], torch.nn.Module]


def _raise_pretrained_loading_error(exc: Exception, pretrained_name: str) -> None:
    raise RuntimeError(
        f"Unable to load '{pretrained_name}' for DistilBERT execution. "
        "The first run requires either network access or a pre-populated local cache. "
        "Run `python scripts/check_environment.py` to verify benchmark prerequisites."
    ) from exc


@dataclass(slots=True)
class DistilBertBaselineArtifacts:
    """Artifacts produced by a completed DistilBERT baseline run."""

    metrics_payload: dict[str, Any]
    prediction_paths: dict[str, Path]
    checkpoint_dir: Path
    checkpoint_path: Path
    history_path: Path
    tokenizer_config_path: Path


class TokenizedTextDataset(Dataset):
    """Tokenizer-backed dataset that preserves sample metadata for export."""

    def __init__(self, records: list[dict[str, Any]], tokenizer: Any, *, max_length: int) -> None:
        self.records = records
        self.tokenizer = tokenizer
        self.max_length = max_length

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
        return {
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


def build_tokenizer(pretrained_name: str) -> Any:
    """Build the tokenizer for the requested pretrained checkpoint."""
    try:
        return AutoTokenizer.from_pretrained(pretrained_name)
    except (OSError, ValueError) as exc:
        _raise_pretrained_loading_error(exc, pretrained_name)


def build_sequence_classifier(pretrained_name: str, num_labels: int) -> torch.nn.Module:
    """Build the DistilBERT sequence-classification model."""
    try:
        return AutoModelForSequenceClassification.from_pretrained(
            pretrained_name,
            num_labels=num_labels,
        )
    except (OSError, ValueError) as exc:
        _raise_pretrained_loading_error(exc, pretrained_name)


def _checkpoint_paths(run_dir: Path) -> tuple[Path, Path, Path, Path]:
    checkpoint_dir = run_dir / "checkpoint"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    return (
        checkpoint_dir,
        checkpoint_dir / "best_model.pt",
        checkpoint_dir / "training_history.json",
        checkpoint_dir / "tokenizer_config.json",
    )


def _pad_sequences(sequences: list[list[int]], pad_token_id: int) -> torch.Tensor:
    max_length = max(len(sequence) for sequence in sequences)
    padded = [sequence + [pad_token_id] * (max_length - len(sequence)) for sequence in sequences]
    return torch.tensor(padded, dtype=torch.long)


def _collate_batch(examples: list[dict[str, Any]], *, pad_token_id: int) -> dict[str, Any]:
    return {
        "input_ids": _pad_sequences([example["input_ids"] for example in examples], pad_token_id),
        "attention_mask": _pad_sequences(
            [example["attention_mask"] for example in examples],
            0,
        ),
        "labels": torch.tensor([example["labels"] for example in examples], dtype=torch.long),
        "sample_id": [example["sample_id"] for example in examples],
        "split": [example["split"] for example in examples],
        "group_id": [example["group_id"] for example in examples],
        "is_id": [example["is_id"] for example in examples],
        "is_ood": [example["is_ood"] for example in examples],
    }


def _build_collate_fn(pad_token_id: int):
    def collate_fn(examples: list[dict[str, Any]]) -> dict[str, Any]:
        return _collate_batch(examples, pad_token_id=pad_token_id)

    return collate_fn


def _device_and_precision(config: dict[str, Any]) -> tuple[torch.device, bool]:
    mixed_precision_config = config.get("model", {}).get(
        "mixed_precision",
        config.get("train", {}).get("mixed_precision", False),
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_mixed_precision = device.type == "cuda" and mixed_precision_config not in {False, "false"}
    return device, use_mixed_precision


def _prediction_records(
    *,
    run_id: str,
    model_name: str,
    true_labels: list[int],
    predicted_labels: list[int],
    probability_rows: list[list[float]],
    logits_rows: list[list[float]],
    metadata: dict[str, list[Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, sample_id in enumerate(metadata["sample_id"]):
        probability_positive = float(probability_rows[index][1])
        records.append(
            {
                "run_id": run_id,
                "sample_id": sample_id,
                "split": metadata["split"][index],
                "model_name": model_name,
                "true_label": int(true_labels[index]),
                "pred_label": int(predicted_labels[index]),
                "pred_score": probability_positive,
                "prob_0": float(probability_rows[index][0]),
                "prob_1": probability_positive,
                "is_correct": int(predicted_labels[index]) == int(true_labels[index]),
                "group_id": metadata["group_id"][index],
                "is_id": bool(metadata["is_id"][index]),
                "is_ood": bool(metadata["is_ood"][index]),
                "logit_0": float(logits_rows[index][0]),
                "logit_1": float(logits_rows[index][1]),
            }
        )
    return records


def _run_validation(
    model: torch.nn.Module,
    dataloader: DataLoader,
    *,
    device: torch.device,
) -> dict[str, Any]:
    model.eval()
    total_loss = 0.0
    batches = 0
    all_labels: list[int] = []
    all_predictions: list[int] = []
    all_probabilities: list[list[float]] = []
    all_logits: list[list[float]] = []
    metadata = {"sample_id": [], "split": [], "group_id": [], "is_id": [], "is_ood": []}

    with torch.no_grad():
        for batch in dataloader:
            labels = batch["labels"].to(device)
            outputs = model(
                input_ids=batch["input_ids"].to(device),
                attention_mask=batch["attention_mask"].to(device),
                labels=labels,
            )
            logits = outputs.logits.detach().cpu()
            probabilities = torch.softmax(logits, dim=-1)
            predictions = torch.argmax(probabilities, dim=-1)

            total_loss += float(outputs.loss.detach().cpu().item())
            batches += 1
            all_labels.extend(labels.detach().cpu().tolist())
            all_predictions.extend(predictions.tolist())
            all_probabilities.extend(probabilities.tolist())
            all_logits.extend(logits.tolist())
            for key in metadata:
                metadata[key].extend(list(batch[key]))

    probability_positive = [float(row[1]) for row in all_probabilities]
    metrics = compute_binary_classification_metrics(
        true_labels=all_labels,
        predicted_labels=all_predictions,
        probability_positive=probability_positive,
    )
    metrics["loss"] = total_loss / batches if batches else None
    return {
        "metrics": metrics,
        "labels": all_labels,
        "predictions": all_predictions,
        "probabilities": all_probabilities,
        "logits": all_logits,
        "metadata": metadata,
    }


def _build_export_loader(
    samples: list[Any],
    *,
    split: str,
    tokenizer: Any,
    pretrained_name: str,
    max_length: int,
    batch_size: int,
    num_workers: int,
    collate_fn: Any,
) -> DataLoader:
    split_view = prepare_transformer_adapter(
        samples,
        split=split,
        tokenizer_name=pretrained_name,
        max_length=max_length,
    )
    split_dataset = TokenizedTextDataset(split_view.records, tokenizer, max_length=max_length)
    return DataLoader(
        split_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        collate_fn=collate_fn,
    )


def train_distilbert_baseline(
    config: dict[str, Any],
    run_dir: Path,
    *,
    dataset_loader: DatasetLoader | None = None,
    tokenizer_factory: TokenizerFactory | None = None,
    model_factory: ModelFactory | None = None,
) -> DistilBertBaselineArtifacts:
    """Train the canonical DistilBERT baseline."""
    set_random_seed(int(config["seed"]))
    resolved_loader = dataset_loader or load_baseline_canonical_dataset
    resolved_tokenizer_factory = tokenizer_factory or build_tokenizer
    resolved_model_factory = model_factory or build_sequence_classifier

    dataset = resolved_loader(config, download=True)
    model_config = dict(config.get("model", {}))
    train_config = dict(config.get("train", {}))
    eval_config = dict(config.get("eval", {}))

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

    train_dataset = TokenizedTextDataset(train_view.records, tokenizer, max_length=max_length)
    validation_dataset = TokenizedTextDataset(
        validation_view.records,
        tokenizer,
        max_length=max_length,
    )
    pad_token_id = int(getattr(tokenizer, "pad_token_id", 0) or 0)

    batch_size_config = dict(model_config.get("batch_size", {}))
    train_batch_size = int(batch_size_config.get("train", train_config.get("batch_size", 16)))
    eval_batch_size = int(batch_size_config.get("eval", train_config.get("eval_batch_size", 32)))
    collate_fn = _build_collate_fn(pad_token_id)

    train_loader = DataLoader(
        train_dataset,
        batch_size=train_batch_size,
        shuffle=True,
        num_workers=int(train_config.get("num_workers", 0)),
        collate_fn=collate_fn,
    )
    train_eval_loader = DataLoader(
        train_dataset,
        batch_size=eval_batch_size,
        shuffle=False,
        num_workers=int(train_config.get("num_workers", 0)),
        collate_fn=collate_fn,
    )
    validation_loader = DataLoader(
        validation_dataset,
        batch_size=eval_batch_size,
        shuffle=False,
        num_workers=int(train_config.get("num_workers", 0)),
        collate_fn=collate_fn,
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
            with torch.amp.autocast("cuda", enabled=use_mixed_precision):
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels,
                )
                loss = outputs.loss

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
            "DistilBERT baseline did not produce a selectable validation checkpoint."
        )

    checkpoint_dir, checkpoint_path, history_path, tokenizer_config_path = _checkpoint_paths(
        run_dir
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
        export_loaders["id_test"] = _build_export_loader(
            dataset.samples,
            split="id_test",
            tokenizer=tokenizer,
            pretrained_name=pretrained_name,
            max_length=max_length,
            batch_size=eval_batch_size,
            num_workers=int(train_config.get("num_workers", 0)),
            collate_fn=collate_fn,
        )
        export_loaders["ood_test"] = _build_export_loader(
            dataset.samples,
            split="ood_test",
            tokenizer=tokenizer,
            pretrained_name=pretrained_name,
            max_length=max_length,
            batch_size=eval_batch_size,
            num_workers=int(train_config.get("num_workers", 0)),
            collate_fn=collate_fn,
        )

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
    }

    return DistilBertBaselineArtifacts(
        metrics_payload=metrics_payload,
        prediction_paths=prediction_paths,
        checkpoint_dir=checkpoint_dir,
        checkpoint_path=checkpoint_path,
        history_path=history_path,
        tokenizer_config_path=tokenizer_config_path,
    )
