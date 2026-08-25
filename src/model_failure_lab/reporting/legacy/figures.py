# ruff: noqa: E402

"""Deterministic static figure builders for report packages."""

from __future__ import annotations

from model_failure_lab.utils.runtime import ensure_matplotlib_runtime_dir

ensure_matplotlib_runtime_dir()

import matplotlib

matplotlib.use("Agg")

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from .discovery import ReportCandidate
from .selection import report_label

PRIMARY_METRIC = "macro_f1"
PRIMARY_METRIC_LABEL = "Macro F1"


def _metric_label(metric_name: str) -> str:
    if metric_name == PRIMARY_METRIC:
        return PRIMARY_METRIC_LABEL
    return metric_name.replace("_", " ").title()


def build_id_ood_comparison_frame(
    candidates: list[ReportCandidate],
    *,
    metric_name: str = PRIMARY_METRIC,
) -> pd.DataFrame:
    """Build the compact ID/OOD comparison rows used by figures and tables."""
    rows: list[dict[str, object]] = []
    robustness_key = f"robustness_gap_{metric_name.replace('macro_', '')}"
    if metric_name == "macro_f1":
        robustness_key = "robustness_gap_f1"

    for candidate in candidates:
        headline_metrics = candidate.overall_metrics.get("headline_metrics", {})
        rows.append(
            {
                "eval_id": candidate.eval_id,
                "label": report_label(candidate),
                "model_name": candidate.metadata.get("model_name"),
                "source_run_id": candidate.metadata.get("source_run_id"),
                "id_score": candidate.overall_metrics.get("id", {}).get(metric_name),
                "ood_score": candidate.overall_metrics.get("ood", {}).get(metric_name),
                "robustness_gap": headline_metrics.get(robustness_key),
                "accuracy": headline_metrics.get("accuracy"),
                "macro_f1": headline_metrics.get("macro_f1"),
                "auroc": headline_metrics.get("auroc"),
            }
        )
    return pd.DataFrame(rows)


def build_worst_group_vs_average_frame(
    candidates: list[ReportCandidate],
    *,
    metric_name: str = PRIMARY_METRIC,
) -> pd.DataFrame:
    """Build the average-versus-worst-group comparison rows."""
    metric_key = "worst_group_f1" if metric_name == PRIMARY_METRIC else f"worst_group_{metric_name}"
    rows: list[dict[str, object]] = []
    for candidate in candidates:
        headline_metrics = candidate.overall_metrics.get("headline_metrics", {})
        rows.append(
            {
                "eval_id": candidate.eval_id,
                "label": report_label(candidate),
                "average_score": candidate.overall_metrics.get("overall", {}).get(metric_name),
                "worst_group_score": headline_metrics.get(metric_key),
            }
        )
    return pd.DataFrame(rows)


def build_worst_subgroups_frame(
    candidate: ReportCandidate,
    *,
    top_k: int = 5,
    min_group_support: int | None = None,
    metric_name: str = PRIMARY_METRIC,
) -> pd.DataFrame:
    """Return the top-k worst eligible subgroup rows for one report candidate."""
    subgroup_frame = candidate.subgroup_metrics.copy()
    if subgroup_frame.empty:
        return subgroup_frame

    group_rows = subgroup_frame.loc[subgroup_frame["grouping_type"] == "group_id"].copy()
    if min_group_support is not None:
        group_rows = group_rows.loc[group_rows["support"] >= int(min_group_support)]
    else:
        eligibility = group_rows["eligible_for_worst_group"].fillna(False)
        group_rows = group_rows.loc[eligibility.astype(bool)]

    if group_rows.empty:
        return group_rows

    selected_columns = ["group_name", "support", "accuracy", "macro_f1", "error_rate"]
    return (
        group_rows.sort_values(
            by=[metric_name, "support", "group_name"],
            ascending=[True, False, True],
        )
        .head(top_k)
        .loc[:, selected_columns]
        .reset_index(drop=True)
    )


