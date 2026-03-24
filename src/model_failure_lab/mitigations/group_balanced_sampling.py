"""DistilBERT group-balanced sampling mitigation built on the baseline training contract."""

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
from torch.optim import AdamW
from torch.utils.data import DataLoader, WeightedRandomSampler
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

from .reweighting import WeightedTokenizedTextDataset, _build_collate_fn

DatasetLoader = Callable[..., CanonicalDataset]
TokenizerFactory = Callable[[str], Any]
ModelFactory = Callable[[str, int], torch.nn.Module]


@dataclass(slots=True)
class DistilBertGroupBalancedSamplingArtifacts:
    """Artifacts produced by a completed DistilBERT group-balanced sampling run."""

    metrics_payload: dict[str, Any]
    prediction_paths: dict[str, Path]
    checkpoint_dir: Path
    checkpoint_path: Path
    history_path: Path
    tokenizer_config_path: Path
    sampling_weights_path: Path
    training_summary: dict[str, Any]


def build_group_sampling_table(
    train_records: list[dict[str, Any]],
    *,
    grouping_field: str = "group_id",
    strategy: str = "inverse_sqrt_frequency",
    blend_alpha: float = 0.35,
    max_sampling_multiplier: float = 3.0,
) -> pd.DataFrame:
    """Build the saved per-group sampling recipe for a mitigation run."""
    if strategy != "inverse_sqrt_frequency":
        raise ValueError(f"Unsupported group-balanced sampling strategy: {strategy}")
    if not 0.0 <= float(blend_alpha) <= 1.0:
        raise ValueError("blend_alpha must be in the interval [0, 1]")
    if float(max_sampling_multiplier) < 1.0:
        raise ValueError("max_sampling_multiplier must be at least 1.0")

    group_counts = Counter(str(record[grouping_field]) for record in train_records)
    if not group_counts:
        raise ValueError("Cannot build sampling weights from an empty training set.")

    total_count = sum(group_counts.values())
    group_count = len(group_counts)
    base_scores = {
        group_name: 1.0 / math.sqrt(float(count))
        for group_name, count in group_counts.items()
    }
    base_score_total = sum(base_scores.values())
    base_group_mass = {
        group_name: float(base_scores[group_name] / base_score_total)
        for group_name in group_counts
    }
    uniform_group_mass = {group_name: float(1.0 / group_count) for group_name in group_counts}
    target_group_mass = {
        group_name: float(
            ((1.0 - float(blend_alpha)) * base_group_mass[group_name])
            + (float(blend_alpha) * uniform_group_mass[group_name])
        )
        for group_name in group_counts
    }

    uncapped_sampling_multiplier = {
        group_name: float(target_group_mass[group_name] * total_count / group_counts[group_name])
        for group_name in group_counts
    }
    sampling_multiplier = {
        group_name: float(
            min(uncapped_sampling_multiplier[group_name], float(max_sampling_multiplier))
        )
        for group_name in group_counts
    }
    total_sampling_weight = sum(
        sampling_multiplier[group_name] * group_counts[group_name]
        for group_name in group_counts
    )

    rows = []
    for group_name in sorted(group_counts):
        sample_probability = float(sampling_multiplier[group_name] / total_sampling_weight)
        final_group_mass = float(sample_probability * group_counts[group_name])
        rows.append(
            {
                "group_id": group_name,
                "support": int(group_counts[group_name]),
                "base_group_mass": float(base_group_mass[group_name]),
                "uniform_group_mass": float(uniform_group_mass[group_name]),
                "target_group_mass": float(target_group_mass[group_name]),
                "final_group_mass": final_group_mass,
                "sample_probability": sample_probability,
                "uncapped_sampling_multiplier": float(
                    uncapped_sampling_multiplier[group_name]
                ),
                "sampling_multiplier": float(sampling_multiplier[group_name]),
                "grouping_field": grouping_field,
                "strategy": strategy,
                "blend_alpha": float(blend_alpha),
                "max_sampling_multiplier": float(max_sampling_multiplier),
            }
        )

    return pd.DataFrame(rows)


def _write_sampling_weights(run_dir: Path, sampling_weights: pd.DataFrame) -> Path:
    output_path = run_dir / "sampling_weights.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sampling_weights.to_csv(output_path, index=False)
    return output_path


