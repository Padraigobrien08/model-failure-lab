"""Subgroup and worst-group evaluation helpers."""

from __future__ import annotations

from typing import Any, Iterable

import pandas as pd

from .aggregate import compute_aggregate_metrics

ATTRIBUTE_SLICE_PREFIX = "slice_"


def _resolve_attribute_columns(
    frame: pd.DataFrame,
    attribute_columns: Iterable[str] | None = None,
) -> list[str]:
    if attribute_columns is not None:
        return [str(column) for column in attribute_columns if str(column) in frame.columns]
    return [
        str(column)
        for column in frame.columns
        if str(column).startswith(ATTRIBUTE_SLICE_PREFIX)
    ]


def _build_subgroup_row(
    frame: pd.DataFrame,
    *,
    grouping_type: str,
    group_column: str,
    group_name: str,
    min_support: int,
    attribute_name: str | None = None,
) -> dict[str, Any]:
    metrics = compute_aggregate_metrics(frame)
    support = int(metrics["sample_count"])
    return {
        "grouping_type": grouping_type,
        "group_column": group_column,
        "group_name": group_name,
        "attribute_name": attribute_name,
        "support": support,
        "eligible_for_worst_group": support >= min_support,
        "accuracy": metrics["accuracy"],
        "macro_f1": metrics["macro_f1"],
        "binary_f1": metrics["binary_f1"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "auroc": metrics["auroc"],
        "avg_predicted_score": metrics["avg_predicted_score"],
        "mean_confidence": metrics["mean_confidence"],
        "error_rate": float(1.0 - metrics["accuracy"]),
        "minimum_support": min_support,
    }


def compute_subgroup_metrics(
    frame: pd.DataFrame,
    *,
    min_support: int = 100,
    group_column: str = "group_id",
    attribute_columns: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Compute subgroup rows for canonical groups and any explicit attribute slices."""
    if group_column not in frame.columns:
        raise ValueError(f"Prediction frame is missing subgroup column: {group_column}")

    rows: list[dict[str, Any]] = []

    for group_name in sorted(frame[group_column].dropna().astype(str).unique()):
        subgroup_frame = frame.loc[frame[group_column].astype(str) == group_name]
        rows.append(
            _build_subgroup_row(
                subgroup_frame,
                grouping_type="group_id",
                group_column=group_column,
                group_name=group_name,
                min_support=min_support,
            )
        )

    for attribute_column in _resolve_attribute_columns(frame, attribute_columns):
        truthy_mask = frame[attribute_column].fillna(0).astype(bool)
        if not truthy_mask.any():
            continue
        attribute_name = attribute_column.removeprefix(ATTRIBUTE_SLICE_PREFIX)
        attribute_frame = frame.loc[truthy_mask]
        rows.append(
            _build_subgroup_row(
                attribute_frame,
                grouping_type="attribute_slice",
                group_column=attribute_column,
                group_name=f"{attribute_name}=1",
                min_support=min_support,
                attribute_name=attribute_name,
            )
        )

    return rows


def build_worst_group_summary(
    subgroup_rows: Iterable[dict[str, Any]],
    *,
    min_support: int,
) -> dict[str, Any]:
    """Return the worst eligible group summary for headline reporting."""
    group_rows = [
        dict(row)
        for row in subgroup_rows
        if str(row.get("grouping_type")) == "group_id"
    ]
    eligible_rows = [row for row in group_rows if bool(row.get("eligible_for_worst_group"))]

    summary: dict[str, Any] = {
        "minimum_support": int(min_support),
        "reported_group_count": len(group_rows),
        "eligible_group_count": len(eligible_rows),
        "low_support_group_count": len(group_rows) - len(eligible_rows),
        "worst_group_f1": None,
        "worst_group_accuracy": None,
    }

    if not eligible_rows:
        return summary

    worst_f1_row = min(eligible_rows, key=lambda row: float(row.get("macro_f1", 0.0)))
    worst_accuracy_row = min(eligible_rows, key=lambda row: float(row.get("accuracy", 0.0)))
    summary["worst_group_f1"] = {
        "group_id": worst_f1_row["group_name"],
        "value": float(worst_f1_row["macro_f1"]),
        "support": int(worst_f1_row["support"]),
    }
    summary["worst_group_accuracy"] = {
        "group_id": worst_accuracy_row["group_name"],
        "value": float(worst_accuracy_row["accuracy"]),
        "support": int(worst_accuracy_row["support"]),
    }
    return summary
