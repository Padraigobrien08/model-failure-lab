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
from model_failure_lab.datasets.load import load_dataset
from model_failure_lab.history import (
    DatasetHealthSummary,
    SignalHistoryContext,
    build_signal_history_context,
    query_history_snapshot,
)
from model_failure_lab.schemas import JsonValue
from model_failure_lab.storage.layout import datasets_root, project_root

DEFAULT_MINIMUM_SEVERITY = 0.05
DEFAULT_FAMILY_CASE_CAP = 200
DEFAULT_MAX_DUPLICATE_RATIO = 0.6
DEFAULT_RECURRENCE_WINDOW = 5
DEFAULT_RECURRENCE_THRESHOLD = 2
DEFAULT_WATCH_SCORE = 0.12
DEFAULT_ELEVATED_SCORE = 0.22
DEFAULT_CRITICAL_SCORE = 0.35
DEFAULT_OVERGROWN_CASE_COUNT = 30
DEFAULT_OVERGROWN_VERSION_COUNT = 4
DEFAULT_STALE_FAIL_RATE = 0.03
DEFAULT_STALE_MIN_RUNS = 3


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
class GovernanceEscalation:
    status: str
    score: float
    severity_band: str
    reason: str
    recent_regression_count: int
    recurring_cluster_count: int
    family_health_label: str | None

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "status": self.status,
            "score": round(self.score, 6),
            "severity_band": self.severity_band,
            "reason": self.reason,
            "recent_regression_count": self.recent_regression_count,
            "recurring_cluster_count": self.recurring_cluster_count,
            "family_health_label": self.family_health_label,
        }


@dataclass(slots=True, frozen=True)
class LifecycleRecommendation:
    family_id: str
    action: str
    health_condition: str
    rationale: str
    target_family_id: str | None = None
    related_family_ids: tuple[str, ...] = ()
    source_dataset_id: str | None = None
    primary_failure_type: str | None = None
    latest_dataset_id: str | None = None
    version_count: int | None = None
    evaluation_run_count: int | None = None
    recent_fail_rate: float | None = None
    projected_case_count: int | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "family_id": self.family_id,
            "action": self.action,
            "health_condition": self.health_condition,
            "rationale": self.rationale,
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
    escalation: GovernanceEscalation | None = None
    lifecycle_recommendation: LifecycleRecommendation | None = None

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
        if self.escalation is not None:
            payload["escalation"] = self.escalation.to_payload()
        if self.lifecycle_recommendation is not None:
            payload["lifecycle_recommendation"] = self.lifecycle_recommendation.to_payload()
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
    lifecycle_recommendation = _build_lifecycle_recommendation(
        family_match=family_match,
        history_context=history_context,
        root=artifact_root,
    )

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
    escalation = _build_escalation(
        action=action,
        signal_verdict=signal_verdict,
        severity=severity,
        family_match=family_match,
        history_context=history_context,
        cluster_context=cluster_context,
        lifecycle_recommendation=lifecycle_recommendation,
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
        escalation=escalation,
        lifecycle_recommendation=lifecycle_recommendation,
    )


