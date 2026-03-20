"""Saved-run scorers for perturbation evaluation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import joblib
import pandas as pd
import torch
from torch.utils.data import DataLoader
from transformers import DistilBertConfig, DistilBertForSequenceClassification

from model_failure_lab.mitigations.temperature_scaling import apply_temperature_scaling
from model_failure_lab.models.distilbert import (
    TokenizedTextDataset,
    _build_collate_fn,
    _device_and_precision,
    _run_validation,
    build_sequence_classifier,
    build_tokenizer,
)
from model_failure_lab.models.export import build_prediction_records
from model_failure_lab.utils.paths import find_run_metadata_path

TokenizerFactory = Callable[[str], Any]
ModelFactory = Callable[[str, int], torch.nn.Module]


@dataclass(slots=True)
class SavedRunScorer:
    """Callable scorer bound to one saved source run."""

    model_name: str
    source_run_id: str
    score_records: Callable[[list[dict[str, Any]], str], pd.DataFrame]


def _artifact_path(metadata: dict[str, Any], key: str) -> Path | None:
    raw_path = dict(metadata.get("artifact_paths", {})).get(key)
    if not raw_path:
        return None
    return _relocate_saved_run_artifact_path(metadata, Path(str(raw_path)))


def _relocate_saved_run_artifact_path(metadata: dict[str, Any], raw_path: Path) -> Path:
    if raw_path.exists():
        return raw_path

    run_id = metadata.get("run_id")
    if not run_id:
        return raw_path

    try:
        run_dir = find_run_metadata_path(str(run_id)).parent
    except (FileNotFoundError, ValueError):
        return raw_path

    candidates = [
        run_dir / raw_path.name,
        run_dir / raw_path.parent.name / raw_path.name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return raw_path


def _selected_checkpoint_path(metadata: dict[str, Any]) -> Path:
    checkpoint_path = _artifact_path(metadata, "selected_checkpoint")
    if checkpoint_path is not None:
        return checkpoint_path
    checkpoint_root = _artifact_path(metadata, "checkpoint")
    if checkpoint_root is not None:
        candidate = checkpoint_root / "best_model.pt"
        if candidate.exists():
            return candidate
    raise ValueError("Saved run metadata is missing a selected checkpoint path")


def _augment_prediction_frame(
    records: list[dict[str, Any]],
    perturbation_samples: list[dict[str, Any]],
) -> pd.DataFrame:
    enriched_records: list[dict[str, Any]] = []
    for record, sample in zip(records, perturbation_samples, strict=True):
        enriched = dict(record)
        enriched["source_sample_id"] = str(sample["source_sample_id"])
        enriched["perturbation_family"] = str(sample["perturbation_family"])
        enriched["severity"] = str(sample["severity"])
        enriched["perturbation_seed"] = int(sample["perturbation_seed"])
        enriched["applied_operations_json"] = json.dumps(
            sample.get("applied_operations", []),
            sort_keys=True,
        )
        enriched_records.append(enriched)
    return pd.DataFrame(enriched_records)


def _logistic_scorer(metadata: dict[str, Any]) -> SavedRunScorer:
    checkpoint_root = _artifact_path(metadata, "checkpoint")
    if checkpoint_root is None:
        raise ValueError("Saved logistic run metadata is missing checkpoint root")
    vectorizer_path = checkpoint_root / "vectorizer.joblib"
    model_path = checkpoint_root / "logistic_model.joblib"
    vectorizer = joblib.load(vectorizer_path)
    classifier = joblib.load(model_path)

    def score_records(perturbation_samples: list[dict[str, Any]], run_id: str) -> pd.DataFrame:
        texts = [str(sample["text"]) for sample in perturbation_samples]
        matrix = vectorizer.transform(texts)
        probability_rows = classifier.predict_proba(matrix).tolist()
        predicted_labels = classifier.predict(matrix).tolist()
        records = build_prediction_records(
            run_id=run_id,
            model_name=str(metadata["model_name"]),
            sample_ids=[str(sample["perturbed_sample_id"]) for sample in perturbation_samples],
            splits=[str(sample["source_split"]) for sample in perturbation_samples],
            true_labels=[int(sample["true_label"]) for sample in perturbation_samples],
            predicted_labels=[int(label) for label in predicted_labels],
            probability_rows=[[float(row[0]), float(row[1])] for row in probability_rows],
            group_ids=[str(sample["source_group_id"]) for sample in perturbation_samples],
            is_id_flags=[bool(sample["source_is_id"]) for sample in perturbation_samples],
            is_ood_flags=[bool(sample["source_is_ood"]) for sample in perturbation_samples],
        )
        return _augment_prediction_frame(records, perturbation_samples)

    return SavedRunScorer(
        model_name=str(metadata["model_name"]),
        source_run_id=str(metadata["run_id"]),
        score_records=score_records,
    )


def _load_tokenizer_config(metadata: dict[str, Any]) -> dict[str, Any]:
    tokenizer_config = dict(metadata.get("resolved_config", {}).get("model", {}))
    checkpoint_roots: list[Path] = []
    checkpoint_root = _artifact_path(metadata, "checkpoint")
    if checkpoint_root is not None:
        checkpoint_roots.append(checkpoint_root)
    selected_checkpoint_path = _artifact_path(metadata, "selected_checkpoint")
    if selected_checkpoint_path is not None:
        checkpoint_roots.append(selected_checkpoint_path.parent)

    seen_roots: set[Path] = set()
    for root in checkpoint_roots:
        if root in seen_roots:
            continue
        seen_roots.add(root)
        config_path = root / "tokenizer_config.json"
        if config_path.exists():
            tokenizer_config = json.loads(config_path.read_text(encoding="utf-8"))
        local_tokenizer_dir = root / "tokenizer"
        if local_tokenizer_dir.exists():
            tokenizer_config["tokenizer_source"] = str(local_tokenizer_dir)
    return tokenizer_config


def _build_offline_sequence_classifier(num_labels: int) -> torch.nn.Module:
    return DistilBertForSequenceClassification(
        DistilBertConfig(num_labels=num_labels)
    )


def _prepare_distilbert_records(perturbation_samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "text": str(sample["text"]),
            "label": int(sample["true_label"]),
            "sample_id": str(sample["perturbed_sample_id"]),
            "split": str(sample["source_split"]),
            "group_id": str(sample["source_group_id"]),
            "is_id": bool(sample["source_is_id"]),
            "is_ood": bool(sample["source_is_ood"]),
            "group_attributes": {},
        }
        for sample in perturbation_samples
    ]


def _load_learned_temperature(metadata: dict[str, Any]) -> float:
    scaler_path = _artifact_path(metadata, "temperature_scaler_json")
    if scaler_path is None or not scaler_path.exists():
        raise ValueError("Temperature-scaling run metadata is missing temperature_scaler_json")
    payload = json.loads(scaler_path.read_text(encoding="utf-8"))
    return float(payload["learned_temperature"])


def _distilbert_scorer(
    metadata: dict[str, Any],
    *,
    tokenizer_factory: TokenizerFactory | None = None,
    model_factory: ModelFactory | None = None,
) -> SavedRunScorer:
    resolved_tokenizer_factory = tokenizer_factory or build_tokenizer
    resolved_model_factory = model_factory or build_sequence_classifier
    tokenizer_config = _load_tokenizer_config(metadata)
    pretrained_name = str(tokenizer_config.get("pretrained_name", "distilbert-base-uncased"))
    tokenizer_source = str(tokenizer_config.get("tokenizer_source", pretrained_name))
    max_length = int(tokenizer_config.get("max_length", 256))
    tokenizer = resolved_tokenizer_factory(tokenizer_source)
    use_offline_shell = tokenizer_source != pretrained_name and Path(tokenizer_source).exists()
    try:
        model = (
            _build_offline_sequence_classifier(2)
            if use_offline_shell
            else resolved_model_factory(pretrained_name, 2)
        )
    except RuntimeError:
        model = _build_offline_sequence_classifier(2)
    checkpoint_path = _selected_checkpoint_path(metadata)
    device, _ = _device_and_precision(metadata.get("resolved_config", {}))
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.to(device)
    model.eval()
    eval_batch_size = int(
        metadata.get("resolved_config", {}).get("model", {}).get("batch_size", {}).get(
            "eval",
            metadata.get("resolved_config", {}).get("train", {}).get("eval_batch_size", 32),
        )
    )
    pad_token_id = int(getattr(tokenizer, "pad_token_id", 0) or 0)

    learned_temperature = None
    if metadata.get("mitigation_method") == "temperature_scaling":
        learned_temperature = _load_learned_temperature(metadata)

    def score_records(perturbation_samples: list[dict[str, Any]], run_id: str) -> pd.DataFrame:
        prepared_records = _prepare_distilbert_records(perturbation_samples)
        tokenized_dataset = TokenizedTextDataset(
            prepared_records,
            tokenizer,
            max_length=max_length,
        )
        dataloader = DataLoader(
            tokenized_dataset,
            batch_size=eval_batch_size,
            shuffle=False,
            num_workers=0,
            collate_fn=_build_collate_fn(pad_token_id),
        )
        evaluation_result = _run_validation(model, dataloader, device=device)

        logits_rows = evaluation_result["logits"]
        probability_rows = evaluation_result["probabilities"]
        predicted_labels = evaluation_result["predictions"]
        if learned_temperature is not None:
            scaled_logits = apply_temperature_scaling(logits_rows, learned_temperature)
            probabilities = torch.softmax(scaled_logits, dim=-1)
            probability_rows = probabilities.tolist()
            logits_rows = scaled_logits.tolist()
            predicted_labels = torch.argmax(probabilities, dim=-1).tolist()

        records = build_prediction_records(
            run_id=run_id,
            model_name=str(metadata["model_name"]),
            sample_ids=evaluation_result["metadata"]["sample_id"],
            splits=evaluation_result["metadata"]["split"],
            true_labels=evaluation_result["labels"],
            predicted_labels=predicted_labels,
            probability_rows=probability_rows,
            group_ids=evaluation_result["metadata"]["group_id"],
            is_id_flags=evaluation_result["metadata"]["is_id"],
            is_ood_flags=evaluation_result["metadata"]["is_ood"],
            logits_rows=logits_rows,
        )
        return _augment_prediction_frame(records, perturbation_samples)

    return SavedRunScorer(
        model_name=str(metadata["model_name"]),
        source_run_id=str(metadata["run_id"]),
        score_records=score_records,
    )


def load_saved_run_scorer(
    metadata: dict[str, Any],
    *,
    tokenizer_factory: TokenizerFactory | None = None,
    model_factory: ModelFactory | None = None,
) -> SavedRunScorer:
    """Load a scorer for one saved baseline or mitigation run."""
    model_name = str(metadata.get("model_name"))
    mitigation_method = metadata.get("mitigation_method")
    if model_name == "logistic_tfidf":
        return _logistic_scorer(metadata)
    if model_name == "distilbert":
        return _distilbert_scorer(
            metadata,
            tokenizer_factory=tokenizer_factory,
            model_factory=model_factory,
        )
    raise ValueError(
        f"Unsupported perturbation scoring model {model_name!r} "
        f"(mitigation_method={mitigation_method!r})"
    )


def score_perturbation_suite(
    suite_records: list[dict[str, Any]],
    *,
    run_id: str,
    scorer: SavedRunScorer,
) -> pd.DataFrame:
    """Score a perturbation suite through one loaded saved-run scorer."""
    return scorer.score_records(suite_records, run_id)
