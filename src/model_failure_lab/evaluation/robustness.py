"""Robustness-gap and ID/OOD comparison helpers."""

from __future__ import annotations

from typing import Any, Iterable

_ROBUSTNESS_METRICS = ("accuracy", "macro_f1", "auroc")


def _index_rows_by_name(split_metric_rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("slice_name")): dict(row)
        for row in split_metric_rows
    }


def build_id_ood_comparison(split_metric_rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build explicit ID-vs-OOD metric comparison rows."""
    rows_by_name = _index_rows_by_name(split_metric_rows)
    id_row = rows_by_name.get("id")
    ood_row = rows_by_name.get("ood")

    comparison_rows: list[dict[str, Any]] = []
    for metric_name in _ROBUSTNESS_METRICS:
        id_value = None if id_row is None else id_row.get(metric_name)
        ood_value = None if ood_row is None else ood_row.get(metric_name)
        delta = None
        if id_value is not None and ood_value is not None:
            delta = round(float(id_value) - float(ood_value), 10)

        comparison_rows.append(
            {
                "metric": metric_name,
                "id_value": id_value,
                "ood_value": ood_value,
                "delta": delta,
                "id_support": None if id_row is None else int(id_row.get("support", 0)),
                "ood_support": None if ood_row is None else int(ood_row.get("support", 0)),
            }
        )

    return comparison_rows


def compute_robustness_gaps(split_metric_rows: Iterable[dict[str, Any]]) -> dict[str, float | None]:
    """Compute the headline robustness-gap scalars from ID and OOD metric rows."""
    comparison_rows = build_id_ood_comparison(split_metric_rows)
    gaps = {
        "robustness_gap_accuracy": None,
        "robustness_gap_f1": None,
        "robustness_gap_auroc": None,
    }
    key_map = {
        "accuracy": "robustness_gap_accuracy",
        "macro_f1": "robustness_gap_f1",
        "auroc": "robustness_gap_auroc",
    }
    for row in comparison_rows:
        metric_name = str(row["metric"])
        gaps[key_map[metric_name]] = None if row["delta"] is None else float(row["delta"])
    return gaps
