"""Helpers for loading saved prediction artifacts for evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from model_failure_lab.models.export import REQUIRED_PREDICTION_COLUMNS
from model_failure_lab.utils.paths import find_run_metadata_path

_SPLIT_ALIASES = {
    "train": "train",
    "validation": "validation",
    "val": "validation",
    "test": "test",
    "id_test": "id_test",
    "ood_test": "ood_test",
}


def normalize_prediction_split(split: str) -> str:
    """Return the canonical split name used by saved prediction bundles."""
    normalized = str(split).strip().lower()
    return _SPLIT_ALIASES.get(normalized, normalized)


def select_prediction_splits(
    available_splits: Iterable[str],
    requested_splits: Iterable[str] | None = None,
) -> list[str]:
    """Return the selected prediction splits while honoring CLI-style aliases."""
    available_map = {
        normalize_prediction_split(split): str(split)
        for split in available_splits
    }
    if requested_splits is None:
        return list(available_map.values())

    selected_splits: list[str] = []
    missing_splits: list[str] = []
    for requested_split in requested_splits:
        normalized_requested = normalize_prediction_split(str(requested_split))
        resolved = available_map.get(normalized_requested)
        if resolved is None:
            missing_splits.append(str(requested_split))
            continue
        if resolved not in selected_splits:
            selected_splits.append(resolved)

    if missing_splits:
        missing_text = ", ".join(sorted(missing_splits))
        available_text = ", ".join(sorted(available_map))
        raise ValueError(
            f"Requested prediction splits are unavailable: {missing_text}. "
            f"Available splits: {available_text}"
        )

    return selected_splits


def _load_metadata(
    metadata_or_path: dict[str, Any] | Path | str,
) -> tuple[dict[str, Any], Path | None]:
    if isinstance(metadata_or_path, dict):
        metadata = dict(metadata_or_path)
        run_id = metadata.get("run_id")
        if run_id is not None:
            try:
                return metadata, find_run_metadata_path(str(run_id))
            except (FileNotFoundError, ValueError):
                return metadata, None
        return metadata, None

    metadata_path = Path(metadata_or_path)
    return json.loads(metadata_path.read_text(encoding="utf-8")), metadata_path


def _relocate_prediction_path(prediction_path: Path, metadata_path: Path | None) -> Path:
    if prediction_path.exists() or metadata_path is None:
        return prediction_path

    run_dir = metadata_path.parent
    relocated_path = run_dir / prediction_path.name
    if relocated_path.exists():
        return relocated_path
    return prediction_path


def _resolve_prediction_paths(
    metadata: dict[str, Any],
    *,
    metadata_path: Path | None = None,
) -> dict[str, Path]:
    artifact_paths = metadata.get("artifact_paths", {})
    prediction_paths = artifact_paths.get("predictions")
    if isinstance(prediction_paths, dict) and prediction_paths:
        return {
            str(split): _relocate_prediction_path(Path(path), metadata_path)
            for split, path in prediction_paths.items()
        }
    if isinstance(prediction_paths, str) and prediction_paths:
        return {
            "predictions": _relocate_prediction_path(Path(prediction_paths), metadata_path)
        }
    raise ValueError("Run metadata does not contain saved prediction artifact paths")


def load_saved_predictions(
    metadata_or_path: dict[str, Any] | Path | str,
    *,
    splits: Iterable[str] | None = None,
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Load saved split-specific prediction parquet artifacts into one evaluation frame."""
    metadata, metadata_path = _load_metadata(metadata_or_path)
    prediction_paths = _resolve_prediction_paths(metadata, metadata_path=metadata_path)
    selected_splits = select_prediction_splits(prediction_paths, splits)

    frames: list[pd.DataFrame] = []
    for split in selected_splits:
        prediction_path = prediction_paths[split]
        if not prediction_path.exists():
            raise FileNotFoundError(
                f"Prediction artifact for split {split!r} was not found: {prediction_path}"
            )
        frame = pd.read_parquet(prediction_path)
        missing_columns = [
            column for column in REQUIRED_PREDICTION_COLUMNS if column not in frame.columns
        ]
        if missing_columns:
            missing_text = ", ".join(missing_columns)
            raise ValueError(
                f"Prediction artifact for split {split!r} is missing required columns: "
                f"{missing_text}"
            )
        frames.append(frame)

    if not frames:
        raise ValueError("No prediction artifacts were selected for evaluation")

    return metadata, pd.concat(frames, ignore_index=True, sort=False)
