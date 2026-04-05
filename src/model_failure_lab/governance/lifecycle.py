"""Lifecycle action persistence for deterministic dataset-family governance."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from model_failure_lab.schemas import JsonValue
from model_failure_lab.storage import (
    lifecycle_family_directory,
    project_root,
    read_json,
    write_json,
)

from .policy import GovernanceEscalation, LifecycleRecommendation

_ALLOWED_LIFECYCLE_ACTIONS = {"keep", "prune", "merge_candidate", "retire"}


@dataclass(slots=True, frozen=True)
class LifecycleActionRecord:
    action_id: str
    family_id: str
    action: str
    health_condition: str
    rationale: str
    applied_at: str
    source: str
    status: str
    target_family_id: str | None = None
    related_family_ids: tuple[str, ...] = ()
    source_dataset_id: str | None = None
    primary_failure_type: str | None = None
    latest_dataset_id: str | None = None
    version_count: int | None = None
    evaluation_run_count: int | None = None
    recent_fail_rate: float | None = None
    projected_case_count: int | None = None
    comparison_id: str | None = None
    escalation_status: str | None = None
    escalation_score: float | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "action_id": self.action_id,
            "family_id": self.family_id,
            "action": self.action,
            "health_condition": self.health_condition,
            "rationale": self.rationale,
            "applied_at": self.applied_at,
            "source": self.source,
            "status": self.status,
            "target_family_id": self.target_family_id,
            "related_family_ids": list(self.related_family_ids),
            "source_dataset_id": self.source_dataset_id,
            "primary_failure_type": self.primary_failure_type,
            "latest_dataset_id": self.latest_dataset_id,
            "version_count": self.version_count,
            "evaluation_run_count": self.evaluation_run_count,
            "recent_fail_rate": (
                round(self.recent_fail_rate, 6) if self.recent_fail_rate is not None else None
            ),
            "projected_case_count": self.projected_case_count,
            "comparison_id": self.comparison_id,
            "escalation_status": self.escalation_status,
            "escalation_score": (
                round(self.escalation_score, 6) if self.escalation_score is not None else None
            ),
        }
        return payload


@dataclass(slots=True, frozen=True)
class LifecycleApplyResult:
    status: str
    family_id: str
    action: str
    record: LifecycleActionRecord
    output_path: Path

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "status": self.status,
            "family_id": self.family_id,
            "action": self.action,
            "output_path": str(self.output_path),
            "record": self.record.to_payload(),
        }


def list_lifecycle_action_records(
    family_id: str,
    *,
    root: str | Path | None = None,
) -> tuple[LifecycleActionRecord, ...]:
    family_dir = lifecycle_family_directory(family_id, root=project_root(root), create=False)
    if not family_dir.exists():
        return ()
    records: list[LifecycleActionRecord] = []
    for artifact_path in sorted(family_dir.glob("*.json")):
        payload = read_json(artifact_path)
        records.append(_record_from_payload(payload))
    return tuple(
        sorted(
            records,
            key=lambda record: (record.applied_at, record.action_id),
        )
    )


def get_active_lifecycle_action(
    family_id: str,
    *,
    root: str | Path | None = None,
) -> LifecycleActionRecord | None:
    records = list_lifecycle_action_records(family_id, root=root)
    if not records:
        return None
    return records[-1]


def apply_lifecycle_action(
    *,
    family_id: str,
    recommendation: LifecycleRecommendation,
    root: str | Path | None = None,
    action: str | None = None,
    applied_at: str | None = None,
    comparison_id: str | None = None,
    escalation: GovernanceEscalation | None = None,
    source: str = "cli",
) -> LifecycleApplyResult:
    selected_action = _normalize_lifecycle_action(action or recommendation.action)
    active_root = project_root(root).resolve()
    timestamp = applied_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    action_id = _build_action_id(
        family_id=family_id,
        action=selected_action,
        recommendation=recommendation,
        comparison_id=comparison_id,
    )
    output_path = (
        lifecycle_family_directory(family_id, root=active_root, create=True) / f"{action_id}.json"
    )
    record = LifecycleActionRecord(
        action_id=action_id,
        family_id=family_id,
        action=selected_action,
        health_condition=recommendation.health_condition,
        rationale=recommendation.rationale,
        applied_at=timestamp,
        source=source,
        status="applied",
        target_family_id=recommendation.target_family_id,
        related_family_ids=recommendation.related_family_ids,
        source_dataset_id=recommendation.source_dataset_id,
        primary_failure_type=recommendation.primary_failure_type,
        latest_dataset_id=recommendation.latest_dataset_id,
        version_count=recommendation.version_count,
        evaluation_run_count=recommendation.evaluation_run_count,
        recent_fail_rate=recommendation.recent_fail_rate,
        projected_case_count=recommendation.projected_case_count,
        comparison_id=comparison_id,
        escalation_status=escalation.status if escalation is not None else None,
        escalation_score=escalation.score if escalation is not None else None,
    )
    if output_path.exists():
        return LifecycleApplyResult(
            status="already_applied",
            family_id=family_id,
            action=selected_action,
            record=record,
            output_path=output_path,
        )
    write_json(output_path, record.to_payload())
    return LifecycleApplyResult(
        status="applied",
        family_id=family_id,
        action=selected_action,
        record=record,
        output_path=output_path,
    )


def _build_action_id(
    *,
    family_id: str,
    action: str,
    recommendation: LifecycleRecommendation,
    comparison_id: str | None,
) -> str:
    digest = hashlib.sha1(
        "|".join(
            [
                family_id,
                action,
                recommendation.health_condition,
                recommendation.target_family_id or "",
                ",".join(recommendation.related_family_ids),
                recommendation.latest_dataset_id or "",
                recommendation.source_dataset_id or "",
                recommendation.primary_failure_type or "",
                str(recommendation.version_count or 0),
                str(recommendation.projected_case_count or 0),
                comparison_id or "",
            ]
        ).encode("utf-8")
    ).hexdigest()[:16]
    return f"{action}-{digest}"


def _normalize_lifecycle_action(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in _ALLOWED_LIFECYCLE_ACTIONS:
        allowed = ", ".join(sorted(_ALLOWED_LIFECYCLE_ACTIONS))
        raise ValueError(f"unsupported lifecycle action: {value}. Expected one of: {allowed}")
    return normalized


def _record_from_payload(payload: dict[str, JsonValue]) -> LifecycleActionRecord:
    return LifecycleActionRecord(
        action_id=str(payload.get("action_id", "")),
        family_id=str(payload.get("family_id", "")),
        action=str(payload.get("action", "")),
        health_condition=str(payload.get("health_condition", "")),
        rationale=str(payload.get("rationale", "")),
        applied_at=str(payload.get("applied_at", "")),
        source=str(payload.get("source", "")),
        status=str(payload.get("status", "")),
        target_family_id=_string_or_none(payload.get("target_family_id")),
        related_family_ids=_string_tuple(payload.get("related_family_ids")),
        source_dataset_id=_string_or_none(payload.get("source_dataset_id")),
        primary_failure_type=_string_or_none(payload.get("primary_failure_type")),
        latest_dataset_id=_string_or_none(payload.get("latest_dataset_id")),
        version_count=_int_or_none(payload.get("version_count")),
        evaluation_run_count=_int_or_none(payload.get("evaluation_run_count")),
        recent_fail_rate=_float_or_none(payload.get("recent_fail_rate")),
        projected_case_count=_int_or_none(payload.get("projected_case_count")),
        comparison_id=_string_or_none(payload.get("comparison_id")),
        escalation_status=_string_or_none(payload.get("escalation_status")),
        escalation_score=_float_or_none(payload.get("escalation_score")),
    )


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(entry for entry in value if isinstance(entry, str) and entry.strip())


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _float_or_none(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)
