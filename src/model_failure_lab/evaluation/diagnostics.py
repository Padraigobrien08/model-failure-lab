"""Diagnostic summaries for saved prediction artifacts."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _histogram_rows(values: pd.Series, *, bins: int) -> list[dict[str, float | int]]:
    edges = np.linspace(0.0, 1.0, bins + 1)
    counts, _ = np.histogram(values.to_numpy(), bins=edges)
    rows: list[dict[str, float | int]] = []
    for index, count in enumerate(counts):
        rows.append(
            {
                "bin_index": int(index),
                "bin_lower": float(edges[index]),
                "bin_upper": float(edges[index + 1]),
                "count": int(count),
            }
        )
    return rows


def _confidence_partition(values: pd.Series, *, bins: int) -> dict[str, Any]:
    if values.empty:
        return {
            "count": 0,
            "mean_confidence": None,
            "min_confidence": None,
            "max_confidence": None,
            "histogram": _histogram_rows(pd.Series(dtype=float), bins=bins),
        }

    return {
        "count": int(len(values)),
        "mean_confidence": float(values.mean()),
        "min_confidence": float(values.min()),
        "max_confidence": float(values.max()),
        "histogram": _histogram_rows(values, bins=bins),
    }


def build_confidence_summary(frame: pd.DataFrame, *, bins: int = 10) -> dict[str, Any]:
    """Summarize confidence for overall, ID, and OOD slices split by correctness."""
    confidence = frame[["prob_0", "prob_1"]].astype(float).max(axis=1)
    partitions = {
        "overall": frame.index,
        "id": frame.loc[frame["is_id"].astype(bool)].index,
        "ood": frame.loc[frame["is_ood"].astype(bool)].index,
    }
    summary: dict[str, Any] = {}

    for slice_name, index in partitions.items():
        slice_confidence = confidence.loc[index]
        slice_correct_mask = (
            frame.loc[index, "is_correct"].astype(bool)
            if len(index)
            else pd.Series(dtype=bool)
        )
        summary[slice_name] = {
            "all": _confidence_partition(slice_confidence, bins=bins),
            "correct": _confidence_partition(slice_confidence.loc[slice_correct_mask], bins=bins),
            "incorrect": _confidence_partition(
                slice_confidence.loc[~slice_correct_mask] if len(index) else pd.Series(dtype=float),
                bins=bins,
            ),
        }

    return summary


def build_diagnostics_payload(frame: pd.DataFrame) -> dict[str, Any]:
    """Build lightweight evaluation diagnostics from saved prediction rows."""
    probability_positive = frame["prob_1"].astype(float)

    return {
        "score_distribution": {
            "count": int(len(frame)),
            "mean": float(probability_positive.mean()),
            "min": float(probability_positive.min()),
            "max": float(probability_positive.max()),
            "std": float(np.std(probability_positive, ddof=0)),
        },
        "prediction_rate_by_split": [
            {
                "split": str(split_name),
                "support": int(len(split_frame)),
                "positive_prediction_rate": float(split_frame["pred_label"].astype(int).mean()),
            }
            for split_name, split_frame in frame.groupby("split", sort=True)
        ],
        "prediction_rate_by_group": [
            {
                "group_id": str(group_name),
                "support": int(len(group_frame)),
                "positive_prediction_rate": float(group_frame["pred_label"].astype(int).mean()),
            }
            for group_name, group_frame in frame.groupby("group_id", sort=True)
        ],
    }
