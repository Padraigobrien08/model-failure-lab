"""Summary builders for perturbation stress-test bundles."""

from __future__ import annotations

from typing import Any

import pandas as pd

from model_failure_lab.models.common import compute_binary_classification_metrics


def _metric_summary(frame: pd.DataFrame) -> dict[str, float | None]:
    if frame.empty:
        return {"accuracy": None, "macro_f1": None, "auroc": None}
    metrics = compute_binary_classification_metrics(
        true_labels=frame["true_label"].astype(int).tolist(),
        predicted_labels=frame["pred_label"].astype(int).tolist(),
        probability_positive=frame["prob_1"].astype(float).tolist(),
    )
    return {
        "accuracy": metrics.get("accuracy"),
        "macro_f1": metrics.get("macro_f1"),
        "auroc": metrics.get("auroc"),
    }


def _delta(clean_value: float | None, perturbed_value: float | None) -> float | None:
    if clean_value is None or perturbed_value is None:
        return None
    return float(clean_value) - float(perturbed_value)


def _summary_row(
    *,
    row_type: str,
    row_name: str,
    clean_frame: pd.DataFrame,
    perturbed_frame: pd.DataFrame,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    clean_metrics = _metric_summary(clean_frame)
    perturbed_metrics = _metric_summary(perturbed_frame)
    payload: dict[str, Any] = {
        "row_type": row_type,
        "row_name": row_name,
        "source_sample_count": int(clean_frame["sample_id"].astype(str).nunique()),
        "perturbed_sample_count": int(len(perturbed_frame)),
        "clean_accuracy": clean_metrics["accuracy"],
        "perturbed_accuracy": perturbed_metrics["accuracy"],
        "accuracy_drop": _delta(clean_metrics["accuracy"], perturbed_metrics["accuracy"]),
        "clean_macro_f1": clean_metrics["macro_f1"],
        "perturbed_macro_f1": perturbed_metrics["macro_f1"],
        "macro_f1_drop": _delta(clean_metrics["macro_f1"], perturbed_metrics["macro_f1"]),
        "clean_auroc": clean_metrics["auroc"],
        "perturbed_auroc": perturbed_metrics["auroc"],
        "auroc_drop": _delta(clean_metrics["auroc"], perturbed_metrics["auroc"]),
    }
    if extra:
        payload.update(extra)
    return payload


def build_suite_summary(clean_frame: pd.DataFrame, perturbed_frame: pd.DataFrame) -> pd.DataFrame:
    """Return the overall clean-versus-perturbed summary table."""
    return pd.DataFrame(
        [
            _summary_row(
                row_type="suite",
                row_name="overall",
                clean_frame=clean_frame,
                perturbed_frame=perturbed_frame,
            )
        ]
    )


def build_family_summary(clean_frame: pd.DataFrame, perturbed_frame: pd.DataFrame) -> pd.DataFrame:
    """Return one summary row per perturbation family."""
    rows: list[dict[str, Any]] = []
    for family, family_frame in sorted(
        perturbed_frame.groupby("perturbation_family"),
        key=lambda item: str(item[0]),
    ):
        source_ids = family_frame["source_sample_id"].astype(str).unique().tolist()
        clean_subset = clean_frame.loc[clean_frame["sample_id"].astype(str).isin(source_ids)].copy()
        rows.append(
            _summary_row(
                row_type="family",
                row_name=str(family),
                clean_frame=clean_subset,
                perturbed_frame=family_frame,
                extra={"perturbation_family": str(family)},
            )
        )
    return pd.DataFrame(rows)


def build_severity_summary(
    clean_frame: pd.DataFrame,
    perturbed_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Return one summary row per severity level."""
    rows: list[dict[str, Any]] = []
    severity_order = {"low": 0, "medium": 1, "high": 2}
    for severity, severity_frame in sorted(
        perturbed_frame.groupby("severity"),
        key=lambda item: (severity_order.get(str(item[0]), 99), str(item[0])),
    ):
        source_ids = severity_frame["source_sample_id"].astype(str).unique().tolist()
        clean_subset = clean_frame.loc[clean_frame["sample_id"].astype(str).isin(source_ids)].copy()
        rows.append(
            _summary_row(
                row_type="severity",
                row_name=str(severity),
                clean_frame=clean_subset,
                perturbed_frame=severity_frame,
                extra={"severity": str(severity)},
            )
        )
    return pd.DataFrame(rows)


def build_family_severity_matrix(
    clean_frame: pd.DataFrame,
    perturbed_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Return one summary row per family-by-severity slice."""
    rows: list[dict[str, Any]] = []
    grouped = perturbed_frame.groupby(["perturbation_family", "severity"])
    severity_order = {"low": 0, "medium": 1, "high": 2}
    for (family, severity), slice_frame in sorted(
        grouped,
        key=lambda item: (
            str(item[0][0]),
            severity_order.get(str(item[0][1]), 99),
            str(item[0][1]),
        ),
    ):
        source_ids = slice_frame["source_sample_id"].astype(str).unique().tolist()
        clean_subset = clean_frame.loc[clean_frame["sample_id"].astype(str).isin(source_ids)].copy()
        rows.append(
            _summary_row(
                row_type="family_severity",
                row_name=f"{family}:{severity}",
                clean_frame=clean_subset,
                perturbed_frame=slice_frame,
                extra={
                    "perturbation_family": str(family),
                    "severity": str(severity),
                },
            )
        )
    return pd.DataFrame(rows)


def build_source_delta_summary(
    clean_frame: pd.DataFrame,
    perturbed_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Return one delta row per source sample."""
    clean_lookup = clean_frame.set_index("sample_id", drop=False)
    rows: list[dict[str, Any]] = []
    for source_sample_id, source_frame in sorted(
        perturbed_frame.groupby("source_sample_id"),
        key=lambda item: str(item[0]),
    ):
        clean_row = clean_lookup.loc[str(source_sample_id)]
        if isinstance(clean_row, pd.DataFrame):
            clean_row = clean_row.iloc[0]
        rows.append(
            {
                "source_sample_id": str(source_sample_id),
                "true_label": int(clean_row["true_label"]),
                "clean_pred_label": int(clean_row["pred_label"]),
                "clean_pred_score": float(clean_row["pred_score"]),
                "avg_perturbed_pred_score": float(source_frame["pred_score"].astype(float).mean()),
                "max_perturbed_pred_score": float(source_frame["pred_score"].astype(float).max()),
                "min_perturbed_pred_score": float(source_frame["pred_score"].astype(float).min()),
                "mean_score_drop": float(
                    float(clean_row["pred_score"]) - source_frame["pred_score"].astype(float).mean()
                ),
                "clean_correct": bool(clean_row["is_correct"]),
                "perturbed_correct_count": int(source_frame["is_correct"].astype(int).sum()),
                "perturbed_sample_count": int(len(source_frame)),
            }
        )
    return pd.DataFrame(rows)
