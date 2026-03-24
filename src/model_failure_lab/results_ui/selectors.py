"""Selectors and view-model helpers for the results explorer."""

from __future__ import annotations

from typing import Any, Iterable

from model_failure_lab.artifact_index.schema import PRIMARY_COHORT_ORDER
from model_failure_lab.results_ui.formatters import (
    build_action,
    build_artifact_ref_action,
    build_bundle_action,
    extract_ref_path,
)

_MITIGATION_ORDER = {
    "temperature_scaling": 0,
    "reweighting": 1,
}


def _filter_default_visible(
    items: Iterable[dict[str, Any]],
    *,
    include_exploratory: bool,
) -> list[dict[str, Any]]:
    if include_exploratory:
        return list(items)
    return [item for item in items if item.get("default_visible", False)]


def get_default_visible_entities(
    index: dict[str, Any],
    entity_type: str,
    *,
    include_exploratory: bool = False,
) -> list[dict[str, Any]]:
    """Return the inventory entity slice the UI should show by default."""
    entities = index.get("entities", {}).get(entity_type, [])
    return _filter_default_visible(entities, include_exploratory=include_exploratory)


def get_entity_lookup(index: dict[str, Any], entity_type: str) -> dict[str, dict[str, Any]]:
    """Return an ID-indexed lookup for one entity family."""
    return {item["id"]: item for item in index.get("entities", {}).get(entity_type, [])}


def _get_primary_stability_package_data(
    index: dict[str, Any],
    *,
    include_exploratory: bool,
) -> dict[str, Any]:
    packages = _filter_default_visible(
        index.get("views", {}).get("stability_packages", []),
        include_exploratory=include_exploratory,
    )
    if not packages:
        raise ValueError("No stability package is available in the artifact index.")
    return packages[0]


def _get_primary_research_closeout_data(
    index: dict[str, Any],
    *,
    include_exploratory: bool,
) -> dict[str, Any] | None:
    packages = _filter_default_visible(
        index.get("views", {}).get("research_closeout", []),
        include_exploratory=include_exploratory,
    )
    if not packages:
        return None
    return packages[0]


def get_evaluation_by_id(index: dict[str, Any], eval_id: str) -> dict[str, Any] | None:
    """Return one evaluation entity by ID."""
    return get_entity_lookup(index, "evaluations").get(eval_id)


def get_seeded_cohorts(
    index: dict[str, Any],
    *,
    include_exploratory: bool = False,
) -> list[dict[str, Any]]:
    """Return seeded cohort views in their canonical display order."""
    raw_cohorts = _filter_default_visible(
        index.get("views", {}).get("seeded_cohorts", []),
        include_exploratory=include_exploratory,
    )
    order = {cohort_id: idx for idx, cohort_id in enumerate(PRIMARY_COHORT_ORDER)}
    stability_package = _get_primary_stability_package_data(
        index,
        include_exploratory=include_exploratory,
    )
    sorted_cohorts = sorted(
        raw_cohorts,
        key=lambda cohort: (
            order.get(cohort.get("cohort_id", ""), len(order)),
            cohort.get("display_name", ""),
        ),
    )
    return [
        {
            **cohort,
            "summary_actions": _build_cohort_summary_actions(index, cohort, stability_package),
        }
        for cohort in sorted_cohorts
    ]


def get_mitigation_comparison_views(
    index: dict[str, Any],
    *,
    include_exploratory: bool = False,
) -> list[dict[str, Any]]:
    """Return mitigation comparison views in a stable UI order."""
    raw_views = _filter_default_visible(
        index.get("views", {}).get("mitigation_comparisons", []),
        include_exploratory=include_exploratory,
    )
    sorted_views = sorted(
        raw_views,
        key=lambda view: (
            _MITIGATION_ORDER.get(view.get("mitigation_method", ""), len(_MITIGATION_ORDER)),
            view.get("mitigation_method", ""),
        ),
    )
    enriched_views: list[dict[str, Any]] = []
    for view in sorted_views:
        enriched_views.append(
            {
                **view,
                "summary_actions": _build_mitigation_summary_actions(index, view),
                "per_seed_comparisons": [
                    {
                        **comparison,
                        "support_actions": _build_per_seed_comparison_actions(index, comparison),
                    }
                    for comparison in view.get("per_seed_comparisons", [])
                ],
            }
        )
    return enriched_views


