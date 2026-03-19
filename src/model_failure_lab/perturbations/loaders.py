"""Loaders for clean source predictions and saved perturbation bundles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from model_failure_lab.evaluation.loaders import load_saved_predictions, normalize_prediction_split


def _load_metadata(metadata_or_path: dict[str, Any] | Path | str) -> dict[str, Any]:
    if isinstance(metadata_or_path, dict):
        return dict(metadata_or_path)
    metadata_path = Path(metadata_or_path)
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def load_clean_source_predictions(
    metadata_or_path: dict[str, Any] | Path | str,
    *,
    split: str,
    source_sample_ids: Iterable[str],
) -> pd.DataFrame:
    """Load clean saved predictions for one split and require all source IDs to exist."""
    normalized_split = normalize_prediction_split(split)
    _, prediction_frame = load_saved_predictions(metadata_or_path, splits=[normalized_split])
    requested_ids = [str(sample_id) for sample_id in source_sample_ids]
    filtered = prediction_frame.loc[
        prediction_frame["sample_id"].astype(str).isin(requested_ids)
    ].copy()
    missing_ids = sorted(set(requested_ids) - set(filtered["sample_id"].astype(str)))
    if missing_ids:
        missing_text = ", ".join(missing_ids[:10])
        raise ValueError(
            "Saved clean predictions are missing required source samples for perturbation "
            f"evaluation: {missing_text}"
        )
    return filtered.reset_index(drop=True)


def load_saved_perturbation_predictions(
    metadata_or_path: dict[str, Any] | Path | str,
) -> pd.DataFrame:
    """Load the saved perturbed prediction frame for one perturbation bundle."""
    metadata = _load_metadata(metadata_or_path)
    artifact_paths = dict(metadata.get("artifact_paths", {}))
    prediction_path = artifact_paths.get("predictions_perturbed_parquet")
    if not prediction_path:
        raise ValueError("Perturbation bundle metadata is missing predictions_perturbed_parquet")
    resolved_path = Path(str(prediction_path))
    if not resolved_path.exists():
        raise FileNotFoundError(f"Perturbed prediction artifact was not found: {resolved_path}")
    return pd.read_parquet(resolved_path)

