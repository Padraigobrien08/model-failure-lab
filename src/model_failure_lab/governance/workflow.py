"""Governance review, apply, and family-health helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from model_failure_lab.datasets import DatasetEvolutionSummary, evolve_dataset_family
from model_failure_lab.datasets.contracts import FailureDataset
from model_failure_lab.datasets.load import load_dataset
from model_failure_lab.history import (
    DatasetHealthSummary,
    query_history_snapshot,
)
from model_failure_lab.index import QueryFilters, query_comparison_signals
from model_failure_lab.schemas import JsonValue
from model_failure_lab.storage import datasets_root
from model_failure_lab.storage.layout import project_root

from .lifecycle import (
    LifecycleActionRecord,
    LifecycleApplyResult,
    apply_lifecycle_action,
    get_active_lifecycle_action,
    list_lifecycle_action_records,
)
from .policy import (
    GovernancePolicy,
    GovernanceRecommendation,
    LifecycleRecommendation,
    describe_dataset_family_lifecycle,
    recommend_dataset_action,
)


@dataclass(slots=True, frozen=True)
class DatasetFamilyHealth:
    family_id: str
    version_count: int
    latest_dataset_id: str
    latest_version_tag: str
    latest_case_count: int
    latest_created_at: str | None
    latest_signal_verdict: str | None
    latest_severity: float | None
    source_dataset_id: str | None
    primary_failure_type: str | None
    latest_comparison_id: str | None
    health_label: str
    trend_label: str
    recent_fail_rate: float | None
    previous_fail_rate: float | None
    volatility_label: str
    evaluation_run_count: int
    active_lifecycle_action: str | None = None
    active_lifecycle_condition: str | None = None
    active_lifecycle_applied_at: str | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "family_id": self.family_id,
            "version_count": self.version_count,
            "latest_dataset_id": self.latest_dataset_id,
            "latest_version_tag": self.latest_version_tag,
            "latest_case_count": self.latest_case_count,
            "latest_signal_verdict": self.latest_signal_verdict,
            "latest_severity": self.latest_severity,
            "source_dataset_id": self.source_dataset_id,
            "primary_failure_type": self.primary_failure_type,
            "latest_comparison_id": self.latest_comparison_id,
            "health_label": self.health_label,
            "trend_label": self.trend_label,
            "recent_fail_rate": self.recent_fail_rate,
            "previous_fail_rate": self.previous_fail_rate,
            "volatility_label": self.volatility_label,
            "evaluation_run_count": self.evaluation_run_count,
            "active_lifecycle_action": self.active_lifecycle_action,
            "active_lifecycle_condition": self.active_lifecycle_condition,
            "active_lifecycle_applied_at": self.active_lifecycle_applied_at,
        }
        if self.latest_created_at is not None:
            payload["latest_created_at"] = self.latest_created_at
        return payload


@dataclass(slots=True, frozen=True)
class GovernanceApplyResult:
    comparison_id: str
    status: str
    action: str
    family_id: str
    policy_rule: str
    reason: str
    recommendation: GovernanceRecommendation
    dataset_id: str | None = None
    version_tag: str | None = None
    output_path: str | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "comparison_id": self.comparison_id,
            "status": self.status,
            "action": self.action,
            "family_id": self.family_id,
            "policy_rule": self.policy_rule,
            "reason": self.reason,
            "recommendation": self.recommendation.to_payload(),
        }
        if self.dataset_id is not None:
            payload["dataset_id"] = self.dataset_id
        if self.version_tag is not None:
            payload["version_tag"] = self.version_tag
        if self.output_path is not None:
            payload["output_path"] = self.output_path
        return payload


@dataclass(slots=True, frozen=True)
class DatasetLifecycleAlert:
    family_id: str
    recommendation: LifecycleRecommendation
    active_action: LifecycleActionRecord | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "family_id": self.family_id,
            "recommendation": self.recommendation.to_payload(),
            "active_action": self.active_action.to_payload() if self.active_action is not None else None,
        }


def list_dataset_family_health(
    *,
    root: str | Path | None = None,
) -> tuple[DatasetFamilyHealth, ...]:
    artifact_root = project_root(root).resolve()
    dataset_dir = datasets_root(root=artifact_root, create=False)
    if not dataset_dir.exists():
        return ()

    family_ids = {
        family_id
        for candidate in sorted(dataset_dir.glob("*.json"))
        for family_id in [_dataset_family_id(load_dataset(candidate))]
        if family_id is not None
    }
    records: list[DatasetFamilyHealth] = []
    for family_id in sorted(family_ids):
        health = get_dataset_family_health(family_id, root=artifact_root)
        if health is None:
            continue
        records.append(health)
    return tuple(
        sorted(
            records,
            key=lambda record: (
                -(record.latest_severity or 0.0),
                -record.version_count,
                record.family_id,
            ),
        )
    )


def review_dataset_actions(
    *,
    filters: QueryFilters | None = None,
    root: str | Path | None = None,
    policy: GovernancePolicy | None = None,
    include_ignored: bool = False,
) -> tuple[GovernanceRecommendation, ...]:
    artifact_root = project_root(root).resolve()
    signal_rows = query_comparison_signals(filters, verdict=None, root=artifact_root)
    recommendations: list[GovernanceRecommendation] = []
    for row in signal_rows:
        recommendation = recommend_dataset_action(
            str(row["report_id"]),
            root=artifact_root,
            policy=policy,
        )
        if include_ignored or recommendation.action != "ignore":
            recommendations.append(recommendation)
    return tuple(
        sorted(
            recommendations,
            key=lambda recommendation: (
                -(recommendation.escalation.score if recommendation.escalation is not None else 0.0),
                -float(recommendation.signal.get("severity", 0.0) or 0.0),
                recommendation.comparison_id,
            ),
        )
    )


def apply_dataset_actions(
    *,
    filters: QueryFilters | None = None,
    root: str | Path | None = None,
    policy: GovernancePolicy | None = None,
    include_ignored: bool = True,
) -> tuple[GovernanceApplyResult, ...]:
    artifact_root = project_root(root).resolve()
    recommendations = review_dataset_actions(
        filters=filters,
        root=artifact_root,
        policy=policy,
        include_ignored=True,
    )
    results: list[GovernanceApplyResult] = []
    for recommendation in recommendations:
        if recommendation.action == "ignore":
            if include_ignored:
                results.append(
                    GovernanceApplyResult(
                        comparison_id=recommendation.comparison_id,
                        status="skipped",
                        action="ignore",
                        family_id=recommendation.matched_family.family_id,
                        policy_rule=recommendation.policy_rule,
                        reason=recommendation.rationale,
                        recommendation=recommendation,
                    )
                )
            continue
        summary = _apply_recommendation(recommendation, root=artifact_root)
        results.append(
            GovernanceApplyResult(
                comparison_id=recommendation.comparison_id,
                status=(
                    "created"
                    if recommendation.action == "create" and summary.version_number == 1
                    else "evolved"
                ),
                action=recommendation.action,
                family_id=recommendation.matched_family.family_id,
                policy_rule=recommendation.policy_rule,
                reason=recommendation.rationale,
                recommendation=recommendation,
                dataset_id=summary.dataset.dataset_id,
                version_tag=summary.version_tag,
                output_path=str(summary.output_path),
            )
        )
    return tuple(results)


def get_dataset_family_health(
    family_id: str,
    *,
    root: str | Path | None = None,
) -> DatasetFamilyHealth | None:
    artifact_root = project_root(root).resolve()
    snapshot = query_history_snapshot(
        family_id=family_id,
        root=artifact_root,
        limit=25,
    )
    health_summary = snapshot.dataset_health
    versions = snapshot.dataset_versions
    if health_summary is None or not versions:
        return None
    latest = versions[-1]
    active_action = get_active_lifecycle_action(family_id, root=artifact_root)
    return _build_dataset_family_health_record(
        health_summary,
        latest,
        active_action=active_action,
    )


def review_dataset_lifecycle(
    *,
    root: str | Path | None = None,
    family_id: str | None = None,
    include_keep: bool = True,
) -> tuple[DatasetLifecycleAlert, ...]:
    artifact_root = project_root(root).resolve()
    rows = list_dataset_family_health(root=artifact_root)
    if family_id is not None:
        rows = tuple(row for row in rows if row.family_id == family_id)
    alerts: list[DatasetLifecycleAlert] = []
    for row in rows:
        recommendation = describe_dataset_family_lifecycle(
            row.family_id,
            root=artifact_root,
            projected_case_count=row.latest_case_count,
        )
        if recommendation is None:
            continue
        if not include_keep and recommendation.action == "keep":
            continue
        alerts.append(
            DatasetLifecycleAlert(
                family_id=row.family_id,
                recommendation=recommendation,
                active_action=get_active_lifecycle_action(row.family_id, root=artifact_root),
            )
        )
    return tuple(
        sorted(
            alerts,
            key=lambda alert: (
                -(alert.recommendation.projected_case_count or 0),
                -(alert.recommendation.version_count or 0),
                alert.family_id,
            ),
        )
    )


def apply_dataset_lifecycle_action(
    family_id: str,
    *,
    root: str | Path | None = None,
    action: str | None = None,
    source: str = "cli",
) -> LifecycleApplyResult:
    artifact_root = project_root(root).resolve()
    recommendation = describe_dataset_family_lifecycle(family_id, root=artifact_root)
    if recommendation is None:
        raise ValueError(f"family {family_id} has no lifecycle recommendation to apply")
    return apply_lifecycle_action(
        family_id=family_id,
        recommendation=recommendation,
        root=artifact_root,
        action=action,
        source=source,
    )


def apply_comparison_lifecycle_action(
    comparison_id: str,
    *,
    root: str | Path | None = None,
    policy: GovernancePolicy | None = None,
    action: str | None = None,
    source: str = "cli",
) -> LifecycleApplyResult:
    artifact_root = project_root(root).resolve()
    recommendation = recommend_dataset_action(
        comparison_id,
        root=artifact_root,
        policy=policy,
    )
    lifecycle = recommendation.lifecycle_recommendation
    if lifecycle is None:
        raise ValueError(f"comparison {comparison_id} has no lifecycle recommendation")
    return apply_lifecycle_action(
        family_id=lifecycle.family_id,
        recommendation=lifecycle,
        root=artifact_root,
        action=action,
        comparison_id=comparison_id,
        escalation=recommendation.escalation,
        source=source,
    )


def list_dataset_lifecycle_actions(
    family_id: str,
    *,
    root: str | Path | None = None,
) -> tuple[LifecycleActionRecord, ...]:
    return list_lifecycle_action_records(family_id, root=root)


def _apply_recommendation(
    recommendation: GovernanceRecommendation,
    *,
    root: Path,
) -> DatasetEvolutionSummary:
    return evolve_dataset_family(
        recommendation.matched_family.family_id,
        comparison_id=recommendation.comparison_id,
        root=root,
        failure_type=recommendation.policy.failure_type,
        top_n=recommendation.policy.top_n,
    )


def _dataset_family_id(dataset: FailureDataset) -> str | None:
    versioning = _mapping_or_empty(dataset.metadata.get("versioning"))
    family_id = _string_or_none(versioning.get("family_id"))
    if family_id is not None:
        return family_id
    source = _mapping_or_empty(dataset.source)
    return _string_or_none(source.get("family_id"))


def _source_dataset_id(dataset: FailureDataset) -> str | None:
    values = {
        source_dataset_id
        for case in dataset.cases
        for source_dataset_id in [_case_source_dataset_id(case.metadata)]
        if source_dataset_id is not None
    }
    if len(values) == 1:
        return next(iter(values))
    return None


def _case_source_dataset_id(metadata: dict[str, JsonValue]) -> str | None:
    harvest = metadata.get("harvest")
    if not isinstance(harvest, dict):
        return None
    value = harvest.get("source_dataset_id")
    return value if isinstance(value, str) and value.strip() else None


def _primary_regression_failure_type(signal: dict[str, JsonValue]) -> str | None:
    raw_drivers = signal.get("top_drivers")
    if not isinstance(raw_drivers, list):
        return None
    for entry in raw_drivers:
        if not isinstance(entry, dict):
            continue
        direction = entry.get("direction")
        failure_type = entry.get("failure_type")
        if direction == "regression" and isinstance(failure_type, str) and failure_type.strip():
            return failure_type
    return None


def _build_dataset_family_health_record(
    health_summary: DatasetHealthSummary,
    latest,
    *,
    active_action: LifecycleActionRecord | None = None,
) -> DatasetFamilyHealth:
    return DatasetFamilyHealth(
        family_id=health_summary.family_id,
        version_count=health_summary.version_count,
        latest_dataset_id=latest.dataset_id,
        latest_version_tag=latest.version_tag,
        latest_case_count=latest.case_count,
        latest_created_at=latest.created_at,
        latest_signal_verdict=latest.signal_verdict,
        latest_severity=latest.severity,
        source_dataset_id=health_summary.source_dataset_id,
        primary_failure_type=health_summary.primary_failure_type,
        latest_comparison_id=latest.source_comparison_id,
        health_label=health_summary.health_label,
        trend_label=health_summary.trend.label,
        recent_fail_rate=health_summary.recent_fail_rate,
        previous_fail_rate=health_summary.previous_fail_rate,
        volatility_label=health_summary.trend.volatility_label,
        evaluation_run_count=health_summary.evaluation_run_count,
        active_lifecycle_action=active_action.action if active_action is not None else None,
        active_lifecycle_condition=(
            active_action.health_condition if active_action is not None else None
        ),
        active_lifecycle_applied_at=(
            active_action.applied_at if active_action is not None else None
        ),
    )


def _mapping_or_empty(value: object) -> dict[str, JsonValue]:
    return value if isinstance(value, dict) else {}


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _float_or_none(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)