def get_primary_stability_package(
    index: dict[str, Any],
    *,
    include_exploratory: bool = False,
) -> dict[str, Any]:
    """Return the default-visible milestone stability package."""
    package = _get_primary_stability_package_data(
        index,
        include_exploratory=include_exploratory,
    )
    return {
        **package,
        "summary_actions": _build_stability_package_actions(index, package),
        "reference_actions": _build_stability_reference_actions(index, package),
    }


def get_primary_research_closeout(
    index: dict[str, Any],
    *,
    include_exploratory: bool = False,
) -> dict[str, Any] | None:
    """Return the default-visible final closeout package when available."""
    package = _get_primary_research_closeout_data(
        index,
        include_exploratory=include_exploratory,
    )
    if package is None:
        return None
    return {
        **package,
        "summary_actions": _build_research_closeout_actions(index, package),
    }


def build_overview_snapshot(
    index: dict[str, Any],
    *,
    include_exploratory: bool = False,
) -> dict[str, Any]:
    """Build the milestone-story snapshot used by the Overview page."""
    seeded_cohorts = get_seeded_cohorts(index, include_exploratory=include_exploratory)
    mitigation_views = get_mitigation_comparison_views(
        index,
        include_exploratory=include_exploratory,
    )
    stability_package = get_primary_stability_package(
        index,
        include_exploratory=include_exploratory,
    )
    research_closeout = get_primary_research_closeout(
        index,
        include_exploratory=include_exploratory,
    )
    cohort_summaries = stability_package.get("cohort_summaries", {})
    mitigation_labels = {
        view["mitigation_method"]: view.get("stability_assessment", {}).get("label", "unknown")
        for view in mitigation_views
    }
    inventory_counts = {
        "runs": len(
            get_default_visible_entities(
                index,
                "runs",
                include_exploratory=include_exploratory,
            )
        ),
        "evaluations": len(
            get_default_visible_entities(
                index,
                "evaluations",
                include_exploratory=include_exploratory,
            )
        ),
        "reports": len(
            get_default_visible_entities(
                index,
                "reports",
                include_exploratory=include_exploratory,
            )
        ),
    }
    findings_doc_action = build_action(
        label="Read v1.4 closeout",
        path=(
            str(research_closeout.get("findings_doc_path"))
            if research_closeout is not None and research_closeout.get("findings_doc_path")
            else "docs/v1_4_closeout.md"
        ),
    )
    mitigation_actions = {
        view["mitigation_method"]: view.get("summary_actions", [])
        for view in mitigation_views
    }
    distilbert_baseline_actions = next(
        (
            cohort.get("summary_actions", [])
            for cohort in seeded_cohorts
            if cohort.get("cohort_id") == "distilbert_baseline"
        ),
        [],
    )
    dataset_expansion_recommendation = stability_package.get(
        "milestone_assessment",
        {},
    ).get("dataset_expansion_recommendation")
    recommendation_reason = stability_package.get("milestone_assessment", {}).get(
        "recommendation_reason"
    )
    next_step = stability_package.get("milestone_assessment", {}).get("next_step")
    final_robustness_verdict = None
    reopen_conditions: list[str] = []
    research_closeout_actions: list[dict[str, str]] = []
    if research_closeout is not None:
        dataset_expansion_recommendation = research_closeout.get(
            "dataset_expansion_decision"
        ) or dataset_expansion_recommendation
        recommendation_reason = research_closeout.get("recommendation_reason") or (
            recommendation_reason
        )
        next_step = research_closeout.get("next_step") or next_step
        final_robustness_verdict = research_closeout.get("final_robustness_verdict")
        reopen_conditions = list(research_closeout.get("reopen_conditions", []))
        research_closeout_actions = list(research_closeout.get("summary_actions", []))
    return {
        "seeded_cohorts": seeded_cohorts,
        "mitigation_views": mitigation_views,
        "stability_package": stability_package,
        "research_closeout": research_closeout,
        "mitigation_labels": mitigation_labels,
        "final_robustness_verdict": final_robustness_verdict,
        "dataset_expansion_recommendation": dataset_expansion_recommendation,
        "recommendation_reason": recommendation_reason,
        "reopen_conditions": reopen_conditions,
        "next_step": next_step,
        "cohort_labels": cohort_summaries,
        "inventory_counts": inventory_counts,
        "headline_actions": {
            "temperature_scaling": mitigation_actions.get("temperature_scaling", []),
            "reweighting": mitigation_actions.get("reweighting", []),
            "dataset_expansion": (
                research_closeout_actions or stability_package.get("summary_actions", [])
            ),
            "research_closeout": research_closeout_actions,
            "distilbert_baseline": distilbert_baseline_actions,
            "findings_doc": [findings_doc_action] if findings_doc_action is not None else [],
        },
    }


