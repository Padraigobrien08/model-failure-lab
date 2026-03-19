"""Shared evaluator-facing prediction export helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from model_failure_lab.utils.paths import build_prediction_artifact_path

REQUIRED_PREDICTION_COLUMNS = [
    "run_id",
    "sample_id",
    "split",
    "model_name",
    "true_label",
    "pred_label",
    "pred_score",
    "prob_0",
    "prob_1",
    "is_correct",
    "group_id",
    "is_id",
    "is_ood",
]
OPTIONAL_PREDICTION_COLUMNS = ["logit_0", "logit_1", "confidence", "margin"]


def build_prediction_records(
    *,
    run_id: str,
    model_name: str,
    sample_ids: list[str],
    splits: list[str],
    true_labels: list[int],
    predicted_labels: list[int],
    probability_rows: list[list[float]],
    group_ids: list[str],
    is_id_flags: list[bool],
    is_ood_flags: list[bool],
    logits_rows: list[list[float]] | None = None,
) -> list[dict[str, Any]]:
    """Build the shared evaluator-facing prediction record contract."""
    records: list[dict[str, Any]] = []
    for index, sample_id in enumerate(sample_ids):
        record: dict[str, Any] = {
            "run_id": run_id,
            "sample_id": sample_id,
            "split": splits[index],
            "model_name": model_name,
            "true_label": int(true_labels[index]),
            "pred_label": int(predicted_labels[index]),
            "pred_score": float(probability_rows[index][1]),
            "prob_0": float(probability_rows[index][0]),
            "prob_1": float(probability_rows[index][1]),
            "is_correct": int(predicted_labels[index]) == int(true_labels[index]),
            "group_id": group_ids[index],
            "is_id": bool(is_id_flags[index]),
            "is_ood": bool(is_ood_flags[index]),
        }
        if logits_rows is not None:
            record["logit_0"] = float(logits_rows[index][0])
            record["logit_1"] = float(logits_rows[index][1])
        records.append(record)
    return records


def write_prediction_exports(
    run_dir: Path,
    split_records: dict[str, list[dict[str, Any]]],
) -> dict[str, Path]:
    """Write split-specific parquet files with a stable shared schema."""
    written_paths: dict[str, Path] = {}
    for split, records in split_records.items():
        prediction_path = build_prediction_artifact_path(run_dir, split)
        prediction_path.parent.mkdir(parents=True, exist_ok=True)

        frame = pd.DataFrame(records)
        missing_columns = [
            column for column in REQUIRED_PREDICTION_COLUMNS if column not in frame.columns
        ]
        if missing_columns:
            missing_text = ", ".join(missing_columns)
            raise ValueError(f"Prediction export is missing required columns: {missing_text}")

        ordered_columns = list(REQUIRED_PREDICTION_COLUMNS)
        ordered_columns.extend(
            column for column in OPTIONAL_PREDICTION_COLUMNS if column in frame.columns
        )
        ordered_columns.extend(
            column
            for column in frame.columns
            if column not in ordered_columns
        )
        frame.loc[:, ordered_columns].to_parquet(prediction_path, index=False)
        written_paths[str(split)] = prediction_path
    return written_paths
