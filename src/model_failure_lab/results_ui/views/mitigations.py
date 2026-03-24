"""Mitigation comparison view."""

from __future__ import annotations

from typing import Any

from model_failure_lab.results_ui.components import (
    build_delta_rows,
    render_actions,
    render_dataframe,
    render_delta_summary,
)
from model_failure_lab.results_ui.formatters import format_label
from model_failure_lab.results_ui.selectors import (
    get_mitigation_comparison_views,
    get_primary_stability_package,
)


def render_mitigations_view(
    st: Any,
    index: dict[str, Any],
    *,
    include_exploratory: bool = False,
) -> None:
    """Render the seeded mitigation comparison page."""
    st.title("Mitigation Comparison")
    st.caption(
        "Aggregate-first parent-child comparisons with explicit seeded and "
        "milestone labels."
    )

    stability_package = get_primary_stability_package(
        index,
        include_exploratory=include_exploratory,
    )
    stability_labels = stability_package.get("cohort_summaries", {})

    for view in get_mitigation_comparison_views(index, include_exploratory=include_exploratory):
        mitigation_method = view.get("mitigation_method", "unknown")
        st.subheader(format_label(mitigation_method))
        st.markdown(
            f"**Seeded comparison summary:** "
            f"{format_label(view.get('comparison_summary', {}).get('seeded_interpretation'))}"
        )
        st.markdown(
            f"**Phase 20 milestone label:** "
            f"{format_label(stability_labels.get(mitigation_method, {}).get('label'))}"
        )

        render_delta_summary(
            st,
            view.get("stability_assessment", {}).get("mean_deltas", {}),
            metric_keys=(
                "id_macro_f1_delta",
                "robustness_gap_delta",
                "worst_group_f1_delta",
            ),
        )
        render_actions(st, view.get("summary_actions", []))

        st.caption(
            f"Verdicts: {view.get('stability_assessment', {}).get('verdict_counts', {})}"
        )
        expander = st.expander("Show per-seed breakdown", expanded=False)
        render_dataframe(expander, build_delta_rows(view.get("per_seed_comparisons", [])))

        for comparison in view.get("per_seed_comparisons", []):
            if comparison.get("support_actions"):
                seed_expander = st.expander(
                    f"Seed {comparison.get('seed')} evidence",
                    expanded=False,
                )
                render_actions(seed_expander, comparison.get("support_actions", []))
