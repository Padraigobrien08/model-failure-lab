"""Policy-as-code regression gates with waiver support."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

from model_failure_lab.index import QueryFilters
from model_failure_lab.schemas import JsonValue
from model_failure_lab.storage import read_json
from model_failure_lab.storage.layout import project_root

from .policy import GovernancePolicy
from .workflow import review_dataset_actions


@dataclass(slots=True, frozen=True)
class GateWaiver:
    comparison_id: str
    reason: str
    owner: str | None
    expires_at: str | None
    active: bool

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "comparison_id": self.comparison_id,
            "reason": self.reason,
            "owner": self.owner,
            "expires_at": self.expires_at,
            "active": self.active,
        }


@dataclass(slots=True, frozen=True)
class GateDecision:
    comparison_id: str
    action: str
    severity: float
    policy_rule: str
    blocked: bool
    waived: bool
    waiver: GateWaiver | None

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "comparison_id": self.comparison_id,
            "action": self.action,
            "severity": round(self.severity, 6),
            "policy_rule": self.policy_rule,
            "blocked": self.blocked,
            "waived": self.waived,
            "waiver": self.waiver.to_payload() if self.waiver is not None else None,
        }


@dataclass(slots=True, frozen=True)
class RegressionGateResult:
    blocked: bool
    policy: GovernancePolicy
    filters: QueryFilters
    rows: tuple[GateDecision, ...]

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "blocked": self.blocked,
            "policy": self.policy.to_payload(),
            "filters": {
                "failure_type": self.filters.failure_type,
                "model": self.filters.model,
                "dataset": self.filters.dataset,
                "report_id": self.filters.report_id,
                "baseline_run_id": self.filters.baseline_run_id,
                "candidate_run_id": self.filters.candidate_run_id,
                "last_n": self.filters.last_n,
                "since": self.filters.since,
                "until": self.filters.until,
                "limit": self.filters.limit,
            },
            "rows": [row.to_payload() for row in self.rows],
        }


def load_governance_policy_from_file(path: str | Path) -> GovernancePolicy:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("policy file must be a mapping")
    allowed_keys = {
        "minimum_severity",
        "top_n",
        "failure_type",
        "family_id",
        "family_case_cap",
        "max_duplicate_ratio",
        "recurrence_window",
        "recurrence_threshold",
        "strategy",
    }
    invalid = sorted(set(payload) - allowed_keys)
    if invalid:
        raise ValueError(f"unsupported policy keys: {', '.join(invalid)}")
    return GovernancePolicy(**payload)


def evaluate_regression_gate(
    *,
    root: str | Path | None = None,
    filters: QueryFilters | None = None,
    policy: GovernancePolicy | None = None,
    waiver_path: str | Path | None = None,
) -> RegressionGateResult:
    active_filters = filters or QueryFilters(limit=20)
    active_policy = policy or GovernancePolicy()
    waivers = _load_waivers(root=root, waiver_path=waiver_path)
    recommendations = review_dataset_actions(
        filters=active_filters,
        root=project_root(root),
        policy=active_policy,
        include_ignored=True,
    )
    rows: list[GateDecision] = []
    for recommendation in recommendations:
        severity = float(recommendation.signal.get("severity", 0.0) or 0.0)
        should_block = recommendation.action in {"create", "evolve"}
        waiver = waivers.get(recommendation.comparison_id)
        waived = waiver is not None and waiver.active
        rows.append(
            GateDecision(
                comparison_id=recommendation.comparison_id,
                action=recommendation.action,
                severity=severity,
                policy_rule=recommendation.policy_rule,
                blocked=bool(should_block and not waived),
                waived=waived,
                waiver=waiver,
            )
        )
    return RegressionGateResult(
        blocked=any(row.blocked for row in rows),
        policy=active_policy,
        filters=active_filters,
        rows=tuple(rows),
    )


def _load_waivers(
    *,
    root: str | Path | None,
    waiver_path: str | Path | None,
) -> dict[str, GateWaiver]:
    if waiver_path is None:
        return {}
    payload = read_json(Path(waiver_path))
    if not isinstance(payload, dict):
        raise ValueError("waiver file must be a JSON object")
    raw_rows = payload.get("waivers")
    if not isinstance(raw_rows, list):
        raise ValueError("waiver file must contain a `waivers` list")
    now = datetime.now(tz=timezone.utc)
    waivers: dict[str, GateWaiver] = {}
    for index, raw in enumerate(raw_rows):
        if not isinstance(raw, dict):
            raise ValueError(f"waivers[{index}] must be an object")
        comparison_id = _required_string(raw, "comparison_id", f"waivers[{index}]")
        reason = _required_string(raw, "reason", f"waivers[{index}]")
        owner = _optional_string(raw.get("owner"))
        expires_at = _optional_string(raw.get("expires_at"))
        active = True
        if expires_at is not None:
            active = _is_future_timestamp(expires_at, now=now)
        waivers[comparison_id] = GateWaiver(
            comparison_id=comparison_id,
            reason=reason,
            owner=owner,
            expires_at=expires_at,
            active=active,
        )
    return waivers


def _required_string(payload: dict[str, object], key: str, label: str) -> str:
    value = payload.get(key)
    if isinstance(value, str) and value.strip():
        return value
    raise ValueError(f"{label}.{key} must be a non-empty string")


def _optional_string(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def _is_future_timestamp(value: str, *, now: datetime) -> bool:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed >= now