def build_id_ood_figure(
    comparison_frame: pd.DataFrame,
    *,
    metric_name: str = PRIMARY_METRIC,
) -> Figure:
    """Build the grouped bar chart for ID versus OOD performance."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x_positions = list(range(len(comparison_frame)))
    width = 0.35

    id_values = comparison_frame["id_score"].fillna(0.0).astype(float).tolist()
    ood_values = comparison_frame["ood_score"].fillna(0.0).astype(float).tolist()
    labels = comparison_frame["label"].astype(str).tolist()

    ax.bar([position - width / 2 for position in x_positions], id_values, width, label="ID")
    ax.bar([position + width / 2 for position in x_positions], ood_values, width, label="OOD")
    ax.set_ylabel(_metric_label(metric_name))
    ax.set_title(f"ID vs OOD {_metric_label(metric_name)}")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.legend()
    ax.set_ylim(bottom=0.0)
    fig.tight_layout()
    return fig


def build_worst_group_vs_average_figure(
    comparison_frame: pd.DataFrame,
    *,
    metric_name: str = PRIMARY_METRIC,
) -> Figure:
    """Build the average versus worst-group comparison chart."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x_positions = list(range(len(comparison_frame)))
    width = 0.35
    labels = comparison_frame["label"].astype(str).tolist()

    average_values = comparison_frame["average_score"].fillna(0.0).astype(float).tolist()
    worst_values = comparison_frame["worst_group_score"].fillna(0.0).astype(float).tolist()

    ax.bar(
        [position - width / 2 for position in x_positions],
        average_values,
        width,
        label=f"Average {_metric_label(metric_name)}",
    )
    ax.bar(
        [position + width / 2 for position in x_positions],
        worst_values,
        width,
        label=f"Worst-group {_metric_label(metric_name)}",
    )
    ax.set_ylabel(_metric_label(metric_name))
    ax.set_title("Worst-group vs Average Performance")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.legend()
    ax.set_ylim(bottom=0.0)
    fig.tight_layout()
    return fig


def build_worst_subgroups_figure(
    subgroup_frame: pd.DataFrame,
    *,
    metric_name: str = PRIMARY_METRIC,
) -> Figure:
    """Build the worst-subgroups horizontal bar chart."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if "label" in subgroup_frame.columns:
        labels = (
            subgroup_frame["label"].astype(str) + " / " + subgroup_frame["group_name"].astype(str)
        ).tolist()
    else:
        labels = subgroup_frame["group_name"].astype(str).tolist()
    scores = subgroup_frame[metric_name].fillna(0.0).astype(float).tolist()

    ax.barh(labels, scores)
    ax.set_xlabel(_metric_label(metric_name))
    ax.set_title(f"Worst Eligible Subgroups by {_metric_label(metric_name)}")
    ax.invert_yaxis()
    ax.set_xlim(left=0.0)
    fig.tight_layout()
    return fig


def build_clean_vs_perturbed_figure(
    suite_summary: pd.DataFrame,
    *,
    metric_name: str = PRIMARY_METRIC,
) -> Figure:
    """Build the grouped bar chart for clean versus perturbed validation performance."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x_positions = list(range(len(suite_summary)))
    width = 0.35
    clean_values = suite_summary[f"clean_{metric_name}"].fillna(0.0).astype(float).tolist()
    perturbed_values = suite_summary[f"perturbed_{metric_name}"].fillna(0.0).astype(float).tolist()
    labels = suite_summary["label"].astype(str).tolist()

    ax.bar([position - width / 2 for position in x_positions], clean_values, width, label="Clean")
    ax.bar(
        [position + width / 2 for position in x_positions],
        perturbed_values,
        width,
        label="Perturbed",
    )
    ax.set_ylabel(_metric_label(metric_name))
    ax.set_title(f"Clean vs Perturbed {_metric_label(metric_name)}")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.legend()
    ax.set_ylim(bottom=0.0)
    fig.tight_layout()
    return fig


def build_perturbation_family_drop_figure(
    family_summary: pd.DataFrame,
    *,
    metric_name: str = PRIMARY_METRIC,
) -> Figure:
    """Build the family-level degradation chart."""
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    drop_column = f"{metric_name}_drop"
    labels = (
        family_summary["label"].astype(str)
        + " / "
        + family_summary["perturbation_family"].astype(str)
    ).tolist()
    drop_values = family_summary[drop_column].fillna(0.0).astype(float).tolist()

    ax.barh(labels, drop_values)
    ax.set_xlabel(f"{_metric_label(metric_name)} Drop")
    ax.set_title("Performance Drop by Perturbation Family")
    ax.invert_yaxis()
    ax.set_xlim(left=0.0)
    fig.tight_layout()
    return fig


def build_severity_ladder_figure(
    severity_summary: pd.DataFrame,
    *,
    metric_name: str = PRIMARY_METRIC,
) -> Figure:
    """Build the severity ladder chart for perturbation degradation."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    drop_column = f"{metric_name}_drop"
    severity_order = ["low", "medium", "high"]
    x_positions = list(range(len(severity_order)))

    for label, label_frame in severity_summary.groupby("label"):
        ordered = (
            label_frame.assign(
                severity_rank=label_frame["severity"].apply(
                    lambda value: severity_order.index(str(value))
                )
            )
            .sort_values(by="severity_rank")
            .reset_index(drop=True)
        )
        ax.plot(
            x_positions,
            ordered[drop_column].fillna(0.0).astype(float).tolist(),
            marker="o",
            label=str(label),
        )

    ax.set_xticks(x_positions)
    ax.set_xticklabels(severity_order)
    ax.set_ylabel(f"{_metric_label(metric_name)} Drop")
    ax.set_title("Severity Sensitivity")
    ax.set_ylim(bottom=0.0)
    ax.legend()
    fig.tight_layout()
    return fig
