"""Calibration summaries for saved prediction artifacts."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss


def _bin_edges(probability_positive: pd.Series, *, n_bins: int, strategy: str) -> np.ndarray:
    if strategy == "uniform":
        return np.linspace(0.0, 1.0, n_bins + 1)
    if strategy == "quantile":
        edges = np.quantile(probability_positive.to_numpy(), np.linspace(0.0, 1.0, n_bins + 1))
        edges[0] = 0.0
        edges[-1] = 1.0
        return edges
    raise ValueError(f"Unsupported calibration binning strategy: {strategy}")


def build_calibration_bins(
    frame: pd.DataFrame,
    *,
    n_bins: int = 10,
    strategy: str = "uniform",
    slice_name: str,
) -> list[dict[str, Any]]:
    """Build fixed-edge calibration bin rows for one evaluation slice."""
    probability_positive = (
        frame["prob_1"].astype(float) if not frame.empty else pd.Series(dtype=float)
    )
    true_labels = frame["true_label"].astype(int) if not frame.empty else pd.Series(dtype=int)
    edges = (
        _bin_edges(probability_positive, n_bins=n_bins, strategy=strategy)
        if not frame.empty
        else np.linspace(0.0, 1.0, n_bins + 1)
    )

    rows: list[dict[str, Any]] = []
    for index in range(n_bins):
        lower = float(edges[index])
        upper = float(edges[index + 1])
        if frame.empty:
            mask = pd.Series(dtype=bool)
        elif index == n_bins - 1:
            mask = (probability_positive >= lower) & (probability_positive <= upper)
        else:
            mask = (probability_positive >= lower) & (probability_positive < upper)

        count = int(mask.sum()) if not frame.empty else 0
        if count:
            avg_confidence = float(probability_positive.loc[mask].mean())
            empirical_accuracy = float(true_labels.loc[mask].mean())
            calibration_gap = abs(empirical_accuracy - avg_confidence)
        else:
            avg_confidence = None
            empirical_accuracy = None
            calibration_gap = None

        rows.append(
            {
                "slice_name": slice_name,
                "bin_index": index,
                "bin_lower": lower,
                "bin_upper": upper,
                "count": count,
                "avg_confidence": avg_confidence,
                "empirical_accuracy": empirical_accuracy,
                "calibration_gap": calibration_gap,
            }
        )

    return rows


def _slice_frames(frame: pd.DataFrame) -> list[tuple[str, pd.DataFrame]]:
    return [
        ("overall", frame),
        ("id", frame.loc[frame["is_id"].astype(bool)]),
        ("ood", frame.loc[frame["is_ood"].astype(bool)]),
    ]


def compute_calibration_summary(
    frame: pd.DataFrame,
    *,
    n_bins: int = 10,
    strategy: str = "uniform",
) -> dict[str, list[dict[str, Any]]]:
    """Compute calibration summaries and fixed-edge bin rows for overall, ID, and OOD."""
    summary_rows: list[dict[str, Any]] = []
    bin_rows: list[dict[str, Any]] = []

    for slice_name, slice_frame in _slice_frames(frame):
        slice_bins = build_calibration_bins(
            slice_frame,
            n_bins=n_bins,
            strategy=strategy,
            slice_name=slice_name,
        )
        bin_rows.extend(slice_bins)

        probability_positive = (
            slice_frame["prob_1"].astype(float) if not slice_frame.empty else None
        )
        true_labels = slice_frame["true_label"].astype(int) if not slice_frame.empty else None
        non_empty_bins = [row for row in slice_bins if row["count"] > 0]
        ece = None
        brier_score = None
        if not slice_frame.empty:
            total_count = len(slice_frame)
            ece = float(
                sum(
                    (row["count"] / total_count) * float(row["calibration_gap"] or 0.0)
                    for row in non_empty_bins
                )
            )
            brier_score = float(brier_score_loss(true_labels, probability_positive))

        summary_rows.append(
            {
                "slice_name": slice_name,
                "sample_count": int(len(slice_frame)),
                "ece": ece,
                "brier_score": brier_score,
                "bin_count": int(n_bins),
                "non_empty_bin_count": int(len(non_empty_bins)),
            }
        )

    return {
        "summary_rows": summary_rows,
        "bin_rows": bin_rows,
    }
