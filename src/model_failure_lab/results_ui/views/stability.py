"""Milestone stability view."""

from __future__ import annotations

from typing import Any

from model_failure_lab.results_ui.components import render_actions, render_dataframe
from model_failure_lab.results_ui.formatters import format_label
from model_failure_lab.results_ui.selectors import get_primary_stability_package


def render_stability_view(
    st: Any,
    index: dict[str, Any],
    *,
    include_exploratory: bool = False,
) -> None:
    """Render the Phase 20 stability package."""
    package = get_primary_stability_package(index, include_exploratory=include_exploratory)
    milestone_assessment = package.get("milestone_assessment", {})

    st.title("Stability")
    st.caption("Phase 20 seeded stability package and final milestone recommendation.")

    cohort_rows = []
    for cohort_id, summary in package.get("cohort_summaries", {}).items():
        cohort_rows.append(
            {
                "Cohort": format_label(cohort_id),
                "Label": format_label(summary.get("label")),
            }
        )
    render_dataframe(st, cohort_rows)

    st.markdown(
        f"**Baseline comparison:** "
        f"{format_label(package.get('baseline_model_comparison', {}).get('label'))}"
    )
    st.markdown(
        f"**Original v1.1 findings:** "
        f"{format_label(milestone_assessment.get('v1_1_findings_status'))}"
    )
    st.markdown(
        f"**Dataset expansion recommendation:** "
        f"{format_label(milestone_assessment.get('dataset_expansion_recommendation'))}"
    )
    if milestone_assessment.get("recommendation_reason"):
        st.caption(milestone_assessment["recommendation_reason"])
    if milestone_assessment.get("next_step"):
        st.markdown(f"**Next step:** {milestone_assessment['next_step']}")
    render_actions(st, package.get("summary_actions", []))

    reference_rows = []
    for scope, reference in package.get("reference_reports", {}).items():
        reference_rows.append(
            {
                "Scope": format_label(scope),
                "Report": reference.get("report_scope", format_label(scope)),
                "Path": reference.get("path"),
            }
        )
    if reference_rows:
        expander = st.expander("Show reference reports", expanded=False)
        render_actions(expander, package.get("reference_actions", []))
        render_dataframe(expander, reference_rows)
