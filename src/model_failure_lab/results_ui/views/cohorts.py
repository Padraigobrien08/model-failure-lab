"""Seeded cohort analysis view."""

from __future__ import annotations

from typing import Any

from model_failure_lab.results_ui.components import (
    build_seed_rows,
    render_dataframe,
    render_entity_actions,
    render_metric_summary,
)
from model_failure_lab.results_ui.selectors import get_report_by_id, get_seeded_cohorts


def render_cohorts_view(
    st: Any,
    index: dict[str, Any],
    *,
    include_exploratory: bool = False,
) -> None:
    """Render the seeded cohort analysis page."""
    st.title("Cohort Analysis")
    st.caption("Aggregate-first seeded cohort summaries with optional per-seed breakdown.")

    report_lookup = {
        report["id"]: report
        for report in index.get("entities", {}).get("reports", [])
    }
    cohorts = get_seeded_cohorts(index, include_exploratory=include_exploratory)
    for cohort in cohorts:
        st.subheader(cohort.get("display_name", cohort.get("cohort_id", "Unknown Cohort")))
        render_metric_summary(
            st,
            cohort.get("aggregate_metrics", {}).get("mean", {}),
            metric_keys=("id_macro_f1", "robustness_gap_f1", "worst_group_f1"),
        )
        st.caption(
            f"Seeds: {', '.join(cohort.get('seed_ids', []))} • "
            f"Experiment group: {cohort.get('experiment_group', 'n/a')}"
        )

        linked_report_id = cohort.get("linked_report_id")
        if linked_report_id:
            linked_report = report_lookup.get(linked_report_id) or get_report_by_id(
                index,
                linked_report_id,
            )
            if linked_report is not None:
                render_entity_actions(st, linked_report)

        expander = st.expander("Show per-seed breakdown", expanded=False)
        render_dataframe(expander, build_seed_rows(cohort.get("per_seed_metrics", [])))