def get_report_by_id(index: dict[str, Any], report_id: str) -> dict[str, Any] | None:
    """Return one report entity by ID."""
    return get_entity_lookup(index, "reports").get(report_id)


def _dedupe_actions(actions: Iterable[dict[str, str] | None]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for action in actions:
        if action is None:
            continue
        label = action.get("label")
        path = action.get("path")
        if not label or not path:
            continue
        key = (label, path)
        if key in seen:
            continue
        deduped.append(action)
        seen.add(key)
    return deduped


def _first_available_action(
    entity: dict[str, Any] | None,
    specs: Iterable[tuple[str, str]],
    *,
    source: str = "artifact_refs",
) -> dict[str, str] | None:
    if entity is None:
        return None
    for ref_key, label in specs:
        action = build_artifact_ref_action(
            entity,
            label=label,
            ref_key=ref_key,
            source=source,
        )
        if action is not None:
            return action
    return None


def _build_eval_support_actions(eval_entity: dict[str, Any] | None) -> list[dict[str, str]]:
    return _dedupe_actions(
        [
            build_bundle_action(eval_entity or {}, label="Open eval bundle"),
            _first_available_action(
                eval_entity,
                (
                    ("split_metrics_csv", "View raw metrics table"),
                    ("id_ood_comparison_csv", "View raw metrics table"),
                    ("subgroup_metrics_csv", "View raw metrics table"),
                ),
            ),
        ]
    )


def _build_report_support_actions(
    report_entity: dict[str, Any] | None,
    *,
    table_specs: Iterable[tuple[str, str]] = (),
    payload_specs: Iterable[tuple[str, str]] = (),
) -> list[dict[str, str]]:
    actions: list[dict[str, str] | None] = []
    if report_entity is not None:
        actions.append(
            build_artifact_ref_action(
                report_entity,
                label="View supporting report",
                ref_key="report_markdown",
            )
        )
        for ref_key, label in table_specs:
            actions.append(build_artifact_ref_action(report_entity, label=label, ref_key=ref_key))
        for ref_key, label in payload_specs:
            actions.append(
                build_artifact_ref_action(
                    report_entity,
                    label=label,
                    ref_key=ref_key,
                    source="payload_refs",
                )
            )
    return _dedupe_actions(actions)


def _build_cohort_summary_actions(
    index: dict[str, Any],
    cohort: dict[str, Any],
    stability_package: dict[str, Any],
) -> list[dict[str, str]]:
    eval_ids = cohort.get("evaluation_ids", [])
    eval_entity = get_evaluation_by_id(index, eval_ids[0]) if eval_ids else None
    if cohort.get("cohort_type") == "mitigation":
        report_entity = get_report_by_id(index, cohort.get("linked_report_id", ""))
        return _dedupe_actions(
            [
                *_build_report_support_actions(
                    report_entity,
                    table_specs=(
                        ("mitigation_comparison_table_csv", "View raw metrics table"),
                        ("comparison_table_csv", "View raw metrics table"),
                    ),
                ),
                *_build_eval_support_actions(eval_entity),
            ]
        )

    report_entity = get_report_by_id(index, stability_package.get("report_id", ""))
    return _dedupe_actions(
        [
            *_build_report_support_actions(
                report_entity,
                table_specs=(("baseline_stability_csv", "View raw metrics table"),),
            ),
            *_build_eval_support_actions(eval_entity),
        ]
    )


def _build_mitigation_summary_actions(
    index: dict[str, Any],
    view: dict[str, Any],
) -> list[dict[str, str]]:
    report_entity = get_report_by_id(index, view.get("aggregate_report_id", ""))
    child_eval_id = None
    if view.get("per_seed_comparisons"):
        child_eval_id = view["per_seed_comparisons"][0].get("child_eval_id")
    eval_entity = get_evaluation_by_id(index, child_eval_id or "")
    return _dedupe_actions(
        [
            *_build_report_support_actions(
                report_entity,
                table_specs=(
                    ("mitigation_comparison_table_csv", "View raw metrics table"),
                    ("comparison_table_csv", "View raw metrics table"),
                ),
            ),
            *_build_eval_support_actions(eval_entity),
        ]
    )


def _build_per_seed_comparison_actions(
    index: dict[str, Any],
    comparison: dict[str, Any],
) -> list[dict[str, str]]:
    report_id = next(iter(comparison.get("related_report_ids", [])), "")
    report_entity = get_report_by_id(index, report_id)
    eval_entity = get_evaluation_by_id(index, comparison.get("child_eval_id", ""))
    return _dedupe_actions(
        [
            *_build_report_support_actions(report_entity),
            *_build_eval_support_actions(eval_entity),
        ]
    )


def _build_stability_package_actions(
    index: dict[str, Any],
    package: dict[str, Any],
) -> list[dict[str, str]]:
    report_entity = get_report_by_id(index, package.get("report_id", ""))
    return _dedupe_actions(
        [
            *_build_report_support_actions(
                report_entity,
                table_specs=(
                    ("baseline_stability_csv", "View baseline stability table"),
                    ("temperature_scaling_deltas_csv", "View temperature-scaling deltas"),
                    ("reweighting_deltas_csv", "View reweighting deltas"),
                ),
                payload_specs=(("stability_summary_json", "View stability summary"),),
            ),
        ]
    )


def _build_stability_reference_actions(
    index: dict[str, Any],
    package: dict[str, Any],
) -> list[dict[str, str]]:
    actions: list[dict[str, str] | None] = []
    for scope, reference in package.get("reference_reports", {}).items():
        report_path = reference.get("path")
        label = f"View {scope.replace('_', ' ')} package"
        action = build_action(label=label, path=report_path)
        if action is not None:
            actions.append(action)
            continue
        report_entity = get_report_by_id(index, scope)
        actions.append(
            build_artifact_ref_action(
                report_entity or {},
                label=label,
                ref_key="report_markdown",
            )
        )
    return _dedupe_actions(actions)


def _build_research_closeout_actions(
    index: dict[str, Any],
    package: dict[str, Any],
) -> list[dict[str, str]]:
    artifact_refs = package.get("artifact_refs", {})
    actions: list[dict[str, str] | None] = [
        build_action(
            label="View final gate JSON",
            path=extract_ref_path(artifact_refs.get("final_gate_json")),
        ),
        build_action(
            label="View promotion audit",
            path=extract_ref_path(artifact_refs.get("promotion_audit_markdown")),
        ),
    ]
    for report_id in package.get("supporting_report_ids", []):
        report_entity = get_report_by_id(index, str(report_id))
        actions.extend(_build_report_support_actions(report_entity))
    return _dedupe_actions(actions)
