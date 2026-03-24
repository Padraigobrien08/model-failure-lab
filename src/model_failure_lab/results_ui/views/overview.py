"""Overview page for the read-only results explorer."""

from __future__ import annotations

from typing import Any

from model_failure_lab.results_ui.components import (
    render_actions,
    render_badge,
    render_metric_summary,
    render_overview_charts,
)
from model_failure_lab.results_ui.formatters import format_label
from model_failure_lab.results_ui.selectors import build_overview_snapshot


def render_overview_view(
    st: Any,
    index: dict[str, Any],
    *,
    include_exploratory: bool = False,
) -> None:
    """Render the milestone-story-first overview view."""
    snapshot = build_overview_snapshot(index, include_exploratory=include_exploratory)
    mitigation_labels = snapshot["mitigation_labels"]
    inventory_counts = snapshot["inventory_counts"]
    seeded_cohorts = snapshot["seeded_cohorts"]

    st.title("Model Failure Lab")
    st.caption("Artifact-driven benchmark story over the final official evidence package.")
    st.markdown(
        "The final closeout confirms that the original shift findings remain "
        "stable under seeds, that **temperature scaling** is the clean calibration "
        "lane, and that **reweighting** remains the best current robustness lane "
        "without resolving robustness cleanly enough for dataset expansion."
    )
    render_actions(st, snapshot.get("headline_actions", {}).get("findings_doc", []))
    render_actions(st, snapshot.get("headline_actions", {}).get("research_closeout", []))

    badge_columns = st.columns(3)
    render_badge(
        badge_columns[0],
        label="Temperature Scaling",
        value=mitigation_labels.get("temperature_scaling", "unknown"),
    )
    render_actions(
        badge_columns[0],
        snapshot.get("headline_actions", {}).get("temperature_scaling", []),
    )
    render_badge(
        badge_columns[1],
        label="Reweighting",
        value=mitigation_labels.get("reweighting", "unknown"),
    )
    render_actions(
        badge_columns[1],
        snapshot.get("headline_actions", {}).get("reweighting", []),
    )
    render_badge(
        badge_columns[2],
        label="Dataset Expansion",
        value=snapshot.get("dataset_expansion_recommendation", "unknown"),
    )
    render_actions(
        badge_columns[2],
        snapshot.get("headline_actions", {}).get("dataset_expansion", []),
    )

    if snapshot.get("final_robustness_verdict"):
        st.subheader("Final Closeout")
        st.markdown(
            f"**Final robustness verdict:** "
            f"{format_label(snapshot.get('final_robustness_verdict'))}"
        )
        st.markdown(
            f"**Expansion gate:** "
            f"{format_label(snapshot.get('dataset_expansion_recommendation'))}"
        )
        reopen_conditions = snapshot.get("reopen_conditions", [])
        if reopen_conditions:
            st.markdown("**Reopen conditions**")
            st.markdown("\n".join(f"- {condition}" for condition in reopen_conditions))

    st.subheader("Inventory")
    inventory_columns = st.columns(3)
    inventory_columns[0].metric("Official Runs", str(inventory_counts["runs"]))
    inventory_columns[1].metric("Official Evals", str(inventory_counts["evaluations"]))
    inventory_columns[2].metric("Official Reports", str(inventory_counts["reports"]))

    if seeded_cohorts:
        st.subheader("Aggregate Cohort Summary")
        render_metric_summary(
            st,
            seeded_cohorts[1].get("aggregate_metrics", {}).get("mean", {}),
            metric_keys=("id_macro_f1", "robustness_gap_f1", "worst_group_f1"),
        )
        render_actions(
            st,
            snapshot.get("headline_actions", {}).get("distilbert_baseline", []),
        )

    render_overview_charts(st, seeded_cohorts)

    st.subheader("Recommendation")
    st.markdown(
        f"**Recommendation:** {format_label(snapshot.get('dataset_expansion_recommendation'))}. "
        f"{snapshot.get('recommendation_reason', '')}"
    )
    if snapshot.get("next_step"):
        st.caption(snapshot["next_step"])