def describe_dataset_family_lifecycle(
    family_id: str,
    *,
    root: str | Path | None = None,
    projected_case_count: int | None = None,
) -> LifecycleRecommendation | None:
    artifact_root = project_root(root).resolve()
    snapshot = query_history_snapshot(
        family_id=family_id,
        root=artifact_root,
        limit=max(DEFAULT_RECURRENCE_WINDOW, 5),
    )
    if snapshot.dataset_health is None or not snapshot.dataset_versions:
        return None
    latest = snapshot.dataset_versions[-1]
    return _recommend_lifecycle_action(
        family_id=family_id,
        health_summary=snapshot.dataset_health,
        latest_case_count=latest.case_count,
        projected_case_count=projected_case_count or latest.case_count,
        latest_dataset_id=latest.dataset_id,
        root=artifact_root,
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


def _build_escalation(
    *,
    action: str,
    signal_verdict: str,
    severity: float,
    family_match: GovernanceFamilyMatch,
    history_context: SignalHistoryContext,
    cluster_context: tuple[FailureClusterSummary, ...],
    lifecycle_recommendation: LifecycleRecommendation,
) -> GovernanceEscalation:
    family_health = history_context.family_health
    score = max(severity, 0.0)
    score += min(history_context.recent_regression_count, 4) * 0.04
    score += min(len(cluster_context), 3) * 0.03
    if family_match.cap_reached or family_match.duplicate_ratio_exceeded:
        score += 0.06
    if family_health is not None and family_health.health_label in {"degrading", "volatile"}:
        score += 0.06
    if lifecycle_recommendation.action in {"prune", "merge_candidate", "retire"}:
        score += 0.05

    if severity >= DEFAULT_ELEVATED_SCORE:
        severity_band = "high"
    elif severity >= DEFAULT_MINIMUM_SEVERITY:
        severity_band = "moderate"
    elif severity > 0:
        severity_band = "low"
    else:
        severity_band = "none"

    if action == "ignore" and signal_verdict != "regression" and score < DEFAULT_WATCH_SCORE:
        status = "suppressed"
    elif score >= DEFAULT_CRITICAL_SCORE:
        status = "critical"
    elif score >= DEFAULT_ELEVATED_SCORE:
        status = "elevated"
    else:
        status = "watch"

    reasons: list[str] = [f"severity={severity:.3f}"]
    if history_context.recent_regression_count:
        reasons.append(f"recent_regressions={history_context.recent_regression_count}")
    if cluster_context:
        reasons.append(f"recurring_clusters={len(cluster_context)}")
    if family_health is not None:
        reasons.append(f"family_health={family_health.health_label}")
    if lifecycle_recommendation.action != "keep":
        reasons.append(f"family_action={lifecycle_recommendation.action}")
    return GovernanceEscalation(
        status=status,
        score=score,
        severity_band=severity_band,
        reason=", ".join(reasons),
        recent_regression_count=history_context.recent_regression_count,
        recurring_cluster_count=len(cluster_context),
        family_health_label=family_health.health_label if family_health is not None else None,
    )


def _build_lifecycle_recommendation(
    *,
    family_match: GovernanceFamilyMatch,
    history_context: SignalHistoryContext,
    root: Path,
) -> LifecycleRecommendation:
    if not family_match.exists:
        return LifecycleRecommendation(
            family_id=family_match.family_id,
            action="keep",
            health_condition="keepable",
            rationale=(
                f"Family `{family_match.family_id}` does not exist yet, so lifecycle management "
                "stays neutral until the first immutable version is created."
            ),
            projected_case_count=family_match.projected_case_count,
        )
    health_summary = history_context.family_health
    if health_summary is None:
        return LifecycleRecommendation(
            family_id=family_match.family_id,
            action="keep",
            health_condition="keepable",
            rationale=(
                f"Family `{family_match.family_id}` has no evaluated history yet, so no lifecycle "
                "action is recommended."
            ),
            latest_dataset_id=family_match.latest_dataset_id,
            version_count=family_match.version_count,
            projected_case_count=family_match.projected_case_count,
        )
    return _recommend_lifecycle_action(
        family_id=family_match.family_id,
        health_summary=health_summary,
        latest_case_count=family_match.current_case_count,
        projected_case_count=family_match.projected_case_count,
        latest_dataset_id=family_match.latest_dataset_id,
        root=root,
    )


def _recommend_lifecycle_action(
    *,
    family_id: str,
    health_summary: DatasetHealthSummary,
    latest_case_count: int,
    projected_case_count: int,
    latest_dataset_id: str | None,
    root: Path,
) -> LifecycleRecommendation:
    related_families = _related_family_ids(
        family_id=family_id,
        source_dataset_id=health_summary.source_dataset_id,
        primary_failure_type=health_summary.primary_failure_type,
        root=root,
    )
    if related_families:
        target_family_id = sorted(
            related_families,
            key=lambda entry: (entry != family_id, entry),
        )[0]
        return LifecycleRecommendation(
            family_id=family_id,
            action="merge_candidate",
            health_condition="merge_candidate",
            rationale=(
                f"Family `{family_id}` shares source dataset `{health_summary.source_dataset_id or 'unknown'}` "
                f"and primary failure type `{health_summary.primary_failure_type or 'unknown'}` with "
                f"`{target_family_id}`, so the family should be reviewed as a deterministic merge candidate."
            ),
            target_family_id=target_family_id,
            related_family_ids=tuple(sorted(related_families)),
            source_dataset_id=health_summary.source_dataset_id,
            primary_failure_type=health_summary.primary_failure_type,
            latest_dataset_id=latest_dataset_id,
            version_count=health_summary.version_count,
            evaluation_run_count=health_summary.evaluation_run_count,
            recent_fail_rate=health_summary.recent_fail_rate,
            projected_case_count=projected_case_count,
        )

    if (
        projected_case_count >= DEFAULT_OVERGROWN_CASE_COUNT
        or health_summary.version_count >= DEFAULT_OVERGROWN_VERSION_COUNT
    ):
        return LifecycleRecommendation(
            family_id=family_id,
            action="prune",
            health_condition="overgrown",
            rationale=(
                f"Family `{family_id}` is projected to carry {projected_case_count} cases across "
                f"{health_summary.version_count} versions, which crosses the deterministic "
                "overgrowth threshold."
            ),
            source_dataset_id=health_summary.source_dataset_id,
            primary_failure_type=health_summary.primary_failure_type,
            latest_dataset_id=latest_dataset_id,
            version_count=health_summary.version_count,
            evaluation_run_count=health_summary.evaluation_run_count,
            recent_fail_rate=health_summary.recent_fail_rate,
            projected_case_count=projected_case_count,
        )

    if (
        health_summary.recent_fail_rate is not None
        and health_summary.recent_fail_rate <= DEFAULT_STALE_FAIL_RATE
        and health_summary.evaluation_run_count >= DEFAULT_STALE_MIN_RUNS
        and health_summary.health_label in {"stable", "improving"}
    ):
        return LifecycleRecommendation(
            family_id=family_id,
            action="retire",
            health_condition="stale",
            rationale=(
                f"Family `{family_id}` is {health_summary.health_label} with recent fail rate "
                f"{health_summary.recent_fail_rate:.3f} across "
                f"{health_summary.evaluation_run_count} evaluation runs, so it should be reviewed "
                "for retirement."
            ),
            source_dataset_id=health_summary.source_dataset_id,
            primary_failure_type=health_summary.primary_failure_type,
            latest_dataset_id=latest_dataset_id,
            version_count=health_summary.version_count,
            evaluation_run_count=health_summary.evaluation_run_count,
            recent_fail_rate=health_summary.recent_fail_rate,
            projected_case_count=projected_case_count,
        )

    return LifecycleRecommendation(
        family_id=family_id,
        action="keep",
        health_condition="keepable",
        rationale=(
            f"Family `{family_id}` remains within deterministic size and health bounds, so it "
            "should be kept in active rotation."
        ),
        source_dataset_id=health_summary.source_dataset_id,
        primary_failure_type=health_summary.primary_failure_type,
        latest_dataset_id=latest_dataset_id,
        version_count=health_summary.version_count,
        evaluation_run_count=health_summary.evaluation_run_count,
        recent_fail_rate=health_summary.recent_fail_rate,
        projected_case_count=projected_case_count,
    )


def _related_family_ids(
    *,
    family_id: str,
    source_dataset_id: str | None,
    primary_failure_type: str | None,
    root: Path,
) -> tuple[str, ...]:
    if source_dataset_id is None or primary_failure_type is None:
        return ()
    dataset_dir = datasets_root(root=root, create=False)
    if not dataset_dir.exists():
        return ()

    matching_families: set[str] = set()
    for dataset_path in sorted(dataset_dir.glob("*.json")):
        dataset = load_dataset(dataset_path)
        candidate_family_id = _dataset_family_id_from_dataset(dataset)
        if candidate_family_id is None or candidate_family_id == family_id:
            continue
        if _source_dataset_id_from_dataset(dataset) != source_dataset_id:
            continue
        if _primary_failure_type_from_dataset(dataset) != primary_failure_type:
            continue
        matching_families.add(candidate_family_id)
    return tuple(sorted(matching_families))


def _dataset_family_id_from_dataset(dataset: object) -> str | None:
    metadata = getattr(dataset, "metadata", {})
    if isinstance(metadata, dict):
        versioning = metadata.get("versioning")
        if isinstance(versioning, dict):
            family_id = versioning.get("family_id")
            if isinstance(family_id, str) and family_id.strip():
                return family_id
    source = getattr(dataset, "source", {})
    if isinstance(source, dict):
        family_id = source.get("family_id")
        if isinstance(family_id, str) and family_id.strip():
            return family_id
    return None


def _source_dataset_id_from_dataset(dataset: object) -> str | None:
    source = getattr(dataset, "source", {})
    if isinstance(source, dict):
        value = source.get("source_dataset_id")
        if isinstance(value, str) and value.strip():
            return value
    cases = getattr(dataset, "cases", ())
    values: set[str] = set()
    for case in cases:
        metadata = getattr(case, "metadata", {})
        if not isinstance(metadata, dict):
            continue
        harvest = metadata.get("harvest")
        if not isinstance(harvest, dict):
            continue
        value = harvest.get("source_dataset_id")
        if isinstance(value, str) and value.strip():
            values.add(value)
    return next(iter(values)) if len(values) == 1 else None


def _primary_failure_type_from_dataset(dataset: object) -> str | None:
    source = getattr(dataset, "source", {})
    if isinstance(source, dict):
        signal = source.get("signal")
        if isinstance(signal, dict):
            raw_drivers = signal.get("top_drivers")
            if isinstance(raw_drivers, list):
                for entry in raw_drivers:
                    if not isinstance(entry, dict):
                        continue
                    failure_type = entry.get("failure_type")
                    if isinstance(failure_type, str) and failure_type.strip():
                        return failure_type
    return None