def train_distilbert_group_balanced_sampling(
    config: dict[str, Any],
    run_dir: Path,
    *,
    dataset_loader: DatasetLoader | None = None,
    tokenizer_factory: TokenizerFactory | None = None,
    model_factory: ModelFactory | None = None,
) -> DistilBertGroupBalancedSamplingArtifacts:
    """Train DistilBERT with capped group-balanced sampling from the inherited parent config."""
    set_random_seed(int(config["seed"]))
    resolved_loader = dataset_loader or load_baseline_canonical_dataset
    resolved_tokenizer_factory = tokenizer_factory or build_tokenizer
    resolved_model_factory = model_factory or build_sequence_classifier

    dataset = resolved_loader(config, download=True)
    model_config = dict(config.get("model", {}))
    train_config = dict(config.get("train", {}))
    eval_config = dict(config.get("eval", {}))
    mitigation_config = dict(config.get("mitigation_config") or config.get("mitigation") or {})
    sampling_config = dict(mitigation_config.get("group_balanced_sampling", {}))

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

    sampling_table = build_group_sampling_table(
        train_view.records,
        grouping_field=str(sampling_config.get("grouping_field", "group_id")),
        strategy=str(sampling_config.get("strategy", "inverse_sqrt_frequency")),
        blend_alpha=float(sampling_config.get("blend_alpha", 0.35)),
        max_sampling_multiplier=float(sampling_config.get("max_sampling_multiplier", 3.0)),
    )
    multiplier_lookup = {
        str(row["group_id"]): float(row["sampling_multiplier"])
        for row in sampling_table.to_dict(orient="records")
    }
    sample_weights = [
        float(multiplier_lookup[str(record["group_id"])]) for record in train_view.records
    ]

    train_dataset = WeightedTokenizedTextDataset(
        train_view.records,
        tokenizer,
        max_length=max_length,
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

    sampler = WeightedRandomSampler(
        weights=torch.tensor(sample_weights, dtype=torch.double),
        num_samples=len(train_dataset),
        replacement=True,
        generator=torch.Generator().manual_seed(int(config["seed"])),
    )
    train_loader = DataLoader(
        train_dataset,
        batch_size=train_batch_size,
        sampler=sampler,
        num_workers=int(train_config.get("num_workers", 0)),
        collate_fn=_build_collate_fn(pad_token_id, include_sample_weight=False),
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
    if bool(train_config.get("export_blind_test_predictions", False)):
        id_test_view = prepare_transformer_adapter(
            dataset.samples,
            split="id_test",
            tokenizer_name=pretrained_name,
            max_length=max_length,
        )
        id_test_dataset = WeightedTokenizedTextDataset(
            id_test_view.records,
            tokenizer,
            max_length=max_length,
        )
        id_test_loader = DataLoader(
            id_test_dataset,
            batch_size=eval_batch_size,
            shuffle=False,
            num_workers=int(train_config.get("num_workers", 0)),
            collate_fn=_build_collate_fn(pad_token_id, include_sample_weight=False),
        )
        ood_test_view = prepare_transformer_adapter(
            dataset.samples,
            split="ood_test",
            tokenizer_name=pretrained_name,
            max_length=max_length,
        )
        ood_test_dataset = WeightedTokenizedTextDataset(
            ood_test_view.records,
            tokenizer,
            max_length=max_length,
        )
        ood_test_loader = DataLoader(
            ood_test_dataset,
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
            "DistilBERT group-balanced sampling did not produce a selectable validation checkpoint."
        )

    checkpoint_dir, checkpoint_path, history_path, tokenizer_config_path = _checkpoint_paths(
        run_dir
    )
    sampling_weights_path = _write_sampling_weights(run_dir, sampling_table)
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
        "group_balanced_sampling": {
            "group_count": int(len(sampling_table)),
            "blend_alpha": float(sampling_config.get("blend_alpha", 0.35)),
            "max_sampling_multiplier": float(
                sampling_config.get("max_sampling_multiplier", 3.0)
            ),
            "max_final_group_mass": float(sampling_table["final_group_mass"].max()),
            "min_final_group_mass": float(sampling_table["final_group_mass"].min()),
        },
    }

    return DistilBertGroupBalancedSamplingArtifacts(
        metrics_payload=metrics_payload,
        prediction_paths=prediction_paths,
        checkpoint_dir=checkpoint_dir,
        checkpoint_path=checkpoint_path,
        history_path=history_path,
        tokenizer_config_path=tokenizer_config_path,
        sampling_weights_path=sampling_weights_path,
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
