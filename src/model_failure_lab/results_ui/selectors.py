"""Selectors and view-model helpers for the results explorer."""

from __future__ import annotations

from typing import Any, Iterable

from model_failure_lab.artifact_index.schema import PRIMARY_COHORT_ORDER

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


def get_seeded_cohorts(
    index: dict[str, Any],
    *,
    include_exploratory: bool = False,
) -> list[dict[str, Any]]:
    """Return seeded cohort views in their canonical display order."""
    cohorts = _filter_default_visible(
        index.get("views", {}).get("seeded_cohorts", []),
        include_exploratory=include_exploratory,
    )
    order = {cohort_id: idx for idx, cohort_id in enumerate(PRIMARY_COHORT_ORDER)}
    return sorted(
        cohorts,
        key=lambda cohort: (
            order.get(cohort.get("cohort_id", ""), len(order)),
            cohort.get("display_name", ""),
        ),
    )


def get_mitigation_comparison_views(
    index: dict[str, Any],
    *,
    include_exploratory: bool = False,
) -> list[dict[str, Any]]:
    """Return mitigation comparison views in a stable UI order."""
    views = _filter_default_visible(
        index.get("views", {}).get("mitigation_comparisons", []),
        include_exploratory=include_exploratory,
    )
    return sorted(
        views,
        key=lambda view: (
            _MITIGATION_ORDER.get(view.get("mitigation_method", ""), len(_MITIGATION_ORDER)),
            view.get("mitigation_method", ""),
        ),
    )


def get_primary_stability_package(
    index: dict[str, Any],
    *,
    include_exploratory: bool = False,
) -> dict[str, Any]:
    """Return the default-visible milestone stability package."""
    packages = _filter_default_visible(
        index.get("views", {}).get("stability_packages", []),
        include_exploratory=include_exploratory,
    )
    if not packages:
        raise ValueError("No stability package is available in the artifact index.")
    return packages[0]


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
    return {
        "seeded_cohorts": seeded_cohorts,
        "mitigation_views": mitigation_views,
        "stability_package": stability_package,
        "mitigation_labels": mitigation_labels,
        "dataset_expansion_recommendation": stability_package.get(
            "milestone_assessment",
            {},
        ).get("dataset_expansion_recommendation"),
        "recommendation_reason": stability_package.get("milestone_assessment", {}).get(
            "recommendation_reason"
        ),
        "next_step": stability_package.get("milestone_assessment", {}).get("next_step"),
        "cohort_labels": cohort_summaries,
        "inventory_counts": inventory_counts,
    }


def get_report_by_id(index: dict[str, Any], report_id: str) -> dict[str, Any] | None:
    """Return one report entity by ID."""
    return get_entity_lookup(index, "reports").get(report_id)
