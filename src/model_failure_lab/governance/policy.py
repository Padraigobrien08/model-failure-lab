"""Deterministic governance policy evaluation for saved comparison signals."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from model_failure_lab.clusters import FailureClusterSummary
from model_failure_lab.datasets.evolution import (
    RegressionPackPreviewCase,
    list_dataset_versions,
    preview_regression_pack,
)
from model_failure_lab.history import SignalHistoryContext, build_signal_history_context
from model_failure_lab.datasets.load import load_dataset
from model_failure_lab.schemas import JsonValue
from model_failure_lab.storage.layout import project_root

DEFAULT_MINIMUM_SEVERITY = 0.05
DEFAULT_FAMILY_CASE_CAP = 200
DEFAULT_MAX_DUPLICATE_RATIO = 0.6
DEFAULT_RECURRENCE_WINDOW = 5
DEFAULT_RECURRENCE_THRESHOLD = 2


@dataclass(slots=True, frozen=True)
class GovernancePolicy:
    minimum_severity: float = DEFAULT_MINIMUM_SEVERITY
    top_n: int = 10
    failure_type: str | None = None
    family_id: str | None = None
    family_case_cap: int | None = DEFAULT_FAMILY_CASE_CAP
    max_duplicate_ratio: float | None = DEFAULT_MAX_DUPLICATE_RATIO
    recurrence_window: int = DEFAULT_RECURRENCE_WINDOW
    recurrence_threshold: int | None = DEFAULT_RECURRENCE_THRESHOLD
    strategy: str = "exact_suggested_family_then_health_guards"

    def __post_init__(self) -> None:
        if self.minimum_severity < 0:
            raise ValueError("minimum_severity must be >= 0")
        if self.top_n < 1:
            raise ValueError("top_n must be >= 1")
        if self.family_case_cap is not None and self.family_case_cap < 1:
            raise ValueError("family_case_cap must be >= 1 when provided")
        if self.max_duplicate_ratio is not None and not 0.0 <= self.max_duplicate_ratio <= 1.0:
            raise ValueError("max_duplicate_ratio must be between 0 and 1 when provided")
        if self.recurrence_window < 1:
            raise ValueError("recurrence_window must be >= 1")
        if self.recurrence_threshold is not None and self.recurrence_threshold < 1:
            raise ValueError("recurrence_threshold must be >= 1 when provided")

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "minimum_severity": round(self.minimum_severity, 6),
            "top_n": self.top_n,
            "failure_type": self.failure_type,
            "family_id": self.family_id,
            "family_case_cap": self.family_case_cap,
            "max_duplicate_ratio": (
                round(self.max_duplicate_ratio, 6)
                if self.max_duplicate_ratio is not None
                else None
            ),
            "recurrence_window": self.recurrence_window,
            "recurrence_threshold": self.recurrence_threshold,
            "strategy": self.strategy,
        }


DEFAULT_GOVERNANCE_POLICY = GovernancePolicy()


@dataclass(slots=True, frozen=True)
class GovernanceFamilyMatch:
    family_id: str
    match_kind: str
    exists: bool
    version_count: int
    latest_dataset_id: str | None
    current_case_count: int
    proposed_addition_count: int
    duplicate_case_count: int
    duplicate_ratio: float
    projected_case_count: int
    family_case_cap: int | None
    cap_reached: bool
    duplicate_ratio_exceeded: bool

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "family_id": self.family_id,
            "match_kind": self.match_kind,
            "exists": self.exists,
            "version_count": self.version_count,
            "latest_dataset_id": self.latest_dataset_id,
            "current_case_count": self.current_case_count,
            "proposed_addition_count": self.proposed_addition_count,
            "duplicate_case_count": self.duplicate_case_count,
            "duplicate_ratio": round(self.duplicate_ratio, 6),
            "projected_case_count": self.projected_case_count,
            "family_case_cap": self.family_case_cap,
            "cap_reached": self.cap_reached,
            "duplicate_ratio_exceeded": self.duplicate_ratio_exceeded,
        }


@dataclass(slots=True, frozen=True)
class GovernanceRecommendation:
    comparison_id: str
    action: str
    policy_rule: str
    rationale: str
    policy: GovernancePolicy
    signal: dict[str, JsonValue]
    matched_family: GovernanceFamilyMatch
    selected_case_count: int
    evidence_case_ids: tuple[str, ...]
    preview_cases: tuple[RegressionPackPreviewCase, ...]
    history_context: SignalHistoryContext | None = None
    cluster_context: tuple[FailureClusterSummary, ...] = ()

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "comparison_id": self.comparison_id,
            "action": self.action,
            "policy_rule": self.policy_rule,
            "rationale": self.rationale,
            "policy": self.policy.to_payload(),
            "signal": dict(self.signal),
            "matched_family": self.matched_family.to_payload(),
            "selected_case_count": self.selected_case_count,
            "evidence_case_ids": list(self.evidence_case_ids),
            "preview_cases": [entry.to_payload() for entry in self.preview_cases],
            "cluster_context": [summary.to_payload() for summary in self.cluster_context],
        }
        if self.history_context is not None:
            payload["history_context"] = self.history_context.to_payload()
        return payload


def recommend_dataset_action(
    comparison_id: str,
    *,
    root: str | Path | None = None,
    policy: GovernancePolicy | None = None,
) -> GovernanceRecommendation:
    active_policy = policy or DEFAULT_GOVERNANCE_POLICY
    artifact_root = project_root(root).resolve()
    preview = preview_regression_pack(
        comparison_id=comparison_id,
        root=artifact_root,
        family_id=active_policy.family_id,
        failure_type=active_policy.failure_type,
        top_n=active_policy.top_n,
        allow_empty=True,
    )
    family_match = _build_family_match(
        family_id=preview.suggested_family_id,
        preview_cases=preview.preview_cases,
        root=artifact_root,
        policy=active_policy,
    )
    history_context = build_signal_history_context(
        comparison_id,
        family_id=family_match.family_id,
        limit=active_policy.recurrence_window,
        root=artifact_root,
    )
    signal_verdict = _signal_string(preview.signal, "verdict") or "unknown"
    severity = _signal_float(preview.signal, "severity")
    history_override = (
        signal_verdict == "regression"
        and severity < active_policy.minimum_severity
        and active_policy.recurrence_threshold is not None
        and history_context.recent_regression_count >= active_policy.recurrence_threshold
    )
    cluster_context = history_context.recurring_clusters

    if signal_verdict == "incompatible":
        action = "ignore"
        policy_rule = "incompatible_signal"
        rationale = "Saved comparison is incompatible, so governance cannot create or evolve a regression family from it."
    elif signal_verdict != "regression":
        action = "ignore"
        policy_rule = "non_regression_signal"
        rationale = (
            f"Signal verdict is `{signal_verdict}`, so the comparison does not qualify for regression-pack governance."
        )
    elif preview.selected_case_count == 0:
        action = "ignore"
        policy_rule = (
            "failure_type_filter_excluded_regressions"
            if active_policy.failure_type is not None
            else "no_regression_cases_selected"
        )
        rationale = (
            "The policy filters did not leave any regression cases eligible for deterministic pack selection."
        )
    elif family_match.proposed_addition_count == 0 and family_match.exists:
        action = "ignore"
        policy_rule = "no_new_cases_after_duplicate_check"
        rationale = (
            f"Matched family `{family_match.family_id}` already contains all selected regression cases under the duplicate-growth key."
        )
    elif family_match.cap_reached:
        action = "ignore"
        policy_rule = "family_case_cap_reached"
        rationale = (
            f"Matched family `{family_match.family_id}` would exceed the configured case cap of {family_match.family_case_cap}."
        )
    elif family_match.duplicate_ratio_exceeded:
        action = "ignore"
        policy_rule = "duplicate_growth_threshold_exceeded"
        rationale = (
            f"Matched family `{family_match.family_id}` would add too little new signal: duplicate ratio {family_match.duplicate_ratio:.3f} exceeds the configured maximum of {active_policy.max_duplicate_ratio:.3f}."
        )
    elif severity < active_policy.minimum_severity and not history_override:
        action = "ignore"
        policy_rule = "below_minimum_severity"
        rationale = (
            f"Signal severity {severity:.3f} is below the configured minimum of {active_policy.minimum_severity:.3f}."
        )
    elif history_override and family_match.exists:
        action = "evolve"
        policy_rule = "recurring_regression_override"
        rationale = (
            f"Signal severity {severity:.3f} is below the configured minimum, but `{history_context.scope_value}` has {history_context.recent_regression_count} regressions in the recent history window, so governance recommends evolving `{family_match.family_id}`."
        )
    elif history_override:
        action = "create"
        policy_rule = "recurring_regression_override"
        rationale = (
            f"Signal severity {severity:.3f} is below the configured minimum, but `{history_context.scope_value}` has {history_context.recent_regression_count} regressions in the recent history window, so governance recommends creating `{family_match.family_id}`."
        )
    elif family_match.exists:
        action = "evolve"
        policy_rule = "existing_family_match"
        rationale = (
            f"Qualifying regression matches existing family `{family_match.family_id}` and remains within cap and duplicate-growth policy."
        )
    else:
        action = "create"
        policy_rule = "new_family_required"
        rationale = (
            f"Qualifying regression has no existing family match, so governance recommends creating `{family_match.family_id}`."
        )

    evidence_case_ids = tuple(
        preview_case.source_case_id for preview_case in preview.preview_cases
    )
    return GovernanceRecommendation(
        comparison_id=comparison_id,
        action=action,
        policy_rule=policy_rule,
        rationale=_append_cluster_rationale(rationale, cluster_context),
        policy=active_policy,
        signal=dict(preview.signal),
        matched_family=family_match,
        selected_case_count=preview.selected_case_count,
        evidence_case_ids=evidence_case_ids,
        preview_cases=preview.preview_cases,
        history_context=history_context,
        cluster_context=cluster_context,
    )


def _build_family_match(
    *,
    family_id: str,
    preview_cases: tuple[RegressionPackPreviewCase, ...],
    root: Path,
    policy: GovernancePolicy,
) -> GovernanceFamilyMatch:
    versions = list_dataset_versions(family_id, root=root)
    latest_dataset = load_dataset(versions[-1].path) if versions else None
    latest_hashes = (
        {_dataset_case_duplicate_key(case) for case in latest_dataset.cases}
        if latest_dataset is not None
        else set()
    )
    preview_hashes = [_preview_case_duplicate_key(case) for case in preview_cases]
    duplicate_case_count = sum(1 for key in preview_hashes if key in latest_hashes)
    proposed_addition_count = max(len(preview_cases) - duplicate_case_count, 0)
    duplicate_ratio = (
        duplicate_case_count / len(preview_cases) if preview_cases else 0.0
    )
    current_case_count = len(latest_dataset.cases) if latest_dataset is not None else 0
    projected_case_count = current_case_count + proposed_addition_count
    cap_reached = (
        policy.family_case_cap is not None and projected_case_count > policy.family_case_cap
    )
    duplicate_ratio_exceeded = (
        policy.max_duplicate_ratio is not None and duplicate_ratio > policy.max_duplicate_ratio
    )
    return GovernanceFamilyMatch(
        family_id=family_id,
        match_kind="existing_exact" if versions else "suggested_new",
        exists=bool(versions),
        version_count=len(versions),
        latest_dataset_id=versions[-1].dataset_id if versions else None,
        current_case_count=current_case_count,
        proposed_addition_count=proposed_addition_count,
        duplicate_case_count=duplicate_case_count,
        duplicate_ratio=duplicate_ratio,
        projected_case_count=projected_case_count,
        family_case_cap=policy.family_case_cap,
        cap_reached=cap_reached,
        duplicate_ratio_exceeded=duplicate_ratio_exceeded,
    )


def _dataset_case_duplicate_key(case: object) -> str:
    metadata = getattr(case, "metadata", {})
    if isinstance(metadata, dict):
        harvest = metadata.get("harvest")
        if isinstance(harvest, dict):
            normalized_prompt_hash = harvest.get("normalized_prompt_hash")
            if isinstance(normalized_prompt_hash, str) and normalized_prompt_hash:
                return normalized_prompt_hash
    prompt = getattr(case, "prompt", "")
    return _normalized_prompt_hash(prompt if isinstance(prompt, str) else "")


def _preview_case_duplicate_key(case: RegressionPackPreviewCase) -> str:
    return _normalized_prompt_hash(case.prompt)


def _normalized_prompt_hash(prompt: str) -> str:
    normalized_prompt = " ".join(prompt.lower().split())
    return hashlib.sha1(normalized_prompt.encode("utf-8")).hexdigest()


def _signal_string(payload: dict[str, JsonValue], key: str) -> str | None:
    value = payload.get(key)
    return value if isinstance(value, str) and value.strip() else None


def _signal_float(payload: dict[str, JsonValue], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return float(value)


def _append_cluster_rationale(
    rationale: str,
    cluster_context: tuple[FailureClusterSummary, ...],
) -> str:
    if not cluster_context:
        return rationale
    primary = cluster_context[0]
    return (
        f"{rationale} Primary recurring cluster `{primary.cluster_id}` "
        f"({primary.label}) spans {primary.scope_count} saved artifacts."
    )
