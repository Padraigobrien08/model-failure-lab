"""Post-hoc DistilBERT temperature scaling built on saved baseline artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from model_failure_lab.data import CanonicalDataset, prepare_transformer_adapter
from model_failure_lab.models.common import (
    compute_binary_classification_metrics,
    load_baseline_canonical_dataset,
    set_random_seed,
)
from model_failure_lab.models.distilbert import (
    TokenizedTextDataset,
    _build_collate_fn,
    _device_and_precision,
    _run_validation,
    build_sequence_classifier,
    build_tokenizer,
)
from model_failure_lab.models.export import build_prediction_records, write_prediction_exports

from .common import load_parent_run_context, validate_distilbert_parent_run

DatasetLoader = Callable[..., CanonicalDataset]
TokenizerFactory = Callable[[str], Any]
ModelFactory = Callable[[str, int], torch.nn.Module]

_LOGIT_COLUMNS = ["logit_0", "logit_1"]


@dataclass(slots=True)
class TemperatureScalingArtifacts:
    """Artifacts produced by a completed temperature-scaling mitigation run."""

    metrics_payload: dict[str, Any]
    prediction_paths: dict[str, Path]
    checkpoint_dir: Path
    temperature_scaler_path: Path
    selected_checkpoint_path: Path
    learned_temperature: float
    calibration_fitting_split: str
    logit_provenance: dict[str, str]


def _prediction_path_for_split(parent_metadata: dict[str, Any], split: str) -> Path | None:
    artifact_paths = dict(parent_metadata.get("artifact_paths", {}))
    predictions = artifact_paths.get("predictions")
    if isinstance(predictions, dict):
        raw_path = predictions.get(split)
        if raw_path:
            return Path(str(raw_path))
    return None


def _selected_checkpoint_path(parent_metadata: dict[str, Any]) -> Path:
    artifact_paths = dict(parent_metadata.get("artifact_paths", {}))
    raw_path = artifact_paths.get("selected_checkpoint")
    if raw_path:
        return Path(str(raw_path))

    checkpoint_root = artifact_paths.get("checkpoint")
    if checkpoint_root:
        checkpoint_path = Path(str(checkpoint_root)) / "best_model.pt"
        if checkpoint_path.exists():
            return checkpoint_path

    raise ValueError("Parent baseline metadata is missing artifact_paths.selected_checkpoint")


def _require_logits(frame: pd.DataFrame, *, split: str) -> pd.DataFrame:
    missing_columns = [column for column in _LOGIT_COLUMNS if column not in frame.columns]
    if missing_columns:
        missing_text = ", ".join(missing_columns)
        raise ValueError(
            f"Saved predictions for split {split!r} are missing required logit columns: "
            f"{missing_text}"
        )
    return frame


def _load_saved_prediction_frame(
    parent_metadata: dict[str, Any],
    split: str,
) -> pd.DataFrame | None:
    prediction_path = _prediction_path_for_split(parent_metadata, split)
    if prediction_path is None or not prediction_path.exists():
        return None
    return pd.read_parquet(prediction_path)


def _regenerate_prediction_frame(
    *,
    parent_context: dict[str, Any],
    child_run_id: str,
    split: str,
    checkpoint_path: Path,
    dataset_loader: DatasetLoader,
    tokenizer_factory: TokenizerFactory,
    model_factory: ModelFactory,
) -> pd.DataFrame:
    parent_config = dict(parent_context["resolved_config"])
    dataset = dataset_loader(parent_config, download=True)
    model_config = dict(parent_config.get("model", {}))
    train_config = dict(parent_config.get("train", {}))

    pretrained_name = str(model_config.get("pretrained_name", "distilbert-base-uncased"))
    max_length = int(model_config.get("max_length", 256))
    tokenizer = tokenizer_factory(pretrained_name)
    adapter_view = prepare_transformer_adapter(
        dataset.samples,
        split=split,
        tokenizer_name=pretrained_name,
        max_length=max_length,
    )
    tokenized_dataset = TokenizedTextDataset(
        adapter_view.records,
        tokenizer,
        max_length=max_length,
    )
    pad_token_id = int(getattr(tokenizer, "pad_token_id", 0) or 0)
    batch_size_config = dict(model_config.get("batch_size", {}))
    eval_batch_size = int(batch_size_config.get("eval", train_config.get("eval_batch_size", 32)))
    dataloader = DataLoader(
        tokenized_dataset,
        batch_size=eval_batch_size,
        shuffle=False,
        num_workers=int(train_config.get("num_workers", 0)),
        collate_fn=_build_collate_fn(pad_token_id),
    )

    model = model_factory(pretrained_name, 2)
    device, _ = _device_and_precision(parent_config)
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.to(device)
    evaluation_result = _run_validation(model, dataloader, device=device)

    return pd.DataFrame(
        build_prediction_records(
            run_id=child_run_id,
            model_name=str(parent_config["model_name"]),
            sample_ids=evaluation_result["metadata"]["sample_id"],
            splits=evaluation_result["metadata"]["split"],
            true_labels=evaluation_result["labels"],
            predicted_labels=evaluation_result["predictions"],
            probability_rows=evaluation_result["probabilities"],
            group_ids=evaluation_result["metadata"]["group_id"],
            is_id_flags=evaluation_result["metadata"]["is_id"],
            is_ood_flags=evaluation_result["metadata"]["is_ood"],
            logits_rows=evaluation_result["logits"],
        )
    )


def _load_logits_frame(
    *,
    parent_context: dict[str, Any],
    child_run_id: str,
    split: str,
    allow_checkpoint_regeneration: bool,
    selected_checkpoint_path: Path,
    dataset_loader: DatasetLoader,
    tokenizer_factory: TokenizerFactory,
    model_factory: ModelFactory,
) -> tuple[pd.DataFrame, str]:
    parent_metadata = dict(parent_context["metadata"])
    saved_frame = _load_saved_prediction_frame(parent_metadata, split)
    if saved_frame is not None:
        return _require_logits(saved_frame, split=split), "saved_predictions"

    if not allow_checkpoint_regeneration:
        raise FileNotFoundError(
            f"Saved predictions with logits were not found for split {split!r}, and "
            "temperature_scaling.allow_checkpoint_regeneration is false."
        )

    regenerated = _regenerate_prediction_frame(
        parent_context=parent_context,
        child_run_id=child_run_id,
        split=split,
        checkpoint_path=selected_checkpoint_path,
        dataset_loader=dataset_loader,
        tokenizer_factory=tokenizer_factory,
        model_factory=model_factory,
    )
    return _require_logits(regenerated, split=split), "checkpoint_regeneration"


def fit_temperature_scaler(
    validation_logits: torch.Tensor | list[list[float]],
    validation_labels: torch.Tensor | list[int],
    *,
    objective: str = "nll",
    max_iter: int = 50,
) -> float:
    """Fit one positive scalar temperature on validation logits only."""
    if objective != "nll":
        raise ValueError(f"Unsupported temperature scaling objective: {objective}")

    logits_tensor = torch.as_tensor(validation_logits, dtype=torch.float32)
    labels_tensor = torch.as_tensor(validation_labels, dtype=torch.long)
    if logits_tensor.ndim != 2 or logits_tensor.shape[1] != 2:
        raise ValueError("validation_logits must be shaped as [n_samples, 2]")
    if labels_tensor.ndim != 1 or labels_tensor.shape[0] != logits_tensor.shape[0]:
        raise ValueError("validation_labels must align to validation_logits")

    log_temperature = torch.nn.Parameter(torch.zeros(1, dtype=torch.float32))
    optimizer = torch.optim.LBFGS(
        [log_temperature],
        lr=0.1,
        max_iter=max_iter,
        line_search_fn="strong_wolfe",
    )

    def closure() -> torch.Tensor:
        optimizer.zero_grad()
        scaled_logits = logits_tensor / log_temperature.exp().clamp_min(1.0e-6)
        loss = F.cross_entropy(scaled_logits, labels_tensor)
        loss.backward()
        return loss

    optimizer.step(closure)
    learned_temperature = float(log_temperature.detach().exp().item())
    if not torch.isfinite(torch.tensor(learned_temperature)):
        raise RuntimeError("Temperature scaling produced a non-finite temperature.")
    return max(learned_temperature, 1.0e-6)


def apply_temperature_scaling(
    logits: torch.Tensor | list[list[float]],
    temperature: float,
) -> torch.Tensor:
    """Return temperature-scaled logits for probability recalibration."""
    logits_tensor = torch.as_tensor(logits, dtype=torch.float32)
    return logits_tensor / max(float(temperature), 1.0e-6)


def _build_calibrated_records(
    frame: pd.DataFrame,
    *,
    run_id: str,
    model_name: str,
    temperature: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scaled_logits = apply_temperature_scaling(frame.loc[:, _LOGIT_COLUMNS].to_numpy(), temperature)
    probabilities = torch.softmax(scaled_logits, dim=-1)
    predictions = torch.argmax(probabilities, dim=-1)
    true_labels = frame["true_label"].astype(int).tolist()

    validation_metrics = compute_binary_classification_metrics(
        true_labels=true_labels,
        predicted_labels=predictions.tolist(),
        probability_positive=probabilities[:, 1].tolist(),
    )
    validation_metrics["loss"] = float(
        F.cross_entropy(
            scaled_logits,
            torch.tensor(true_labels, dtype=torch.long),
        ).item()
    )

    records = build_prediction_records(
        run_id=run_id,
        model_name=model_name,
        sample_ids=frame["sample_id"].astype(str).tolist(),
        splits=frame["split"].astype(str).tolist(),
        true_labels=true_labels,
        predicted_labels=predictions.tolist(),
        probability_rows=probabilities.tolist(),
        group_ids=frame["group_id"].astype(str).tolist(),
        is_id_flags=frame["is_id"].astype(bool).tolist(),
        is_ood_flags=frame["is_ood"].astype(bool).tolist(),
        logits_rows=scaled_logits.tolist(),
    )
    return records, validation_metrics


def run_temperature_scaling(
    config: dict[str, Any],
    run_dir: Path,
    *,
    dataset_loader: DatasetLoader | None = None,
    tokenizer_factory: TokenizerFactory | None = None,
    model_factory: ModelFactory | None = None,
) -> TemperatureScalingArtifacts:
    """Fit and apply temperature scaling using validation logits from the parent run."""
    set_random_seed(int(config["seed"]))
    parent_run_id = config.get("parent_run_id")
    if parent_run_id is None:
        raise ValueError("Temperature scaling requires config.parent_run_id")

    parent_context = validate_distilbert_parent_run(load_parent_run_context(str(parent_run_id)))
    mitigation_config = dict(config.get("mitigation_config") or config.get("mitigation") or {})
    scaling_config = dict(mitigation_config.get("temperature_scaling", {}))
    fitting_split = str(scaling_config.get("fitting_split", "validation"))
    objective = str(scaling_config.get("objective", "nll"))
    apply_to_splits = [str(split) for split in scaling_config.get("apply_to_splits", [])]
    allow_checkpoint_regeneration = bool(
        scaling_config.get("allow_checkpoint_regeneration", False)
    )

    resolved_dataset_loader = dataset_loader or load_baseline_canonical_dataset
    resolved_tokenizer_factory = tokenizer_factory or build_tokenizer
    resolved_model_factory = model_factory or build_sequence_classifier
    selected_checkpoint_path = _selected_checkpoint_path(parent_context["metadata"])

    requested_splits = list(dict.fromkeys([*apply_to_splits, fitting_split]))
    split_frames: dict[str, pd.DataFrame] = {}
    logit_provenance: dict[str, str] = {}
    for split in requested_splits:
        split_frame, provenance = _load_logits_frame(
            parent_context=parent_context,
            child_run_id=str(config["run_id"]),
            split=split,
            allow_checkpoint_regeneration=allow_checkpoint_regeneration,
            selected_checkpoint_path=selected_checkpoint_path,
            dataset_loader=resolved_dataset_loader,
            tokenizer_factory=resolved_tokenizer_factory,
            model_factory=resolved_model_factory,
        )
        split_frames[split] = split_frame
        logit_provenance[split] = provenance

    fitting_frame = split_frames[fitting_split]
    learned_temperature = fit_temperature_scaler(
        fitting_frame.loc[:, _LOGIT_COLUMNS].to_numpy(),
        fitting_frame["true_label"].astype(int).tolist(),
        objective=objective,
    )

    prediction_records: dict[str, list[dict[str, Any]]] = {}
    validation_metrics: dict[str, Any] | None = None
    for split in apply_to_splits:
        records, split_metrics = _build_calibrated_records(
            split_frames[split],
            run_id=str(config["run_id"]),
            model_name=str(config["model_name"]),
            temperature=learned_temperature,
        )
        prediction_records[split] = records
        if split == fitting_split:
            validation_metrics = split_metrics

    prediction_paths = write_prediction_exports(run_dir, prediction_records)

    checkpoint_dir = run_dir / "checkpoint"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    temperature_scaler_path = checkpoint_dir / "temperature_scaler.json"
    temperature_scaler_payload = {
        "parent_run_id": str(parent_run_id),
        "selected_checkpoint": str(selected_checkpoint_path),
        "learned_temperature": learned_temperature,
        "fitting_split": fitting_split,
        "objective": objective,
        "apply_to_splits": apply_to_splits,
        "logit_provenance": logit_provenance,
    }
    temperature_scaler_path.write_text(
        json.dumps(temperature_scaler_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    if validation_metrics is None:
        raise RuntimeError(
            "Temperature scaling did not produce validation metrics for the fitting split."
        )

    eval_config = dict(config.get("eval", {}))
    primary_metric_name = str(eval_config.get("primary_metric", "macro_f1"))
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
        "learned_temperature": learned_temperature,
        "calibration_fitting_split": fitting_split,
        "logit_provenance": logit_provenance,
        "selected_checkpoint": {
            "path": str(selected_checkpoint_path),
            "source": "parent_selected_checkpoint",
        },
    }

    return TemperatureScalingArtifacts(
        metrics_payload=metrics_payload,
        prediction_paths=prediction_paths,
        checkpoint_dir=checkpoint_dir,
        temperature_scaler_path=temperature_scaler_path,
        selected_checkpoint_path=selected_checkpoint_path,
        learned_temperature=learned_temperature,
        calibration_fitting_split=fitting_split,
        logit_provenance=logit_provenance,
    )
