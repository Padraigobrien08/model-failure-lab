"""Seeded stability aggregation helpers for the milestone findings package."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from .discovery import ReportCandidate
from .mitigation import build_mitigation_comparison_table

SEED_TAG_PATTERN = re.compile(r"^seed_(\d+)$")
BASELINE_STABILITY_COLUMNS = [
    "cohort",
    "row_type",
    "seed",
    "model_name",
    "source_run_id",
    "eval_id",
    "id_macro_f1",
    "ood_macro_f1",
    "robustness_gap_f1",
    "worst_group_f1",
    "ece",
    "brier_score",
]
MITIGATION_STABILITY_COLUMNS = [
    "mitigation_method",
    "row_type",
    "seed",
    "parent_eval_id",
    "mitigation_eval_id",
    "parent_label",
    "mitigation_label",
    "id_macro_f1_delta",
    "ood_macro_f1_delta",
    "robustness_gap_delta",
    "worst_group_f1_delta",
    "ece_delta",
    "brier_score_delta",
    "verdict",
]
BASELINE_NUMERIC_COLUMNS = [
    "id_macro_f1",
    "ood_macro_f1",
    "robustness_gap_f1",
    "worst_group_f1",
    "ece",
    "brier_score",
]
MITIGATION_NUMERIC_COLUMNS = [
    "id_macro_f1_delta",
    "ood_macro_f1_delta",
    "robustness_gap_delta",
    "worst_group_f1_delta",
    "ece_delta",
    "brier_score_delta",
]
REPORT_REFERENCE_SCOPES = {
    "temperature_scaling_seeded": "phase18_temperature_scaling_seeded",
    "reweighting_seeded": "phase19_reweighting_seeded",
}
LABEL_STABLE = "stable"
LABEL_MIXED = "mixed"
LABEL_NOISY = "noisy"


def _candidate_metric(candidate: ReportCandidate, section: str, metric_name: str) -> float | None:
    payload = candidate.overall_metrics.get(section, {})
    if not isinstance(payload, dict):
        return None
    value = payload.get(metric_name)
    if value is None or pd.isna(value):
        return None
    return float(value)


def _headline_metric(candidate: ReportCandidate, metric_name: str) -> float | None:
    payload = candidate.overall_metrics.get("headline_metrics", {})
    if not isinstance(payload, dict):
        return None
    value = payload.get(metric_name)
    if value is None or pd.isna(value):
        return None
    return float(value)


def _overall_calibration_metric(candidate: ReportCandidate, metric_name: str) -> float | None:
    frame = candidate.calibration_summary.copy()
    if frame.empty or metric_name not in frame.columns:
        return None
    overall_rows = frame.loc[frame["slice_name"] == "overall"]
    if overall_rows.empty:
        return None
    value = overall_rows.iloc[0][metric_name]
    if value is None or pd.isna(value):
        return None
    return float(value)


def _seed_from_metadata(metadata: dict[str, Any]) -> str:
    for tag_source in (
        metadata.get("tags", []),
        metadata.get("resolved_config", {}).get("tags", []),
    ):
        if not isinstance(tag_source, list):
            continue
        for tag in tag_source:
            match = SEED_TAG_PATTERN.match(str(tag))
            if match:
                return match.group(1)
    random_seed = metadata.get("random_seed")
    if random_seed is not None:
        return str(int(random_seed))
    resolved_seed = metadata.get("resolved_config", {}).get("seed")
    if resolved_seed is not None:
        return str(int(resolved_seed))
    raise ValueError("Saved evaluation bundle is missing a stable seed identity")


def _seed_sort_value(seed: object) -> tuple[int, str]:
    seed_text = str(seed)
    if seed_text.isdigit():
        return (0, f"{int(seed_text):08d}")
    if seed_text == "mean":
        return (1, seed_text)
    if seed_text == "std":
        return (2, seed_text)
    return (3, seed_text)


def _append_aggregate_rows(
    frame: pd.DataFrame,
    *,
    group_columns: list[str],
    numeric_columns: list[str],
    all_columns: list[str],
) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=all_columns)

    rows: list[dict[str, Any]] = []
    for group_values, group_frame in frame.groupby(group_columns, dropna=False, sort=False):
        if not isinstance(group_values, tuple):
            group_values = (group_values,)
        group_lookup = dict(zip(group_columns, group_values, strict=False))
        for aggregate_name, reducer in (("mean", "mean"), ("std", "std")):
            row = {column: None for column in all_columns}
            row.update(group_lookup)
            row["row_type"] = "aggregate"
            row["seed"] = aggregate_name
            for column in numeric_columns:
                series = group_frame[column]
                row[column] = (
                    float(series.mean())
                    if reducer == "mean"
                    else float(series.std(ddof=0))
                )
            rows.append(row)

    aggregate_frame = pd.DataFrame(rows, columns=all_columns)
    combined = pd.concat([frame, aggregate_frame], ignore_index=True)
    return combined.sort_values(
        by=group_columns + ["seed"],
        key=lambda series: series.map(_seed_sort_value),
        ignore_index=True,
    )


def build_baseline_stability_table(
    *,
    logistic_candidates: list[ReportCandidate],
    distilbert_candidates: list[ReportCandidate],
) -> pd.DataFrame:
    """Build one normalized baseline stability table across both baseline cohorts."""
    rows: list[dict[str, Any]] = []
    for cohort_name, candidates in (
        ("logistic_baseline", logistic_candidates),
        ("distilbert_baseline", distilbert_candidates),
    ):
        for candidate in candidates:
            rows.append(
                {
                    "cohort": cohort_name,
                    "row_type": "seed",
                    "seed": _seed_from_metadata(candidate.metadata),
                    "model_name": candidate.metadata.get("model_name"),
                    "source_run_id": candidate.metadata.get("source_run_id"),
                    "eval_id": candidate.eval_id,
                    "id_macro_f1": _candidate_metric(candidate, "id", "macro_f1"),
                    "ood_macro_f1": _candidate_metric(candidate, "ood", "macro_f1"),
                    "robustness_gap_f1": _headline_metric(candidate, "robustness_gap_f1"),
                    "worst_group_f1": _headline_metric(candidate, "worst_group_f1"),
                    "ece": _overall_calibration_metric(candidate, "ece"),
                    "brier_score": _overall_calibration_metric(candidate, "brier_score"),
                }
            )

    frame = pd.DataFrame(rows, columns=BASELINE_STABILITY_COLUMNS)
    return _append_aggregate_rows(
        frame,
        group_columns=["cohort"],
        numeric_columns=BASELINE_NUMERIC_COLUMNS,
        all_columns=BASELINE_STABILITY_COLUMNS,
    )


def build_mitigation_stability_table(
    *,
    parent_candidates: list[ReportCandidate],
    mitigation_candidates: list[ReportCandidate],
) -> pd.DataFrame:
    """Build one seeded mitigation delta table with per-seed and aggregate rows."""
    comparison_table = build_mitigation_comparison_table(
        [*parent_candidates, *mitigation_candidates]
    )
    if comparison_table.empty:
        return pd.DataFrame(columns=MITIGATION_STABILITY_COLUMNS)

    seed_lookup = {
        candidate.eval_id: _seed_from_metadata(candidate.metadata)
        for candidate in mitigation_candidates
    }
    frame = comparison_table.copy()
    frame["row_type"] = "seed"
    frame["seed"] = frame["mitigation_eval_id"].map(seed_lookup).fillna("")
    frame = frame[MITIGATION_STABILITY_COLUMNS]
    return _append_aggregate_rows(
        frame,
        group_columns=["mitigation_method"],
        numeric_columns=MITIGATION_NUMERIC_COLUMNS,
        all_columns=MITIGATION_STABILITY_COLUMNS,
    )


def _mean_std_lookup(
    frame: pd.DataFrame,
    *,
    group_column: str,
    group_value: str,
    numeric_columns: list[str],
) -> tuple[dict[str, float | None], dict[str, float | None]]:
    mean_lookup = {column: None for column in numeric_columns}
    std_lookup = {column: None for column in numeric_columns}
    if frame.empty:
        return mean_lookup, std_lookup

    filtered = frame.loc[frame[group_column] == group_value]
    mean_rows = filtered.loc[filtered["seed"] == "mean"]
    std_rows = filtered.loc[filtered["seed"] == "std"]
    if not mean_rows.empty:
        mean_lookup = {
            column: None if pd.isna(mean_rows.iloc[0][column]) else float(mean_rows.iloc[0][column])
            for column in numeric_columns
        }
    if not std_rows.empty:
        std_lookup = {
            column: None if pd.isna(std_rows.iloc[0][column]) else float(std_rows.iloc[0][column])
            for column in numeric_columns
        }
    return mean_lookup, std_lookup


def _classify_baseline_cohort(seed_rows: pd.DataFrame) -> str:
    if seed_rows.empty:
        return LABEL_NOISY

    robustness_gap = seed_rows["robustness_gap_f1"].astype(float)
    ood_macro_f1 = seed_rows["ood_macro_f1"].astype(float)
    worst_group_f1 = seed_rows["worst_group_f1"].astype(float)
    if (robustness_gap > 0.0).all() and (ood_macro_f1.max() - ood_macro_f1.min()) <= 0.01 and (
        worst_group_f1.max() - worst_group_f1.min()
    ) <= 0.02:
        return LABEL_STABLE
    if (robustness_gap > 0.0).sum() >= max(1, len(robustness_gap.index) - 1):
        return LABEL_MIXED
    return LABEL_NOISY


def _classify_mitigation_lane(seed_rows: pd.DataFrame) -> str:
    if seed_rows.empty:
        return LABEL_NOISY
    verdict_counts = seed_rows["verdict"].fillna("").value_counts()
    wins = int(verdict_counts.get("win", 0))
    tradeoffs = int(verdict_counts.get("tradeoff", 0))
    failures = int(verdict_counts.get("failure", 0))
    total = int(len(seed_rows.index))

    if wins == total:
        return LABEL_STABLE
    if wins >= 1 and tradeoffs >= 1 and failures == 0:
        return LABEL_MIXED
    if wins >= 2 and failures == 0:
        return LABEL_MIXED
    return LABEL_NOISY


def _build_baseline_model_comparison_summary(baseline_table: pd.DataFrame) -> dict[str, Any]:
    seed_rows = baseline_table.loc[baseline_table["row_type"] == "seed"].copy()
    logistic_rows = seed_rows.loc[seed_rows["cohort"] == "logistic_baseline"].copy()
    distilbert_rows = seed_rows.loc[seed_rows["cohort"] == "distilbert_baseline"].copy()
    merged = distilbert_rows.merge(
        logistic_rows,
        on="seed",
        suffixes=("_distilbert", "_logistic"),
    )
    if merged.empty:
        return {"label": LABEL_NOISY, "per_seed_deltas": [], "mean_deltas": {}, "std_deltas": {}}

    merged["ood_macro_f1_delta"] = (
        merged["ood_macro_f1_distilbert"] - merged["ood_macro_f1_logistic"]
    )
    merged["worst_group_f1_delta"] = (
        merged["worst_group_f1_distilbert"] - merged["worst_group_f1_logistic"]
    )
    label = (
        LABEL_STABLE
        if (merged["ood_macro_f1_delta"] > 0.0).all()
        and (merged["worst_group_f1_delta"] > 0.0).all()
        else LABEL_MIXED
        if (merged["ood_macro_f1_delta"] > 0.0).sum() >= 2
        else LABEL_NOISY
    )
    return {
        "label": label,
        "per_seed_deltas": [
            {
                "seed": str(row["seed"]),
                "ood_macro_f1_delta": float(row["ood_macro_f1_delta"]),
                "worst_group_f1_delta": float(row["worst_group_f1_delta"]),
            }
            for _, row in merged.sort_values(by="seed").iterrows()
        ],
        "mean_deltas": {
            "ood_macro_f1_delta": float(merged["ood_macro_f1_delta"].mean()),
            "worst_group_f1_delta": float(merged["worst_group_f1_delta"].mean()),
        },
        "std_deltas": {
            "ood_macro_f1_delta": float(merged["ood_macro_f1_delta"].std(ddof=0)),
            "worst_group_f1_delta": float(merged["worst_group_f1_delta"].std(ddof=0)),
        },
    }


def _build_baseline_cohort_summary(
    baseline_table: pd.DataFrame,
    *,
    cohort_name: str,
) -> dict[str, Any]:
    seed_rows = baseline_table.loc[
        (baseline_table["cohort"] == cohort_name) & (baseline_table["row_type"] == "seed")
    ].copy()
    mean_metrics, std_metrics = _mean_std_lookup(
        baseline_table,
        group_column="cohort",
        group_value=cohort_name,
        numeric_columns=BASELINE_NUMERIC_COLUMNS,
    )
    return {
        "label": _classify_baseline_cohort(seed_rows),
        "seed_count": int(len(seed_rows.index)),
        "mean_metrics": mean_metrics,
        "std_metrics": std_metrics,
    }


def _build_mitigation_lane_summary(
    mitigation_table: pd.DataFrame,
    *,
    method_name: str,
) -> dict[str, Any]:
    seed_rows = mitigation_table.loc[
        (mitigation_table["mitigation_method"] == method_name)
        & (mitigation_table["row_type"] == "seed")
    ].copy()
    mean_deltas, std_deltas = _mean_std_lookup(
        mitigation_table,
        group_column="mitigation_method",
        group_value=method_name,
        numeric_columns=MITIGATION_NUMERIC_COLUMNS,
    )
    verdict_counts = {
        "win": int((seed_rows["verdict"] == "win").sum()) if not seed_rows.empty else 0,
        "tradeoff": int((seed_rows["verdict"] == "tradeoff").sum()) if not seed_rows.empty else 0,
        "failure": int((seed_rows["verdict"] == "failure").sum()) if not seed_rows.empty else 0,
    }
    return {
        "label": _classify_mitigation_lane(seed_rows),
        "seed_count": int(len(seed_rows.index)),
        "verdict_counts": verdict_counts,
        "mean_deltas": mean_deltas,
        "std_deltas": std_deltas,
    }


def _latest_report_markdown_path(report_scope: str) -> str | None:
    report_root = (
        Path(__file__).resolve().parents[3]
        / "artifacts"
        / "reports"
        / "comparisons"
        / report_scope
    )
    candidates = sorted(report_root.glob("*/report.md"))
    if not candidates:
        return None
    return str(candidates[-1])


def build_default_reference_reports() -> dict[str, str | None]:
    """Return the default reference report paths used by the Phase 20 synthesis page."""
    return {
        key: _latest_report_markdown_path(scope)
        for key, scope in REPORT_REFERENCE_SCOPES.items()
    }


def build_stability_summary(
    *,
    report_title: str,
    baseline_stability_table: pd.DataFrame,
    temperature_scaling_deltas: pd.DataFrame,
    reweighting_deltas: pd.DataFrame,
    reference_reports: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    """Build the machine-readable seeded stability summary payload."""
    cohort_summaries = {
        "logistic_baseline": _build_baseline_cohort_summary(
            baseline_stability_table,
            cohort_name="logistic_baseline",
        ),
        "distilbert_baseline": _build_baseline_cohort_summary(
            baseline_stability_table,
            cohort_name="distilbert_baseline",
        ),
        "temperature_scaling": _build_mitigation_lane_summary(
            temperature_scaling_deltas,
            method_name="temperature_scaling",
        ),
        "reweighting": _build_mitigation_lane_summary(
            reweighting_deltas,
            method_name="reweighting",
        ),
    }
    baseline_model_comparison = _build_baseline_model_comparison_summary(baseline_stability_table)

    if (
        cohort_summaries["distilbert_baseline"]["label"] != LABEL_NOISY
        and cohort_summaries["temperature_scaling"]["label"] == LABEL_STABLE
        and baseline_model_comparison["label"] != LABEL_NOISY
    ):
        v1_1_findings_status = LABEL_STABLE
    elif baseline_model_comparison["label"] == LABEL_NOISY:
        v1_1_findings_status = LABEL_NOISY
    else:
        v1_1_findings_status = LABEL_MIXED

    dataset_recommendation = (
        "consider"
        if cohort_summaries["reweighting"]["label"] == LABEL_STABLE
        and cohort_summaries["temperature_scaling"]["label"] == LABEL_STABLE
        else "defer"
    )
    recommendation_reason = (
        (
            "Keep dataset expansion deferred until the robustness-oriented "
            "mitigation story is more consistent across seeds."
        )
        if dataset_recommendation == "defer"
        else (
            "The baseline and mitigation stories are consistent enough to "
            "consider a bounded second-dataset validation."
        )
    )
    next_step = (
        (
            "Keep dataset expansion deferred and follow with either tighter "
            "reweighting validation or another robustness-targeted mitigation."
        )
        if dataset_recommendation == "defer"
        else (
            "Promote the same artifact contract to one carefully bounded "
            "second-dataset validation."
        )
    )

    temp_mean_ece = cohort_summaries["temperature_scaling"]["mean_deltas"].get("ece_delta")
    reweight_mean_worst = cohort_summaries["reweighting"]["mean_deltas"].get(
        "worst_group_f1_delta"
    )
    model_mean_ood = baseline_model_comparison["mean_deltas"].get("ood_macro_f1_delta")
    headline_findings = [
        (
            "The DistilBERT baseline robustness gap is stable across the official seeded cohort."
            if cohort_summaries["distilbert_baseline"]["label"] == LABEL_STABLE
            else (
                "The DistilBERT baseline robustness gap remains directionally "
                "consistent but needs caveats."
            )
        ),
        (
            (
                "Temperature scaling is stable across seeds with mean "
                f"ECE delta {float(temp_mean_ece):.3f}."
            )
            if temp_mean_ece is not None
            else "Temperature scaling remains the cleanest mitigation lane across seeds."
        ),
        (
            (
                "Reweighting is mixed across seeds with mean worst-group "
                f"F1 delta {float(reweight_mean_worst):.3f}."
            )
            if reweight_mean_worst is not None
            else "Reweighting remains mixed across the official seeded cohort."
        ),
        (
            (
                "DistilBERT beats Logistic Regression on OOD Macro F1 by a "
                f"mean {float(model_mean_ood):.3f} across matched seeds."
            )
            if model_mean_ood is not None
            else "DistilBERT remains the stronger baseline model across matched seeds."
        ),
        recommendation_reason,
    ]
    key_takeaway = headline_findings[0]

    return {
        "report_title": report_title,
        "headline_findings": headline_findings,
        "key_takeaway": key_takeaway,
        "cohort_summaries": cohort_summaries,
        "baseline_model_comparison": baseline_model_comparison,
        "milestone_assessment": {
            "v1_1_findings_status": v1_1_findings_status,
            "dataset_expansion_recommendation": dataset_recommendation,
            "recommendation_reason": recommendation_reason,
            "next_step": next_step,
        },
        "reference_reports": reference_reports or build_default_reference_reports(),
    }
