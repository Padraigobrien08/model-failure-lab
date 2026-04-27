"""Deterministic portfolio prioritization and saved lifecycle planning."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from model_failure_lab.index import QueryFilters, query_comparison_signals
from model_failure_lab.schemas import JsonValue
from model_failure_lab.storage import (
    portfolio_plan_file,
    portfolio_plans_root,
    project_root,
    read_json,
    write_json,
)

from .lifecycle import LifecycleApplyResult, apply_lifecycle_action, get_active_lifecycle_action
from .policy import (
    LifecycleRecommendation,
    describe_dataset_family_lifecycle,
    recommend_dataset_action,
)
from .workflow import DatasetFamilyHealth, list_dataset_family_health

if TYPE_CHECKING:
    from .outcomes import PortfolioOutcomeFeedbackSummary

_DEFAULT_PORTFOLIO_SCAN_LIMIT = 200
_MAX_COMPARISON_REFS = 5
_ACTIONABILITY_VALUES = {"all", "actionable", "neutral"}
_PRIORITY_BANDS = ("urgent", "high", "medium", "low")
_ACTION_WEIGHTS = {
    "keep": 0.0,
    "retire": 8.0,
    "merge_candidate": 10.0,
    "prune": 12.0,
}
_HEALTH_WEIGHTS = {
    "degrading": 10.0,
    "volatile": 8.0,
    "unevaluated": 4.0,
    "stable": 2.0,
    "improving": 1.0,
}


@dataclass(slots=True, frozen=True)
class PortfolioFilters:
    family_id: str | None = None
    model: str | None = None
    dataset: str | None = None
    failure_type: str | None = None
    actionability: str = "all"
    priority_band: str | None = None
    limit: int = 20

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "family_id": self.family_id,
            "model": self.model,
            "dataset": self.dataset,
            "failure_type": self.failure_type,
            "actionability": self.actionability,
            "priority_band": self.priority_band,
            "limit": self.limit,
        }


@dataclass(slots=True, frozen=True)
class PortfolioComparisonReference:
    comparison_id: str
    created_at: str
    dataset: str | None
    baseline_model: str | None
    candidate_model: str | None
    severity: float
    signal_verdict: str
    recurring_cluster_ids: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "comparison_id": self.comparison_id,
            "created_at": self.created_at,
            "dataset": self.dataset,
            "baseline_model": self.baseline_model,
            "candidate_model": self.candidate_model,
            "severity": round(self.severity, 6),
            "signal_verdict": self.signal_verdict,
            "recurring_cluster_ids": list(self.recurring_cluster_ids),
        }


@dataclass(slots=True, frozen=True)
class DatasetPortfolioItem:
    family_id: str
    priority_rank: int
    priority_band: str
    priority_score: float
    actionability: str
    rationale: str
    lifecycle_action: str
    health_condition: str
    health_label: str
    trend_label: str
    version_count: int
    latest_dataset_id: str
    latest_version_tag: str
    latest_comparison_id: str | None
    source_dataset_id: str | None
    primary_failure_type: str | None
    recent_fail_rate: float | None
    projected_case_count: int | None
    escalation_status: str | None
    escalation_score: float | None
    recent_regression_count: int
    recurring_cluster_count: int
    target_family_id: str | None = None
    related_family_ids: tuple[str, ...] = ()
    comparison_refs: tuple[PortfolioComparisonReference, ...] = ()
    cluster_ids: tuple[str, ...] = ()
    datasets: tuple[str, ...] = ()
    models: tuple[str, ...] = ()
    active_lifecycle_action_id: str | None = None
    active_lifecycle_action: str | None = None
    active_lifecycle_condition: str | None = None
    active_lifecycle_applied_at: str | None = None
    outcome_feedback: PortfolioOutcomeFeedbackSummary | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "family_id": self.family_id,
            "priority_rank": self.priority_rank,
            "priority_band": self.priority_band,
            "priority_score": round(self.priority_score, 6),
            "actionability": self.actionability,
            "rationale": self.rationale,
            "lifecycle_action": self.lifecycle_action,
            "health_condition": self.health_condition,
            "health_label": self.health_label,
            "trend_label": self.trend_label,
            "version_count": self.version_count,
            "latest_dataset_id": self.latest_dataset_id,
            "latest_version_tag": self.latest_version_tag,
            "latest_comparison_id": self.latest_comparison_id,
            "source_dataset_id": self.source_dataset_id,
            "primary_failure_type": self.primary_failure_type,
            "recent_fail_rate": (
                round(self.recent_fail_rate, 6) if self.recent_fail_rate is not None else None
            ),
            "projected_case_count": self.projected_case_count,
            "escalation_status": self.escalation_status,
            "escalation_score": (
                round(self.escalation_score, 6) if self.escalation_score is not None else None
            ),
            "recent_regression_count": self.recent_regression_count,
            "recurring_cluster_count": self.recurring_cluster_count,
            "target_family_id": self.target_family_id,
            "related_family_ids": list(self.related_family_ids),
            "comparison_refs": [row.to_payload() for row in self.comparison_refs],
            "cluster_ids": list(self.cluster_ids),
            "datasets": list(self.datasets),
            "models": list(self.models),
            "active_lifecycle_action_id": self.active_lifecycle_action_id,
            "active_lifecycle_action": self.active_lifecycle_action,
            "active_lifecycle_condition": self.active_lifecycle_condition,
            "active_lifecycle_applied_at": self.active_lifecycle_applied_at,
            "outcome_feedback": (
                self.outcome_feedback.to_payload() if self.outcome_feedback is not None else None
            ),
        }


@dataclass(slots=True, frozen=True)
class PlanningUnitMember:
    family_id: str
    priority_rank: int
    priority_band: str
    priority_score: float
    actionability: str
    lifecycle_action: str
    health_condition: str
    version_count: int = 0
    source_dataset_id: str | None = None
    primary_failure_type: str | None = None
    latest_dataset_id: str | None = None
    projected_case_count: int | None = None
    recent_fail_rate: float | None = None
    datasets: tuple[str, ...] = ()
    models: tuple[str, ...] = ()
    target_family_id: str | None = None
    related_family_ids: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "family_id": self.family_id,
            "priority_rank": self.priority_rank,
            "priority_band": self.priority_band,
            "priority_score": round(self.priority_score, 6),
            "actionability": self.actionability,
            "lifecycle_action": self.lifecycle_action,
            "health_condition": self.health_condition,
            "version_count": self.version_count,
            "source_dataset_id": self.source_dataset_id,
            "primary_failure_type": self.primary_failure_type,
            "latest_dataset_id": self.latest_dataset_id,
            "projected_case_count": self.projected_case_count,
            "recent_fail_rate": (
                round(self.recent_fail_rate, 6) if self.recent_fail_rate is not None else None
            ),
            "datasets": list(self.datasets),
            "models": list(self.models),
            "target_family_id": self.target_family_id,
            "related_family_ids": list(self.related_family_ids),
        }


@dataclass(slots=True, frozen=True)
class DatasetPlanningUnit:
    unit_id: str
    unit_kind: str
    priority_band: str
    priority_score: float
    rationale: str
    family_ids: tuple[str, ...]
    comparison_ids: tuple[str, ...]
    cluster_ids: tuple[str, ...]
    members: tuple[PlanningUnitMember, ...]

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "unit_id": self.unit_id,
            "unit_kind": self.unit_kind,
            "priority_band": self.priority_band,
            "priority_score": round(self.priority_score, 6),
            "rationale": self.rationale,
            "family_ids": list(self.family_ids),
            "comparison_ids": list(self.comparison_ids),
            "cluster_ids": list(self.cluster_ids),
            "members": [member.to_payload() for member in self.members],
        }


@dataclass(slots=True, frozen=True)
class PortfolioPlanAction:
    family_id: str
    action: str
    health_condition: str
    rationale: str
    priority_rank: int
    priority_band: str
    priority_score: float
    version_count: int = 0
    source_dataset_id: str | None = None
    primary_failure_type: str | None = None
    latest_dataset_id: str | None = None
    projected_case_count: int | None = None
    target_family_id: str | None = None
    related_family_ids: tuple[str, ...] = ()
    dependency_family_ids: tuple[str, ...] = ()
    comparison_ids: tuple[str, ...] = ()
    cluster_ids: tuple[str, ...] = ()
    datasets: tuple[str, ...] = ()
    models: tuple[str, ...] = ()
    recent_fail_rate: float | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "family_id": self.family_id,
            "action": self.action,
            "health_condition": self.health_condition,
            "rationale": self.rationale,
            "priority_rank": self.priority_rank,
            "priority_band": self.priority_band,
            "priority_score": round(self.priority_score, 6),
            "version_count": self.version_count,
            "source_dataset_id": self.source_dataset_id,
            "primary_failure_type": self.primary_failure_type,
            "latest_dataset_id": self.latest_dataset_id,
            "projected_case_count": self.projected_case_count,
            "target_family_id": self.target_family_id,
            "related_family_ids": list(self.related_family_ids),
            "dependency_family_ids": list(self.dependency_family_ids),
            "comparison_ids": list(self.comparison_ids),
            "cluster_ids": list(self.cluster_ids),
            "datasets": list(self.datasets),
            "models": list(self.models),
            "recent_fail_rate": (
                round(self.recent_fail_rate, 6) if self.recent_fail_rate is not None else None
            ),
        }


@dataclass(slots=True, frozen=True)
class PortfolioPlanImpact:
    affected_family_count: int
    action_count: int
    projected_case_count: int
    action_counts: dict[str, int]

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "affected_family_count": self.affected_family_count,
            "action_count": self.action_count,
            "projected_case_count": self.projected_case_count,
            "action_counts": dict(self.action_counts),
        }


@dataclass(slots=True, frozen=True)
class SavedPortfolioPlan:
    plan_id: str
    created_at: str
    status: str
    rationale: str
    filters: PortfolioFilters
    family_ids: tuple[str, ...]
    datasets: tuple[str, ...]
    models: tuple[str, ...]
    failure_types: tuple[str, ...]
    priority_bands: tuple[str, ...]
    units: tuple[DatasetPlanningUnit, ...]
    actions: tuple[PortfolioPlanAction, ...]
    impact: PortfolioPlanImpact

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "plan_id": self.plan_id,
            "created_at": self.created_at,
            "status": self.status,
            "rationale": self.rationale,
            "filters": self.filters.to_payload(),
            "family_ids": list(self.family_ids),
            "datasets": list(self.datasets),
            "models": list(self.models),
            "failure_types": list(self.failure_types),
            "priority_bands": list(self.priority_bands),
            "units": [unit.to_payload() for unit in self.units],
            "actions": [action.to_payload() for action in self.actions],
            "impact": self.impact.to_payload(),
        }


@dataclass(slots=True, frozen=True)
class PortfolioPlanSaveResult:
    status: str
    output_path: Path
    plan: SavedPortfolioPlan

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "status": self.status,
            "output_path": str(self.output_path),
            "plan": self.plan.to_payload(),
        }


@dataclass(slots=True, frozen=True)
class PortfolioPlanApplyResult:
    plan_id: str
    family_id: str
    action: str
    status: str
    result: LifecycleApplyResult

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "plan_id": self.plan_id,
            "family_id": self.family_id,
            "action": self.action,
            "status": self.status,
            "result": self.result.to_payload(),
        }


@dataclass(slots=True, frozen=True)
class _FamilyPortfolioEvidence:
    comparison_refs: tuple[PortfolioComparisonReference, ...]
    cluster_ids: tuple[str, ...]
    datasets: tuple[str, ...]
    models: tuple[str, ...]
    recent_regression_count: int
    escalation_status: str | None
    escalation_score: float | None


def list_dataset_portfolio(
    *,
    root: str | Path | None = None,
    filters: PortfolioFilters | None = None,
) -> tuple[DatasetPortfolioItem, ...]:
    active_root = project_root(root).resolve()
    normalized = _normalize_filters(filters)
    family_rows = list_dataset_family_health(root=active_root)
    if normalized.family_id is not None:
        family_rows = tuple(
            row for row in family_rows if row.family_id == normalized.family_id
        )
    if not family_rows:
        return ()

    evidence_by_family = _build_family_evidence(
        root=active_root,
        family_ids={row.family_id for row in family_rows},
        filters=normalized,
    )
    ranked: list[DatasetPortfolioItem] = []
    for family in family_rows:
        recommendation = describe_dataset_family_lifecycle(
            family.family_id,
            root=active_root,
            projected_case_count=family.latest_case_count,
        )
        if recommendation is None:
            continue
        item = _build_portfolio_item(
            family,
            recommendation=recommendation,
            evidence=evidence_by_family.get(family.family_id),
            root=active_root,
        )
        ranked.append(item)

    ranked.sort(
        key=lambda item: (
            -item.priority_score,
            _priority_band_index(item.priority_band),
            -(item.escalation_score or 0.0),
            -item.version_count,
            item.family_id,
        )
    )
    ranked = [
        replace(item, priority_rank=index)
        for index, item in enumerate(ranked, start=1)
    ]
    filtered = [item for item in ranked if _portfolio_item_matches(item, normalized)]
    return tuple(filtered[: max(normalized.limit, 1)])


def get_dataset_portfolio_item(
    family_id: str,
    *,
    root: str | Path | None = None,
) -> DatasetPortfolioItem | None:
    rows = list_dataset_portfolio(
        root=root,
        filters=PortfolioFilters(family_id=family_id, limit=1),
    )
    return rows[0] if rows else None


def list_dataset_planning_units(
    *,
    root: str | Path | None = None,
    filters: PortfolioFilters | None = None,
) -> tuple[DatasetPlanningUnit, ...]:
    items = list_dataset_portfolio(root=root, filters=filters)
    if not items:
        return ()
    item_map = {item.family_id: item for item in items}
    remaining = set(item_map)
    units: list[DatasetPlanningUnit] = []
    seen_units: set[str] = set()

    for item in items:
        if item.family_id not in remaining:
            continue
        member_ids = tuple(
            sorted(
                {
                    item.family_id,
                    *(entry for entry in item.related_family_ids if entry in item_map),
                    *(
                        (item.target_family_id,)
                        if item.target_family_id is not None and item.target_family_id in item_map
                        else ()
                    ),
                }
            )
        )
        if item.lifecycle_action != "merge_candidate" or len(member_ids) < 2:
            continue
        unit_id = f"merge:{'+'.join(member_ids)}"
        if unit_id in seen_units:
            continue
        units.append(
            _build_planning_unit(
                unit_id=unit_id,
                unit_kind="merge_review",
                family_ids=member_ids,
                rationale=(
                    "Families share deterministic merge-candidate provenance and should be "
                    "reviewed together before any lifecycle action is promoted."
                ),
                item_map=item_map,
            )
        )
        seen_units.add(unit_id)
        remaining.difference_update(member_ids)

    grouped: dict[tuple[str, str], list[str]] = {}
    for family_id in sorted(remaining):
        item = item_map[family_id]
        if item.source_dataset_id is None or item.primary_failure_type is None:
            continue
        grouped.setdefault(
            (item.source_dataset_id, item.primary_failure_type),
            [],
        ).append(family_id)
    for (source_dataset_id, failure_type), family_ids in sorted(grouped.items()):
        if len(family_ids) < 2:
            continue
        unit_id = f"related:{source_dataset_id}:{failure_type}"
        units.append(
            _build_planning_unit(
                unit_id=unit_id,
                unit_kind="related_family_review",
                family_ids=tuple(sorted(family_ids)),
                rationale=(
                    f"Families share source dataset `{source_dataset_id}` and primary failure "
                    f"type `{failure_type}`, so they should be reviewed as one explicit planning "
                    "unit."
                ),
                item_map=item_map,
            )
        )
        remaining.difference_update(family_ids)

    for family_id in sorted(remaining):
        units.append(
            _build_planning_unit(
                unit_id=f"family:{family_id}",
                unit_kind="family_review",
                family_ids=(family_id,),
                rationale="Family remains a standalone review unit in the current portfolio queue.",
                item_map=item_map,
            )
        )

    return tuple(
        sorted(
            units,
            key=lambda unit: (-unit.priority_score, _priority_band_index(unit.priority_band), unit.unit_id),
        )
    )


def create_saved_portfolio_plan(
    *,
    root: str | Path | None = None,
    filters: PortfolioFilters | None = None,
    max_units: int = 5,
    max_actions: int = 10,
    include_keep: bool = False,
) -> PortfolioPlanSaveResult:
    active_root = project_root(root).resolve()
    normalized = _normalize_filters(filters)
    planning_units = list_dataset_planning_units(root=active_root, filters=normalized)
    selected_units: list[DatasetPlanningUnit] = []
    selected_actions: list[PortfolioPlanAction] = []
    for unit in planning_units:
        if len(selected_units) >= max(max_units, 1):
            break
        unit_actions = [
            _build_plan_action(unit, member)
            for member in unit.members
            if include_keep or member.lifecycle_action != "keep"
        ]
        if not unit_actions:
            continue
        if selected_actions and len(selected_actions) + len(unit_actions) > max(max_actions, 1):
            continue
        if not selected_actions and len(unit_actions) > max(max_actions, 1):
            unit_actions = unit_actions[: max(max_actions, 1)]
        selected_units.append(
            replace(
                unit,
                members=tuple(
                    member
                    for member in unit.members
                    if any(action.family_id == member.family_id for action in unit_actions)
                ),
                family_ids=tuple(action.family_id for action in unit_actions),
            )
        )
        selected_actions.extend(unit_actions)
    if not selected_actions:
        raise ValueError("no portfolio actions matched the current filters")

    selected_units = [
        _rebuild_planning_unit_links(unit, actions=selected_actions)
        for unit in selected_units
    ]
    plan_id = _build_plan_id(
        filters=normalized,
        units=selected_units,
        actions=selected_actions,
    )
    output_path = portfolio_plan_file(plan_id, root=active_root, create=True)
    if output_path.exists():
        return PortfolioPlanSaveResult(
            status="already_exists",
            output_path=output_path,
            plan=_saved_plan_from_payload(read_json(output_path)),
        )

    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    plan = SavedPortfolioPlan(
        plan_id=plan_id,
        created_at=created_at,
        status="draft",
        rationale=(
            f"Saved deterministic portfolio draft covering {len(selected_units)} planning units "
            f"and {len(selected_actions)} family actions."
        ),
        filters=normalized,
        family_ids=tuple(sorted(action.family_id for action in selected_actions)),
        datasets=_sorted_unique(
            dataset
            for action in selected_actions
            for dataset in action.datasets
        ),
        models=_sorted_unique(
            model
            for action in selected_actions
            for model in action.models
        ),
        failure_types=_sorted_unique(
            failure_type
            for action in selected_actions
            for failure_type in [action.primary_failure_type]
            if failure_type is not None
        ),
        priority_bands=_sorted_priority_bands(
            action.priority_band for action in selected_actions
        ),
        units=tuple(selected_units),
        actions=tuple(selected_actions),
        impact=PortfolioPlanImpact(
            affected_family_count=len({action.family_id for action in selected_actions}),
            action_count=len(selected_actions),
            projected_case_count=sum(
                member.projected_case_count or 0
                for unit in selected_units
                for member in unit.members
            ),
            action_counts={
                action_name: sum(
                    1 for action in selected_actions if action.action == action_name
                )
                for action_name in ("keep", "prune", "merge_candidate", "retire")
            },
        ),
    )
    write_json(output_path, plan.to_payload())
    return PortfolioPlanSaveResult(
        status="saved",
        output_path=output_path,
        plan=plan,
    )


def list_saved_portfolio_plans(
    *,
    root: str | Path | None = None,
    filters: PortfolioFilters | None = None,
) -> tuple[SavedPortfolioPlan, ...]:
    active_root = project_root(root).resolve()
    normalized = _normalize_filters(filters)
    plan_root = portfolio_plans_root(root=active_root, create=False)
    if not plan_root.exists():
        return ()
    rows: list[SavedPortfolioPlan] = []
    for artifact_path in sorted(plan_root.glob("*.json")):
        plan = _saved_plan_from_payload(read_json(artifact_path))
        if _saved_plan_matches(plan, normalized):
            rows.append(plan)
    rows.sort(key=lambda plan: (plan.created_at, plan.plan_id), reverse=True)
    return tuple(rows[: max(normalized.limit, 1)])


def get_saved_portfolio_plan(
    plan_id: str,
    *,
    root: str | Path | None = None,
) -> SavedPortfolioPlan | None:
    artifact_path = portfolio_plan_file(plan_id, root=project_root(root), create=False)
    if not artifact_path.exists():
        return None
    return _saved_plan_from_payload(read_json(artifact_path))


def apply_saved_portfolio_plan_action(
    plan_id: str,
    family_id: str,
    *,
    root: str | Path | None = None,
    source: str = "cli",
) -> PortfolioPlanApplyResult:
    active_root = project_root(root).resolve()
    plan = get_saved_portfolio_plan(plan_id, root=active_root)
    if plan is None:
        raise ValueError(f"portfolio plan not found: {plan_id}")
    action = next((row for row in plan.actions if row.family_id == family_id), None)
    if action is None:
        raise ValueError(f"portfolio plan {plan_id} does not contain family {family_id}")
    recommendation = LifecycleRecommendation(
        family_id=action.family_id,
        action=action.action,
        health_condition=action.health_condition,
        rationale=action.rationale,
        target_family_id=action.target_family_id,
        related_family_ids=action.related_family_ids,
        source_dataset_id=action.source_dataset_id,
        primary_failure_type=action.primary_failure_type,
        latest_dataset_id=action.latest_dataset_id,
        version_count=action.version_count,
        recent_fail_rate=action.recent_fail_rate,
        projected_case_count=action.projected_case_count,
    )
    result = apply_lifecycle_action(
        family_id=family_id,
        recommendation=recommendation,
        root=active_root,
        action=action.action,
        source=f"portfolio-plan:{plan_id}:{source}",
    )
    return PortfolioPlanApplyResult(
        plan_id=plan_id,
        family_id=family_id,
        action=action.action,
        status=result.status,
        result=result,
    )


def _build_family_evidence(
    *,
    root: Path,
    family_ids: set[str],
    filters: PortfolioFilters,
) -> dict[str, _FamilyPortfolioEvidence]:
    comparison_rows = query_comparison_signals(
        QueryFilters(
            model=filters.model,
            dataset=filters.dataset,
            failure_type=filters.failure_type,
            limit=max(filters.limit * 10, _DEFAULT_PORTFOLIO_SCAN_LIMIT),
        ),
        verdict=None,
        root=root,
    )
    grouped: dict[str, list[tuple[PortfolioComparisonReference, str | None, float | None, int]]] = {}
    for row in comparison_rows:
        recommendation = recommend_dataset_action(str(row["report_id"]), root=root)
        family_id = recommendation.matched_family.family_id
        if family_id not in family_ids:
            continue
        cluster_ids = tuple(
            sorted({cluster.cluster_id for cluster in recommendation.cluster_context})
        )
        reference = PortfolioComparisonReference(
            comparison_id=str(row["report_id"]),
            created_at=str(row["created_at"]),
            dataset=_string_or_none(row.get("dataset")),
            baseline_model=_string_or_none(row.get("baseline_model")),
            candidate_model=_string_or_none(row.get("candidate_model")),
            severity=_float_or_zero(row.get("severity")),
            signal_verdict=str(row.get("signal_verdict") or "unknown"),
            recurring_cluster_ids=cluster_ids,
        )
        grouped.setdefault(family_id, []).append(
            (
                reference,
                recommendation.escalation.status if recommendation.escalation is not None else None,
                recommendation.escalation.score if recommendation.escalation is not None else None,
                (
                    recommendation.history_context.recent_regression_count
                    if recommendation.history_context is not None
                    else 0
                ),
            )
        )

    evidence: dict[str, _FamilyPortfolioEvidence] = {}
    for family_id, entries in grouped.items():
        entries.sort(
            key=lambda entry: (
                -(entry[2] or 0.0),
                -entry[0].severity,
                entry[0].comparison_id,
            )
        )
        comparison_refs = tuple(entry[0] for entry in entries[:_MAX_COMPARISON_REFS])
        cluster_ids = _sorted_unique(
            cluster_id
            for reference in comparison_refs
            for cluster_id in reference.recurring_cluster_ids
        )
        datasets = _sorted_unique(
            dataset
            for reference in comparison_refs
            for dataset in [reference.dataset]
            if dataset is not None
        )
        models = _sorted_unique(
            model
            for reference in comparison_refs
            for model in (reference.baseline_model, reference.candidate_model)
            if model is not None
        )
        evidence[family_id] = _FamilyPortfolioEvidence(
            comparison_refs=comparison_refs,
            cluster_ids=cluster_ids,
            datasets=datasets,
            models=models,
            recent_regression_count=max(entry[3] for entry in entries),
            escalation_status=entries[0][1],
            escalation_score=entries[0][2],
        )
    return evidence


def _build_portfolio_item(
    family: DatasetFamilyHealth,
    *,
    recommendation: LifecycleRecommendation,
    evidence: _FamilyPortfolioEvidence | None,
    root: Path,
) -> DatasetPortfolioItem:
    from .outcomes import summarize_portfolio_outcomes_for_family

    active_action = get_active_lifecycle_action(family.family_id, root=root)
    outcome_feedback = summarize_portfolio_outcomes_for_family(family.family_id, root=root)
    priority_score = _priority_score(
        family=family,
        recommendation=recommendation,
        evidence=evidence,
        outcome_feedback=outcome_feedback,
    )
    priority_band = _priority_band(priority_score)
    actionability = "actionable" if recommendation.action != "keep" else "neutral"
    datasets = (
        evidence.datasets
        if evidence is not None and evidence.datasets
        else ((family.source_dataset_id,) if family.source_dataset_id is not None else ())
    )
    models = evidence.models if evidence is not None else ()
    cluster_ids = evidence.cluster_ids if evidence is not None else ()
    comparison_refs = evidence.comparison_refs if evidence is not None else ()
    recent_regression_count = evidence.recent_regression_count if evidence is not None else 0
    recurring_cluster_count = len(cluster_ids)
    escalation_status = evidence.escalation_status if evidence is not None else None
    escalation_score = evidence.escalation_score if evidence is not None else None
    rationale_parts = [
        f"lifecycle={recommendation.action}",
        f"health={family.health_label}",
    ]
    if escalation_status is not None and escalation_score is not None:
        rationale_parts.append(f"escalation={escalation_status} ({escalation_score:.3f})")
    if recent_regression_count:
        rationale_parts.append(f"recent_regressions={recent_regression_count}")
    if recurring_cluster_count:
        rationale_parts.append(f"recurring_clusters={recurring_cluster_count}")
    if outcome_feedback is not None:
        rationale_parts.append(
            f"outcomes={outcome_feedback.attested_count} attested/{outcome_feedback.open_count + outcome_feedback.evidence_linked_count} open"
        )
        if outcome_feedback.latest_verdict is not None:
            rationale_parts.append(f"latest_outcome={outcome_feedback.latest_verdict}")
    return DatasetPortfolioItem(
        family_id=family.family_id,
        priority_rank=0,
        priority_band=priority_band,
        priority_score=priority_score,
        actionability=actionability,
        rationale=", ".join(rationale_parts),
        lifecycle_action=recommendation.action,
        health_condition=recommendation.health_condition,
        health_label=family.health_label,
        trend_label=family.trend_label,
        version_count=family.version_count,
        latest_dataset_id=family.latest_dataset_id,
        latest_version_tag=family.latest_version_tag,
        latest_comparison_id=family.latest_comparison_id,
        source_dataset_id=family.source_dataset_id,
        primary_failure_type=family.primary_failure_type,
        recent_fail_rate=family.recent_fail_rate,
        projected_case_count=recommendation.projected_case_count,
        escalation_status=escalation_status,
        escalation_score=escalation_score,
        recent_regression_count=recent_regression_count,
        recurring_cluster_count=recurring_cluster_count,
        target_family_id=recommendation.target_family_id,
        related_family_ids=recommendation.related_family_ids,
        comparison_refs=comparison_refs,
        cluster_ids=cluster_ids,
        datasets=datasets,
        models=models,
        active_lifecycle_action_id=active_action.action_id if active_action is not None else None,
        active_lifecycle_action=family.active_lifecycle_action,
        active_lifecycle_condition=family.active_lifecycle_condition,
        active_lifecycle_applied_at=family.active_lifecycle_applied_at,
        outcome_feedback=outcome_feedback,
    )


def _priority_score(
    *,
    family: DatasetFamilyHealth,
    recommendation: LifecycleRecommendation,
    evidence: _FamilyPortfolioEvidence | None,
    outcome_feedback: PortfolioOutcomeFeedbackSummary | None,
) -> float:
    score = _ACTION_WEIGHTS.get(recommendation.action, 0.0)
    score += _HEALTH_WEIGHTS.get(family.health_label, 0.0)
    score += min(family.version_count, 6) * 1.5
    score += (family.recent_fail_rate or 0.0) * 20.0
    score += (family.latest_severity or 0.0) * 35.0
    if evidence is not None:
        score += (evidence.escalation_score or 0.0) * 100.0
        score += min(evidence.recent_regression_count, 5) * 4.0
        score += min(len(evidence.cluster_ids), 4) * 3.0
    if outcome_feedback is not None:
        score += min(outcome_feedback.regressed_count, 3) * 4.0
        score -= min(outcome_feedback.improved_count, 3) * 2.5
        score += min(outcome_feedback.evidence_linked_count, 2) * 1.0
        if outcome_feedback.latest_state == "open":
            score += 1.0
    if family.active_lifecycle_action is not None and family.active_lifecycle_action != recommendation.action:
        score += 2.0
    return round(score, 6)


def _build_planning_unit(
    *,
    unit_id: str,
    unit_kind: str,
    family_ids: tuple[str, ...],
    rationale: str,
    item_map: dict[str, DatasetPortfolioItem],
) -> DatasetPlanningUnit:
    members = tuple(
        sorted(
            (
                PlanningUnitMember(
                    family_id=item_map[family_id].family_id,
                    priority_rank=item_map[family_id].priority_rank,
                    priority_band=item_map[family_id].priority_band,
                    priority_score=item_map[family_id].priority_score,
                    actionability=item_map[family_id].actionability,
                    lifecycle_action=item_map[family_id].lifecycle_action,
                    health_condition=item_map[family_id].health_condition,
                    version_count=item_map[family_id].version_count,
                    source_dataset_id=item_map[family_id].source_dataset_id,
                    primary_failure_type=item_map[family_id].primary_failure_type,
                    latest_dataset_id=item_map[family_id].latest_dataset_id,
                    projected_case_count=item_map[family_id].projected_case_count,
                    recent_fail_rate=item_map[family_id].recent_fail_rate,
                    datasets=item_map[family_id].datasets,
                    models=item_map[family_id].models,
                    target_family_id=item_map[family_id].target_family_id,
                    related_family_ids=item_map[family_id].related_family_ids,
                )
                for family_id in family_ids
            ),
            key=lambda member: (member.priority_rank, member.family_id),
        )
    )
    comparison_ids = _sorted_unique(
        reference.comparison_id
        for family_id in family_ids
        for reference in item_map[family_id].comparison_refs
    )
    cluster_ids = _sorted_unique(
        cluster_id
        for family_id in family_ids
        for cluster_id in item_map[family_id].cluster_ids
    )
    highest = sorted(
        (item_map[family_id] for family_id in family_ids),
        key=lambda item: (item.priority_rank, item.family_id),
    )[0]
    return DatasetPlanningUnit(
        unit_id=unit_id,
        unit_kind=unit_kind,
        priority_band=highest.priority_band,
        priority_score=highest.priority_score,
        rationale=rationale,
        family_ids=family_ids,
        comparison_ids=comparison_ids,
        cluster_ids=cluster_ids,
        members=members,
    )


def _build_plan_action(
    unit: DatasetPlanningUnit,
    member: PlanningUnitMember,
) -> PortfolioPlanAction:
    dependency_family_ids = tuple(
        sorted(
            family_id
            for family_id in {*(member.related_family_ids), *( (member.target_family_id,) if member.target_family_id is not None else ())}
            if family_id != member.family_id and family_id in unit.family_ids
        )
    )
    return PortfolioPlanAction(
        family_id=member.family_id,
        action=member.lifecycle_action,
        health_condition=member.health_condition,
        rationale=unit.rationale,
        priority_rank=member.priority_rank,
        priority_band=member.priority_band,
        priority_score=member.priority_score,
        version_count=member.version_count,
        source_dataset_id=member.source_dataset_id,
        primary_failure_type=member.primary_failure_type,
        latest_dataset_id=member.latest_dataset_id,
        projected_case_count=member.projected_case_count,
        target_family_id=member.target_family_id,
        related_family_ids=member.related_family_ids,
        dependency_family_ids=dependency_family_ids,
        comparison_ids=unit.comparison_ids,
        cluster_ids=unit.cluster_ids,
        datasets=member.datasets,
        models=member.models,
        recent_fail_rate=member.recent_fail_rate,
    )


def _rebuild_planning_unit_links(
    unit: DatasetPlanningUnit,
    *,
    actions: list[PortfolioPlanAction],
) -> DatasetPlanningUnit:
    action_lookup = {action.family_id: action for action in actions}
    family_ids = tuple(
        family_id for family_id in unit.family_ids if family_id in action_lookup
    )
    members = tuple(member for member in unit.members if member.family_id in action_lookup)
    comparison_ids = _sorted_unique(
        comparison_id
        for family_id in family_ids
        for comparison_id in action_lookup[family_id].comparison_ids
    )
    cluster_ids = _sorted_unique(
        cluster_id
        for family_id in family_ids
        for cluster_id in action_lookup[family_id].cluster_ids
    )
    return replace(
        unit,
        family_ids=family_ids,
        comparison_ids=comparison_ids,
        cluster_ids=cluster_ids,
        members=members,
    )


def _build_plan_id(
    *,
    filters: PortfolioFilters,
    units: list[DatasetPlanningUnit],
    actions: list[PortfolioPlanAction],
) -> str:
    digest = hashlib.sha1(
        json.dumps(
            {
                "filters": filters.to_payload(),
                "units": [unit.to_payload() for unit in units],
                "actions": [action.to_payload() for action in actions],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:16]
    return f"portfolio-plan-{digest}"


def _saved_plan_from_payload(payload: dict[str, JsonValue]) -> SavedPortfolioPlan:
    filters_payload = _mapping_or_empty(payload.get("filters"))
    return SavedPortfolioPlan(
        plan_id=str(payload.get("plan_id", "")),
        created_at=str(payload.get("created_at", "")),
        status=str(payload.get("status", "")),
        rationale=str(payload.get("rationale", "")),
        filters=PortfolioFilters(
            family_id=_string_or_none(filters_payload.get("family_id")),
            model=_string_or_none(filters_payload.get("model")),
            dataset=_string_or_none(filters_payload.get("dataset")),
            failure_type=_string_or_none(filters_payload.get("failure_type")),
            actionability=_string_or_none(filters_payload.get("actionability")) or "all",
            priority_band=_string_or_none(filters_payload.get("priority_band")),
            limit=_int_or_default(filters_payload.get("limit"), 20),
        ),
        family_ids=_string_tuple(payload.get("family_ids")),
        datasets=_string_tuple(payload.get("datasets")),
        models=_string_tuple(payload.get("models")),
        failure_types=_string_tuple(payload.get("failure_types")),
        priority_bands=_string_tuple(payload.get("priority_bands")),
        units=_planning_units_from_payload(payload.get("units")),
        actions=_plan_actions_from_payload(payload.get("actions")),
        impact=_impact_from_payload(_mapping_or_empty(payload.get("impact"))),
    )


def _planning_units_from_payload(value: object) -> tuple[DatasetPlanningUnit, ...]:
    if not isinstance(value, list):
        return ()
    rows: list[DatasetPlanningUnit] = []
    for entry in value:
        payload = _mapping_or_empty(entry)
        rows.append(
            DatasetPlanningUnit(
                unit_id=str(payload.get("unit_id", "")),
                unit_kind=str(payload.get("unit_kind", "")),
                priority_band=str(payload.get("priority_band", "")),
                priority_score=_float_or_zero(payload.get("priority_score")),
                rationale=str(payload.get("rationale", "")),
                family_ids=_string_tuple(payload.get("family_ids")),
                comparison_ids=_string_tuple(payload.get("comparison_ids")),
                cluster_ids=_string_tuple(payload.get("cluster_ids")),
                members=_planning_unit_members_from_payload(payload.get("members")),
            )
        )
    return tuple(rows)


def _planning_unit_members_from_payload(value: object) -> tuple[PlanningUnitMember, ...]:
    if not isinstance(value, list):
        return ()
    rows: list[PlanningUnitMember] = []
    for entry in value:
        payload = _mapping_or_empty(entry)
        rows.append(
            PlanningUnitMember(
                family_id=str(payload.get("family_id", "")),
                priority_rank=_int_or_default(payload.get("priority_rank"), 0),
                priority_band=str(payload.get("priority_band", "")),
                priority_score=_float_or_zero(payload.get("priority_score")),
                actionability=str(payload.get("actionability", "neutral")),
                lifecycle_action=str(payload.get("lifecycle_action", "keep")),
                health_condition=str(payload.get("health_condition", "")),
                version_count=_int_or_default(payload.get("version_count"), 0),
                source_dataset_id=_string_or_none(payload.get("source_dataset_id")),
                primary_failure_type=_string_or_none(payload.get("primary_failure_type")),
                latest_dataset_id=_string_or_none(payload.get("latest_dataset_id")),
                projected_case_count=_int_or_none(payload.get("projected_case_count")),
                recent_fail_rate=_float_or_none(payload.get("recent_fail_rate")),
                datasets=_string_tuple(payload.get("datasets")),
                models=_string_tuple(payload.get("models")),
                target_family_id=_string_or_none(payload.get("target_family_id")),
                related_family_ids=_string_tuple(payload.get("related_family_ids")),
            )
        )
    return tuple(rows)


def _plan_actions_from_payload(value: object) -> tuple[PortfolioPlanAction, ...]:
    if not isinstance(value, list):
        return ()
    rows: list[PortfolioPlanAction] = []
    for entry in value:
        payload = _mapping_or_empty(entry)
        rows.append(
            PortfolioPlanAction(
                family_id=str(payload.get("family_id", "")),
                action=str(payload.get("action", "")),
                health_condition=str(payload.get("health_condition", "")),
                rationale=str(payload.get("rationale", "")),
                priority_rank=_int_or_default(payload.get("priority_rank"), 0),
                priority_band=str(payload.get("priority_band", "")),
                priority_score=_float_or_zero(payload.get("priority_score")),
                version_count=_int_or_default(payload.get("version_count"), 0),
                source_dataset_id=_string_or_none(payload.get("source_dataset_id")),
                primary_failure_type=_string_or_none(payload.get("primary_failure_type")),
                latest_dataset_id=_string_or_none(payload.get("latest_dataset_id")),
                projected_case_count=_int_or_none(payload.get("projected_case_count")),
                target_family_id=_string_or_none(payload.get("target_family_id")),
                related_family_ids=_string_tuple(payload.get("related_family_ids")),
                dependency_family_ids=_string_tuple(payload.get("dependency_family_ids")),
                comparison_ids=_string_tuple(payload.get("comparison_ids")),
                cluster_ids=_string_tuple(payload.get("cluster_ids")),
                datasets=_string_tuple(payload.get("datasets")),
                models=_string_tuple(payload.get("models")),
                recent_fail_rate=_float_or_none(payload.get("recent_fail_rate")),
            )
        )
    return tuple(rows)


def _impact_from_payload(payload: dict[str, JsonValue]) -> PortfolioPlanImpact:
    action_counts = payload.get("action_counts")
    return PortfolioPlanImpact(
        affected_family_count=_int_or_default(payload.get("affected_family_count"), 0),
        action_count=_int_or_default(payload.get("action_count"), 0),
        projected_case_count=_int_or_default(payload.get("projected_case_count"), 0),
        action_counts=(
            {
                str(key): _int_or_default(value, 0)
                for key, value in action_counts.items()
            }
            if isinstance(action_counts, dict)
            else {}
        ),
    )


def _saved_plan_matches(plan: SavedPortfolioPlan, filters: PortfolioFilters) -> bool:
    if filters.family_id is not None and filters.family_id not in plan.family_ids:
        return False
    if filters.dataset is not None and filters.dataset not in plan.datasets:
        return False
    if filters.model is not None and filters.model not in plan.models:
        return False
    if filters.failure_type is not None and filters.failure_type not in plan.failure_types:
        return False
    if filters.priority_band is not None and filters.priority_band not in plan.priority_bands:
        return False
    if filters.actionability == "actionable" and not any(
        action.action != "keep" for action in plan.actions
    ):
        return False
    if filters.actionability == "neutral" and any(action.action != "keep" for action in plan.actions):
        return False
    return True


def _portfolio_item_matches(item: DatasetPortfolioItem, filters: PortfolioFilters) -> bool:
    if filters.family_id is not None and item.family_id != filters.family_id:
        return False
    if filters.dataset is not None and filters.dataset not in item.datasets:
        return False
    if filters.model is not None and filters.model not in item.models:
        return False
    if filters.failure_type is not None and item.primary_failure_type != filters.failure_type:
        return False
    if filters.priority_band is not None and item.priority_band != filters.priority_band:
        return False
    if filters.actionability == "actionable" and item.actionability != "actionable":
        return False
    if filters.actionability == "neutral" and item.actionability != "neutral":
        return False
    return True


def _normalize_filters(filters: PortfolioFilters | None) -> PortfolioFilters:
    active = filters or PortfolioFilters()
    actionability = active.actionability.strip().lower()
    if actionability not in _ACTIONABILITY_VALUES:
        allowed = ", ".join(sorted(_ACTIONABILITY_VALUES))
        raise ValueError(f"unsupported portfolio actionability: {actionability}. Expected one of: {allowed}")
    priority_band = (
        active.priority_band.strip().lower()
        if isinstance(active.priority_band, str) and active.priority_band.strip()
        else None
    )
    if priority_band is not None and priority_band not in _PRIORITY_BANDS:
        allowed = ", ".join(_PRIORITY_BANDS)
        raise ValueError(f"unsupported portfolio priority band: {priority_band}. Expected one of: {allowed}")
    return PortfolioFilters(
        family_id=active.family_id,
        model=active.model,
        dataset=active.dataset,
        failure_type=active.failure_type,
        actionability=actionability,
        priority_band=priority_band,
        limit=max(active.limit, 1),
    )


def _priority_band(score: float) -> str:
    if score >= 60.0:
        return "urgent"
    if score >= 40.0:
        return "high"
    if score >= 20.0:
        return "medium"
    return "low"


def _priority_band_index(value: str) -> int:
    try:
        return _PRIORITY_BANDS.index(value)
    except ValueError:
        return len(_PRIORITY_BANDS)


def _sorted_priority_bands(values) -> tuple[str, ...]:
    unique = {value for value in values if isinstance(value, str) and value in _PRIORITY_BANDS}
    return tuple(sorted(unique, key=_priority_band_index))


def _sorted_unique(values) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if isinstance(value, str) and value.strip()}))


def _mapping_or_empty(value: object) -> dict[str, JsonValue]:
    return value if isinstance(value, dict) else {}


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(
        entry for entry in value if isinstance(entry, str) and entry.strip()
    )


def _float_or_none(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _float_or_zero(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return float(value)


def _int_or_default(value: object, default: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return default
    return value


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value
