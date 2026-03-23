"""Reusable presentational helpers for the results explorer."""

from __future__ import annotations

from typing import Any

import pandas as pd

from model_failure_lab.results_ui.formatters import (
    DELTA_METRICS,
    KEY_OVERVIEW_METRICS,
    build_metadata_actions,
    extract_ref_path,
    format_delta,
    format_label,
    format_metric,
    format_metric_label,
    resolve_artifact_uri,
)


def render_badge(st: Any, *, label: str, value: str) -> None:
    """Render a lightweight badge-like callout."""
    st.markdown(f"**{label}:** {format_label(value)}")


def render_actions(st: Any, actions: list[dict[str, str]]) -> None:
    """Render lightweight artifact drill-through actions."""
    if not actions:
        return

    columns = st.columns(len(actions))
    for column, action in zip(columns, actions):
        uri = action.get("uri")
        label = action.get("label", "Open")
        if hasattr(column, "link_button") and uri:
            column.link_button(label, uri)
        else:
            column.markdown(f"[{label}]({uri})")


def render_entity_actions(st: Any, entity: dict[str, Any]) -> None:
    """Render the standard actions for one manifest entity."""
    render_actions(st, build_metadata_actions(entity))


def render_metric_summary(
    st: Any,
    metrics: dict[str, Any],
    *,
    metric_keys: tuple[str, ...],
) -> None:
    """Render one compact row of metric cards."""
    columns = st.columns(len(metric_keys))
    for column, metric_key in zip(columns, metric_keys):
        column.metric(format_metric_label(metric_key), format_metric(metrics.get(metric_key)))


def render_delta_summary(
    st: Any,
    deltas: dict[str, Any],
    *,
    metric_keys: tuple[str, ...] = DELTA_METRICS,
) -> None:
    """Render one compact row of delta cards."""
    columns = st.columns(len(metric_keys))
    for column, metric_key in zip(columns, metric_keys):
        column.metric(format_metric_label(metric_key), format_delta(deltas.get(metric_key)))


def render_dataframe(st: Any, rows: list[dict[str, Any]]) -> None:
    """Render a simple dataframe from row dictionaries."""
    if not rows:
        st.caption("No rows available.")
        return
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def build_metric_chart_rows(cohorts: list[dict[str, Any]], metric_key: str) -> pd.DataFrame:
    """Build aggregate cohort rows for one chart."""
    rows: list[dict[str, Any]] = []
    for cohort in cohorts:
        mean_metrics = cohort.get("aggregate_metrics", {}).get("mean", {})
        rows.append(
            {
                "cohort": cohort.get("display_name", cohort.get("cohort_id", "Unknown")),
                "value": mean_metrics.get(metric_key),
            }
        )
    return pd.DataFrame(rows)


def render_overview_charts(st: Any, cohorts: list[dict[str, Any]]) -> None:
    """Render the aggregate-first overview visuals."""
    robustness_gap_df = build_metric_chart_rows(cohorts, "robustness_gap_f1")
    worst_group_df = build_metric_chart_rows(cohorts, "worst_group_f1")

    st.subheader("Cohort Snapshot")
    if not robustness_gap_df.empty:
        st.bar_chart(robustness_gap_df.set_index("cohort"))
    if not worst_group_df.empty:
        st.bar_chart(worst_group_df.set_index("cohort"))


def build_seed_rows(per_seed_metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize one per-seed metric table for display."""
    rows: list[dict[str, Any]] = []
    for metric_row in per_seed_metrics:
        row = {
            "Seed": metric_row.get("seed"),
            "Run": metric_row.get("run_id"),
            "Eval": metric_row.get("eval_id"),
        }
        for metric_key in KEY_OVERVIEW_METRICS:
            row[format_metric_label(metric_key)] = format_metric(metric_row.get(metric_key))
        row[format_metric_label("ece")] = format_metric(metric_row.get("ece"))
        row[format_metric_label("brier_score")] = format_metric(metric_row.get("brier_score"))
        rows.append(row)
    return rows


def build_delta_rows(per_seed_comparisons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize one seeded delta table for display."""
    rows: list[dict[str, Any]] = []
    for comparison in per_seed_comparisons:
        row = {
            "Seed": comparison.get("seed"),
            "Verdict": format_label(comparison.get("verdict")),
            "Parent Run": comparison.get("parent_run_id"),
            "Child Run": comparison.get("child_run_id"),
        }
        for metric_key in DELTA_METRICS:
            row[format_metric_label(metric_key)] = format_delta(
                comparison.get("deltas", {}).get(metric_key)
            )
        rows.append(row)
    return rows


def render_related_report_actions(
    st: Any,
    *,
    report_entities: list[dict[str, Any]],
) -> None:
    """Render actions for one or more related report entities."""
    actions: list[dict[str, str]] = []
    for entity in report_entities:
        report_scope = entity.get("report_scope", "report")
        report_markdown_path = extract_ref_path(
            entity.get("artifact_refs", {}).get("report_markdown")
        )
        action = {
            "label": f"View {format_label(report_scope)}",
            "path": report_markdown_path or "",
            "uri": resolve_artifact_uri(report_markdown_path) or "",
        }
        if report_markdown_path:
            actions.append(action)
    render_actions(st, actions)
