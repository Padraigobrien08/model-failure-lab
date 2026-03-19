"""Lineage-aware mitigation comparison helpers for saved evaluation bundles."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .discovery import ReportCandidate
from .selection import report_label

DEFAULT_COMPARISON_TOLERANCES = {
    "id_macro_f1_max_drop": 0.01,
    "overall_macro_f1_max_drop": 0.01,
    "ece_neutral_tolerance": 0.005,
}
MITIGATION_COMPARISON_COLUMNS = [
    "parent_eval_id",
    "mitigation_eval_id",
    "parent_label",
    "mitigation_label",
    "mitigation_method",
    "id_macro_f1_delta",
    "ood_macro_f1_delta",
    "robustness_gap_delta",
    "worst_group_f1_delta",
    "ece_delta",
    "brier_score_delta",
    "verdict",
]


def _candidate_metric(candidate: ReportCandidate, section: str, metric_name: str) -> float | None:
    payload = candidate.overall_metrics.get(section, {})
    if not isinstance(payload, dict):
        return None
    value = payload.get(metric_name)
    return None if value is None or pd.isna(value) else float(value)


def _headline_metric(candidate: ReportCandidate, metric_name: str) -> float | None:
    headline_metrics = candidate.overall_metrics.get("headline_metrics", {})
    if not isinstance(headline_metrics, dict):
        return None
    value = headline_metrics.get(metric_name)
    return None if value is None or pd.isna(value) else float(value)


def _overall_calibration_metric(candidate: ReportCandidate, metric_name: str) -> float | None:
    calibration_frame = candidate.calibration_summary.copy()
    if calibration_frame.empty or metric_name not in calibration_frame.columns:
        return None
    overall_rows = calibration_frame.loc[calibration_frame["slice_name"] == "overall"]
    if overall_rows.empty:
        return None
    value = overall_rows.iloc[0][metric_name]
    return None if value is None or pd.isna(value) else float(value)


def _metric_delta(child: float | None, parent: float | None) -> float | None:
    if child is None or parent is None:
        return None
    return float(child - parent)


def _resolve_comparison_tolerances(candidate: ReportCandidate) -> dict[str, float]:
    resolved = dict(DEFAULT_COMPARISON_TOLERANCES)
    metadata = dict(candidate.metadata)
    resolved_config = metadata.get("resolved_config", {})
    mitigation_config = metadata.get("mitigation_config", {})
    if isinstance(resolved_config, dict):
        mitigation_config = mitigation_config or resolved_config.get(
            "mitigation"
        ) or resolved_config.get("mitigation_config", {})
    if isinstance(mitigation_config, dict):
        raw_tolerances = mitigation_config.get("comparison_tolerances", {})
        if isinstance(raw_tolerances, dict):
            for key, value in raw_tolerances.items():
                resolved[str(key)] = float(value)
    return resolved


def classify_mitigation_verdict(
    *,
    mitigation_method: str,
    deltas: dict[str, float | None],
    tolerances: dict[str, float] | None = None,
) -> str:
    """Classify one mitigation outcome as win, tradeoff, or failure."""
    resolved_tolerances = dict(DEFAULT_COMPARISON_TOLERANCES)
    if tolerances:
        resolved_tolerances.update({str(key): float(value) for key, value in tolerances.items()})

    id_drop_tolerance = float(resolved_tolerances["id_macro_f1_max_drop"])
    overall_drop_tolerance = float(resolved_tolerances["overall_macro_f1_max_drop"])
    ece_tolerance = float(resolved_tolerances["ece_neutral_tolerance"])

    id_regression = (deltas.get("id_macro_f1_delta") or 0.0) < (-1.0 * id_drop_tolerance)
    overall_regression = (deltas.get("overall_macro_f1_delta") or 0.0) < (
        -1.0 * overall_drop_tolerance
    )

    if mitigation_method == "reweighting":
        target_improved = any(
            (value is not None and value > 0.0)
            for value in (
                deltas.get("ood_macro_f1_delta"),
                deltas.get("worst_group_f1_delta"),
            )
        )
        if not target_improved:
            return "failure"
        if id_regression or overall_regression:
            return "tradeoff"
        return "win"

    if mitigation_method == "temperature_scaling":
        ece_delta = deltas.get("ece_delta")
        brier_delta = deltas.get("brier_score_delta")
        calibration_improved = bool(
            (ece_delta is not None and ece_delta < (-1.0 * ece_tolerance))
            or (brier_delta is not None and brier_delta < 0.0)
        )
        if not calibration_improved:
            return "failure"

        calibration_regression = ece_delta is not None and ece_delta > ece_tolerance
        classification_regression = any(
            (value is not None and value < (-1.0 * overall_drop_tolerance))
            for value in (
                deltas.get("ood_macro_f1_delta"),
                deltas.get("worst_group_f1_delta"),
            )
        )
        if (
            id_regression
            or overall_regression
            or calibration_regression
            or classification_regression
        ):
            return "tradeoff"
        return "win"

    return "failure"


def pair_mitigation_candidates_with_parents(
    candidates: list[ReportCandidate],
) -> list[tuple[ReportCandidate, ReportCandidate]]:
    """Pair selected mitigation evaluations with their parent baseline evaluations."""
    parent_lookup: dict[str, ReportCandidate] = {}
    for candidate in candidates:
        source_run_id = candidate.metadata.get("source_run_id")
        if source_run_id is None:
            continue
        if candidate.metadata.get("source_parent_run_id") is None:
            parent_lookup[str(source_run_id)] = candidate

    pairs: list[tuple[ReportCandidate, ReportCandidate]] = []
    for candidate in candidates:
        source_parent_run_id = candidate.metadata.get("source_parent_run_id")
        if source_parent_run_id is None:
            continue

        parent_candidate = parent_lookup.get(str(source_parent_run_id))
        if parent_candidate is None:
            raise ValueError(
                "Selected mitigation evaluation bundle is missing its parent baseline "
                f"evaluation: source_parent_run_id={source_parent_run_id}"
            )
        pairs.append((parent_candidate, candidate))

    return sorted(
        pairs,
        key=lambda pair: (
            str(pair[1].metadata.get("mitigation_method", "")),
            str(pair[1].metadata.get("source_run_id", "")),
            pair[1].eval_id,
        ),
    )


def build_mitigation_comparison_table(candidates: list[ReportCandidate]) -> pd.DataFrame:
    """Build the saved parent-versus-child mitigation delta table."""
    pairs = pair_mitigation_candidates_with_parents(candidates)
    rows: list[dict[str, Any]] = []
    for parent_candidate, mitigation_candidate in pairs:
        mitigation_method = str(
            mitigation_candidate.metadata.get("mitigation_method")
            or mitigation_candidate.metadata.get("resolved_config", {})
            .get("mitigation", {})
            .get("method", "unknown")
        )
        deltas = {
            "id_macro_f1_delta": _metric_delta(
                _candidate_metric(mitigation_candidate, "id", "macro_f1"),
                _candidate_metric(parent_candidate, "id", "macro_f1"),
            ),
            "ood_macro_f1_delta": _metric_delta(
                _candidate_metric(mitigation_candidate, "ood", "macro_f1"),
                _candidate_metric(parent_candidate, "ood", "macro_f1"),
            ),
            "overall_macro_f1_delta": _metric_delta(
                _candidate_metric(mitigation_candidate, "overall", "macro_f1"),
                _candidate_metric(parent_candidate, "overall", "macro_f1"),
            ),
            "robustness_gap_delta": _metric_delta(
                _headline_metric(mitigation_candidate, "robustness_gap_f1"),
                _headline_metric(parent_candidate, "robustness_gap_f1"),
            ),
            "worst_group_f1_delta": _metric_delta(
                _headline_metric(mitigation_candidate, "worst_group_f1"),
                _headline_metric(parent_candidate, "worst_group_f1"),
            ),
            "ece_delta": _metric_delta(
                _overall_calibration_metric(mitigation_candidate, "ece"),
                _overall_calibration_metric(parent_candidate, "ece"),
            ),
            "brier_score_delta": _metric_delta(
                _overall_calibration_metric(mitigation_candidate, "brier_score"),
                _overall_calibration_metric(parent_candidate, "brier_score"),
            ),
        }
        verdict = classify_mitigation_verdict(
            mitigation_method=mitigation_method,
            deltas=deltas,
            tolerances=_resolve_comparison_tolerances(mitigation_candidate),
        )
        rows.append(
            {
                "parent_eval_id": parent_candidate.eval_id,
                "mitigation_eval_id": mitigation_candidate.eval_id,
                "parent_label": report_label(parent_candidate),
                "mitigation_label": report_label(mitigation_candidate),
                "mitigation_method": mitigation_method,
                "id_macro_f1_delta": deltas["id_macro_f1_delta"],
                "ood_macro_f1_delta": deltas["ood_macro_f1_delta"],
                "robustness_gap_delta": deltas["robustness_gap_delta"],
                "worst_group_f1_delta": deltas["worst_group_f1_delta"],
                "ece_delta": deltas["ece_delta"],
                "brier_score_delta": deltas["brier_score_delta"],
                "verdict": verdict,
            }
        )

    return pd.DataFrame(rows, columns=MITIGATION_COMPARISON_COLUMNS)
