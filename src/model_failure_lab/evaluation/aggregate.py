"""Aggregate saved-run evaluation metrics."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)

from model_failure_lab.models.export import REQUIRED_PREDICTION_COLUMNS


def _validate_prediction_frame(frame: pd.DataFrame) -> pd.DataFrame:
    missing_columns = [
        column for column in REQUIRED_PREDICTION_COLUMNS if column not in frame.columns
    ]
    if missing_columns:
        missing_text = ", ".join(missing_columns)
        raise ValueError(f"Prediction frame is missing required columns: {missing_text}")
    if frame.empty:
        raise ValueError("Prediction frame must contain at least one row")
    return frame.copy()


def _safe_auroc(true_labels: pd.Series, probability_positive: pd.Series) -> float | None:
    try:
        return float(roc_auc_score(true_labels, probability_positive))
    except ValueError:
        return None


def compute_aggregate_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    """Compute aggregate classification metrics from saved prediction rows."""
    normalized_frame = _validate_prediction_frame(frame)
    true_labels = normalized_frame["true_label"].astype(int)
    predicted_labels = normalized_frame["pred_label"].astype(int)
    probability_positive = normalized_frame["prob_1"].astype(float)
    probability_negative = normalized_frame["prob_0"].astype(float)
    confidence = normalized_frame[["prob_0", "prob_1"]].astype(float).max(axis=1)

    precision, recall, binary_f1, _ = precision_recall_fscore_support(
        true_labels,
        predicted_labels,
        average="binary",
        zero_division=0,
    )
    confusion = confusion_matrix(true_labels, predicted_labels, labels=[0, 1])
    tn, fp, fn, tp = (int(value) for value in confusion.ravel())

    return {
        "sample_count": int(len(normalized_frame)),
        "support": int(len(normalized_frame)),
        "accuracy": float(accuracy_score(true_labels, predicted_labels)),
        "macro_f1": float(
            f1_score(true_labels, predicted_labels, average="macro", zero_division=0)
        ),
        "precision": float(precision),
        "recall": float(recall),
        "binary_f1": float(binary_f1),
        "auroc": _safe_auroc(true_labels, probability_positive),
        "avg_predicted_score": float(probability_positive.mean()),
        "avg_negative_score": float(probability_negative.mean()),
        "mean_confidence": float(confidence.mean()),
        "score_std": float(np.std(probability_positive, ddof=0)),
        "positive_label_rate": float(true_labels.mean()),
        "positive_prediction_rate": float(predicted_labels.mean()),
        "confusion_matrix": {
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp,
        },
    }


def _build_metric_row(frame: pd.DataFrame, *, slice_type: str, slice_name: str) -> dict[str, Any]:
    metrics = compute_aggregate_metrics(frame)
    confusion = metrics.pop("confusion_matrix")
    return {
        "slice_type": slice_type,
        "slice_name": slice_name,
        "sample_count": metrics["sample_count"],
        "support": metrics["support"],
        "accuracy": metrics["accuracy"],
        "macro_f1": metrics["macro_f1"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "binary_f1": metrics["binary_f1"],
        "auroc": metrics["auroc"],
        "avg_predicted_score": metrics["avg_predicted_score"],
        "avg_negative_score": metrics["avg_negative_score"],
        "mean_confidence": metrics["mean_confidence"],
        "score_std": metrics["score_std"],
        "positive_label_rate": metrics["positive_label_rate"],
        "positive_prediction_rate": metrics["positive_prediction_rate"],
        "tn": confusion["tn"],
        "fp": confusion["fp"],
        "fn": confusion["fn"],
        "tp": confusion["tp"],
    }


def build_split_metrics_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Build aggregate rows for overall, ID/OOD, and explicit split slices."""
    normalized_frame = _validate_prediction_frame(frame)
    rows = [_build_metric_row(normalized_frame, slice_type="overall", slice_name="overall")]

    if normalized_frame["is_id"].astype(bool).any():
        rows.append(
            _build_metric_row(
                normalized_frame.loc[normalized_frame["is_id"].astype(bool)],
                slice_type="distribution",
                slice_name="id",
            )
        )
    if normalized_frame["is_ood"].astype(bool).any():
        rows.append(
            _build_metric_row(
                normalized_frame.loc[normalized_frame["is_ood"].astype(bool)],
                slice_type="distribution",
                slice_name="ood",
            )
        )

    for split_name in pd.unique(normalized_frame["split"]):
        split_frame = normalized_frame.loc[normalized_frame["split"] == split_name]
        rows.append(
            _build_metric_row(
                split_frame,
                slice_type="split",
                slice_name=str(split_name),
            )
        )

    return rows
