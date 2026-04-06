"""Saved portfolio plan preflight, execution, and receipt persistence."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from model_failure_lab.schemas import JsonValue
from model_failure_lab.storage import (
    portfolio_plan_execution_file,
    portfolio_plan_executions_root,
    project_root,
    read_json,
    write_json,
)

from .lifecycle import get_active_lifecycle_action
from .policy import LifecycleRecommendation, describe_dataset_family_lifecycle
from .portfolio import (
    PortfolioPlanAction,
    SavedPortfolioPlan,
    get_dataset_portfolio_item,
    get_saved_portfolio_plan,
)
from .workflow import get_dataset_family_health

_ALLOWED_EXECUTION_MODES = {"batch", "stepwise"}


@dataclass(slots=True, frozen=True)
class PortfolioPlanPreflightCheck:
    family_id: str
    action: str
    status: str
    summary: str
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    dependency_family_ids: tuple[str, ...] = ()
    active_lifecycle_action: str | None = None
    active_lifecycle_action_id: str | None = None
    current_recommendation_action: str | None = None
    target_family_id: str | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "family_id": self.family_id,
            "action": self.action,
            "status": self.status,
            "summary": self.summary,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "dependency_family_ids": list(self.dependency_family_ids),
            "active_lifecycle_action": self.active_lifecycle_action,
            "active_lifecycle_action_id": self.active_lifecycle_action_id,
            "current_recommendation_action": self.current_recommendation_action,
            "target_family_id": self.target_family_id,
        }


@dataclass(slots=True, frozen=True)
class PortfolioPlanPreflight:
    plan_id: str
    created_at: str
    status: str
    total_actions: int
    ready_actions: int
    blocked_actions: int
    already_applied_actions: int
    checks: tuple[PortfolioPlanPreflightCheck, ...]

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "plan_id": self.plan_id,
            "created_at": self.created_at,
            "status": self.status,
            "total_actions": self.total_actions,
            "ready_actions": self.ready_actions,
            "blocked_actions": self.blocked_actions,
            "already_applied_actions": self.already_applied_actions,
            "checks": [check.to_payload() for check in self.checks],
        }


@dataclass(slots=True, frozen=True)
class PortfolioExecutionSnapshot:
    family_id: str
    captured_at: str
    health_label: str | None = None
    trend_label: str | None = None
    version_count: int | None = None
    latest_dataset_id: str | None = None
    latest_version_tag: str | None = None
    recent_fail_rate: float | None = None
    priority_rank: int | None = None
    priority_band: str | None = None
    priority_score: float | None = None
    active_lifecycle_action: str | None = None
    active_lifecycle_condition: str | None = None
    active_lifecycle_applied_at: str | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "family_id": self.family_id,
            "captured_at": self.captured_at,
            "health_label": self.health_label,
            "trend_label": self.trend_label,
            "version_count": self.version_count,
            "latest_dataset_id": self.latest_dataset_id,
            "latest_version_tag": self.latest_version_tag,
            "recent_fail_rate": (
                round(self.recent_fail_rate, 6) if self.recent_fail_rate is not None else None
            ),
            "priority_rank": self.priority_rank,
            "priority_band": self.priority_band,
            "priority_score": (
                round(self.priority_score, 6) if self.priority_score is not None else None
            ),
            "active_lifecycle_action": self.active_lifecycle_action,
            "active_lifecycle_condition": self.active_lifecycle_condition,
            "active_lifecycle_applied_at": self.active_lifecycle_applied_at,
        }


@dataclass(slots=True, frozen=True)
class PortfolioExecutionFollowUp:
    status: str
    summary: str
    datasets: tuple[str, ...]
    models: tuple[str, ...]
    comparison_ids: tuple[str, ...]
    next_steps: tuple[str, ...]

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "status": self.status,
            "summary": self.summary,
            "datasets": list(self.datasets),
            "models": list(self.models),
            "comparison_ids": list(self.comparison_ids),
            "next_steps": list(self.next_steps),
        }


@dataclass(slots=True, frozen=True)
class PortfolioPlanExecutionCheckpoint:
    checkpoint_index: int
    family_id: str
    action: str
    status: str
    recorded_at: str
    summary: str

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "checkpoint_index": self.checkpoint_index,
            "family_id": self.family_id,
            "action": self.action,
            "status": self.status,
            "recorded_at": self.recorded_at,
            "summary": self.summary,
        }


@dataclass(slots=True, frozen=True)
class PortfolioPlanExecutionReceipt:
    checkpoint_index: int
    family_id: str
    action: str
    status: str
    recorded_at: str
    rationale: str
    lifecycle_action_id: str | None
    output_path: str | None
    rollback_guidance: str
    before_snapshot: PortfolioExecutionSnapshot | None
    after_snapshot: PortfolioExecutionSnapshot | None
    preflight: PortfolioPlanPreflightCheck
    follow_up: PortfolioExecutionFollowUp

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "checkpoint_index": self.checkpoint_index,
            "family_id": self.family_id,
            "action": self.action,
            "status": self.status,
            "recorded_at": self.recorded_at,
            "rationale": self.rationale,
            "lifecycle_action_id": self.lifecycle_action_id,
            "output_path": self.output_path,
            "rollback_guidance": self.rollback_guidance,
            "before_snapshot": (
                self.before_snapshot.to_payload() if self.before_snapshot is not None else None
            ),
            "after_snapshot": (
                self.after_snapshot.to_payload() if self.after_snapshot is not None else None
            ),
            "preflight": self.preflight.to_payload(),
            "follow_up": self.follow_up.to_payload(),
        }


@dataclass(slots=True, frozen=True)
class PortfolioPlanExecution:
    execution_id: str
    plan_id: str
    created_at: str
    completed_at: str | None
    mode: str
    status: str
    rationale: str
    selected_family_ids: tuple[str, ...]
    remaining_family_ids: tuple[str, ...]
    total_action_count: int
    completed_checkpoint_count: int
    preflight: PortfolioPlanPreflight
    checkpoints: tuple[PortfolioPlanExecutionCheckpoint, ...]
    receipts: tuple[PortfolioPlanExecutionReceipt, ...]

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "execution_id": self.execution_id,
            "plan_id": self.plan_id,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "mode": self.mode,
            "status": self.status,
            "rationale": self.rationale,
            "selected_family_ids": list(self.selected_family_ids),
            "remaining_family_ids": list(self.remaining_family_ids),
            "total_action_count": self.total_action_count,
            "completed_checkpoint_count": self.completed_checkpoint_count,
            "preflight": self.preflight.to_payload(),
            "checkpoints": [checkpoint.to_payload() for checkpoint in self.checkpoints],
            "receipts": [receipt.to_payload() for receipt in self.receipts],
        }


@dataclass(slots=True, frozen=True)
class PortfolioPlanExecutionResult:
    status: str
    output_path: Path
    execution: PortfolioPlanExecution

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "status": self.status,
            "output_path": str(self.output_path),
            "execution": self.execution.to_payload(),
        }


def preflight_saved_portfolio_plan(
    plan_id: str,
    *,
    root: str | Path | None = None,
    family_ids: tuple[str, ...] | None = None,
    captured_at: str | None = None,
) -> PortfolioPlanPreflight:
    active_root = project_root(root).resolve()
    plan = get_saved_portfolio_plan(plan_id, root=active_root)
    if plan is None:
        raise ValueError(f"portfolio plan not found: {plan_id}")
    selected_actions = _select_plan_actions(plan, family_ids)
    selected_family_ids = {action.family_id for action in selected_actions}
    generated_at = captured_at or _now_timestamp()
    checks: list[PortfolioPlanPreflightCheck] = []
    for action in selected_actions:
        family_health = get_dataset_family_health(action.family_id, root=active_root)
        portfolio_item = get_dataset_portfolio_item(action.family_id, root=active_root)
        active_action = get_active_lifecycle_action(action.family_id, root=active_root)
        current_recommendation = describe_dataset_family_lifecycle(
            action.family_id,
            root=active_root,
            projected_case_count=(
                family_health.latest_case_count
                if family_health is not None
                else action.projected_case_count
            ),
        )

        blockers: list[str] = []
        warnings: list[str] = []
        if family_health is None:
            blockers.append(
                "Dataset family no longer exists in the current immutable version history."
            )
        if portfolio_item is None:
            blockers.append("Dataset family no longer resolves to a current portfolio queue item.")
        if current_recommendation is None:
            blockers.append("Current lifecycle recommendation could not be recomputed.")
        elif current_recommendation.action != action.action:
            if active_action is not None and active_action.action == action.action:
                warnings.append(
                    "Saved plan action is already applied, but the current recommendation has moved."
                )
            else:
                blockers.append(
                    "Saved plan action no longer matches the current lifecycle recommendation."
                )

        missing_dependencies = tuple(
            dependency
            for dependency in action.dependency_family_ids
            if dependency not in selected_family_ids
        )
        if missing_dependencies:
            blockers.append(
                "Execution selection omits dependent family actions required by this plan action."
            )
        if action.target_family_id is not None:
            target_health = get_dataset_family_health(action.target_family_id, root=active_root)
            if target_health is None:
                blockers.append(
                    f"Target family `{action.target_family_id}` is unavailable in the current root."
                )

        status = "ready"
        if blockers:
            status = "blocked"
        elif active_action is not None and active_action.action == action.action:
            status = "already_applied"
        summary = _preflight_summary(
            action=action,
            status=status,
            blockers=tuple(blockers),
            current_recommendation_action=(
                current_recommendation.action if current_recommendation is not None else None
            ),
        )
        checks.append(
            PortfolioPlanPreflightCheck(
                family_id=action.family_id,
                action=action.action,
                status=status,
                summary=summary,
                blockers=tuple(blockers),
                warnings=tuple(warnings),
                dependency_family_ids=action.dependency_family_ids,
                active_lifecycle_action=active_action.action if active_action is not None else None,
                active_lifecycle_action_id=(
                    active_action.action_id if active_action is not None else None
                ),
                current_recommendation_action=(
                    current_recommendation.action if current_recommendation is not None else None
                ),
                target_family_id=action.target_family_id,
            )
        )

    blocked_actions = sum(1 for check in checks if check.status == "blocked")
    already_applied_actions = sum(1 for check in checks if check.status == "already_applied")
    ready_actions = sum(1 for check in checks if check.status == "ready")
    if blocked_actions:
        status = "blocked"
    elif ready_actions:
        status = "ready"
    else:
        status = "already_applied"
    return PortfolioPlanPreflight(
        plan_id=plan.plan_id,
        created_at=generated_at,
        status=status,
        total_actions=len(checks),
        ready_actions=ready_actions,
        blocked_actions=blocked_actions,
        already_applied_actions=already_applied_actions,
        checks=tuple(checks),
    )


def execute_saved_portfolio_plan(
    plan_id: str,
    *,
    root: str | Path | None = None,
    family_ids: tuple[str, ...] | None = None,
    mode: str = "batch",
    max_actions: int | None = None,
    source: str = "cli",
    execution_id: str | None = None,
    executed_at: str | None = None,
) -> PortfolioPlanExecutionResult:
    active_root = project_root(root).resolve()
    normalized_mode = _normalize_mode(mode)
    started_at = executed_at or _now_timestamp()
    preflight = preflight_saved_portfolio_plan(
        plan_id,
        root=active_root,
        family_ids=family_ids,
        captured_at=started_at,
    )
    plan = get_saved_portfolio_plan(plan_id, root=active_root)
    if plan is None:
        raise ValueError(f"portfolio plan not found: {plan_id}")
    selected_actions = _select_plan_actions(plan, family_ids)
    resolved_execution_id = execution_id or _build_execution_id(
        plan_id=plan.plan_id,
        family_ids=tuple(action.family_id for action in selected_actions),
        mode=normalized_mode,
        executed_at=started_at,
    )
    output_path = portfolio_plan_execution_file(
        resolved_execution_id,
        root=active_root,
        create=True,
    )
    if output_path.exists():
        existing = _execution_from_payload(read_json(output_path))
        return PortfolioPlanExecutionResult(
            status="already_exists",
            output_path=output_path,
            execution=existing,
        )

    check_by_family = {check.family_id: check for check in preflight.checks}
    ready_limit = _resolve_ready_limit(
        mode=normalized_mode,
        max_actions=max_actions,
        ready_actions=preflight.ready_actions,
    )
    receipts: list[PortfolioPlanExecutionReceipt] = []
    checkpoints: list[PortfolioPlanExecutionCheckpoint] = []
    remaining_ready_family_ids = [
        action.family_id
        for action in selected_actions
        if check_by_family[action.family_id].status == "ready"
    ]
    execution = PortfolioPlanExecution(
        execution_id=resolved_execution_id,
        plan_id=plan.plan_id,
        created_at=started_at,
        completed_at=None,
        mode=normalized_mode,
        status="running" if preflight.status != "blocked" else "blocked",
        rationale=(
            "Saved plan execution is running with persisted checkpoints."
            if preflight.status != "blocked"
            else "Preflight blocked execution before any lifecycle action was applied."
        ),
        selected_family_ids=tuple(action.family_id for action in selected_actions),
        remaining_family_ids=tuple(remaining_ready_family_ids),
        total_action_count=len(selected_actions),
        completed_checkpoint_count=0,
        preflight=preflight,
        checkpoints=(),
        receipts=(),
    )
    _write_execution(output_path, execution)

    if preflight.status == "blocked":
        return PortfolioPlanExecutionResult(
            status="blocked",
            output_path=output_path,
            execution=execution,
        )

    completed_ready_actions = 0
    checkpoint_index = 0
    for action in selected_actions:
        check = check_by_family[action.family_id]
        if check.status == "ready" and completed_ready_actions >= ready_limit:
            continue

        checkpoint_index += 1
        recorded_at = _now_timestamp()
        before_snapshot = _capture_family_snapshot(action.family_id, root=active_root)
        after_snapshot = before_snapshot
        lifecycle_action_id: str | None = None
        lifecycle_output_path: str | None = None
        receipt_status = check.status
        if check.status == "ready":
            result = _apply_action_from_plan(
                action,
                root=active_root,
                source=f"portfolio-execution:{plan.plan_id}:{source}",
            )
            receipt_status = result.status
            lifecycle_action_id = result.record.action_id
            lifecycle_output_path = str(result.output_path)
            after_snapshot = _capture_family_snapshot(action.family_id, root=active_root)
            completed_ready_actions += 1
            if action.family_id in remaining_ready_family_ids:
                remaining_ready_family_ids.remove(action.family_id)
        else:
            lifecycle_action_id = check.active_lifecycle_action_id
            if action.family_id in remaining_ready_family_ids:
                remaining_ready_family_ids.remove(action.family_id)

        receipt = PortfolioPlanExecutionReceipt(
            checkpoint_index=checkpoint_index,
            family_id=action.family_id,
            action=action.action,
            status=receipt_status,
            recorded_at=recorded_at,
            rationale=action.rationale,
            lifecycle_action_id=lifecycle_action_id,
            output_path=lifecycle_output_path,
            rollback_guidance=_build_rollback_guidance(
                action=action.action,
                before_snapshot=before_snapshot,
            ),
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            preflight=check,
            follow_up=_build_follow_up(action),
        )
        checkpoint = PortfolioPlanExecutionCheckpoint(
            checkpoint_index=checkpoint_index,
            family_id=action.family_id,
            action=action.action,
            status=receipt.status,
            recorded_at=recorded_at,
            summary=check.summary,
        )
        receipts.append(receipt)
        checkpoints.append(checkpoint)
        execution = PortfolioPlanExecution(
            execution_id=resolved_execution_id,
            plan_id=plan.plan_id,
            created_at=started_at,
            completed_at=None,
            mode=normalized_mode,
            status="running",
            rationale="Saved plan execution is running with persisted checkpoints.",
            selected_family_ids=tuple(action.family_id for action in selected_actions),
            remaining_family_ids=tuple(remaining_ready_family_ids),
            total_action_count=len(selected_actions),
            completed_checkpoint_count=len(checkpoints),
            preflight=preflight,
            checkpoints=tuple(checkpoints),
            receipts=tuple(receipts),
        )
        _write_execution(output_path, execution)

    final_status = _final_execution_status(
        receipts=tuple(receipts),
        remaining_family_ids=tuple(remaining_ready_family_ids),
    )
    completed_at = _now_timestamp()
    final_execution = PortfolioPlanExecution(
        execution_id=resolved_execution_id,
        plan_id=plan.plan_id,
        created_at=started_at,
        completed_at=completed_at,
        mode=normalized_mode,
        status=final_status,
        rationale=_final_execution_rationale(
            status=final_status,
            receipts=tuple(receipts),
            remaining_family_ids=tuple(remaining_ready_family_ids),
            preflight=preflight,
        ),
        selected_family_ids=tuple(action.family_id for action in selected_actions),
        remaining_family_ids=tuple(remaining_ready_family_ids),
        total_action_count=len(selected_actions),
        completed_checkpoint_count=len(checkpoints),
        preflight=preflight,
        checkpoints=tuple(checkpoints),
        receipts=tuple(receipts),
    )
    _write_execution(output_path, final_execution)
    return PortfolioPlanExecutionResult(
        status=final_status,
        output_path=output_path,
        execution=final_execution,
    )


def list_saved_portfolio_plan_executions(
    *,
    root: str | Path | None = None,
    plan_id: str | None = None,
    family_id: str | None = None,
    limit: int = 20,
) -> tuple[PortfolioPlanExecution, ...]:
    execution_root = portfolio_plan_executions_root(root=project_root(root), create=False)
    if not execution_root.exists():
        return ()
    rows: list[PortfolioPlanExecution] = []
    for artifact_path in sorted(execution_root.glob("*.json")):
        execution = _execution_from_payload(read_json(artifact_path))
        if plan_id is not None and execution.plan_id != plan_id:
            continue
        if family_id is not None and family_id not in execution.selected_family_ids:
            continue
        rows.append(execution)
    rows.sort(
        key=lambda execution: (
            execution.created_at,
            execution.execution_id,
        ),
        reverse=True,
    )
    return tuple(rows[: max(limit, 1)])


def get_saved_portfolio_plan_execution(
    execution_id: str,
    *,
    root: str | Path | None = None,
) -> PortfolioPlanExecution | None:
    artifact_path = portfolio_plan_execution_file(
        execution_id,
        root=project_root(root),
        create=False,
    )
    if not artifact_path.exists():
        return None
    return _execution_from_payload(read_json(artifact_path))


def _apply_action_from_plan(
    action: PortfolioPlanAction,
    *,
    root: Path,
    source: str,
):
    from .lifecycle import apply_lifecycle_action

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
    return apply_lifecycle_action(
        family_id=action.family_id,
        recommendation=recommendation,
        root=root,
        action=action.action,
        source=source,
    )


def _capture_family_snapshot(
    family_id: str,
    *,
    root: Path,
) -> PortfolioExecutionSnapshot | None:
    family_health = get_dataset_family_health(family_id, root=root)
    portfolio_item = get_dataset_portfolio_item(family_id, root=root)
    active_action = get_active_lifecycle_action(family_id, root=root)
    if family_health is None and portfolio_item is None and active_action is None:
        return None
    return PortfolioExecutionSnapshot(
        family_id=family_id,
        captured_at=_now_timestamp(),
        health_label=family_health.health_label if family_health is not None else None,
        trend_label=family_health.trend_label if family_health is not None else None,
        version_count=family_health.version_count if family_health is not None else None,
        latest_dataset_id=(
            family_health.latest_dataset_id if family_health is not None else None
        ),
        latest_version_tag=(
            family_health.latest_version_tag if family_health is not None else None
        ),
        recent_fail_rate=family_health.recent_fail_rate if family_health is not None else None,
        priority_rank=portfolio_item.priority_rank if portfolio_item is not None else None,
        priority_band=portfolio_item.priority_band if portfolio_item is not None else None,
        priority_score=portfolio_item.priority_score if portfolio_item is not None else None,
        active_lifecycle_action=active_action.action if active_action is not None else None,
        active_lifecycle_condition=(
            active_action.health_condition if active_action is not None else None
        ),
        active_lifecycle_applied_at=(
            active_action.applied_at if active_action is not None else None
        ),
    )


def _build_follow_up(action: PortfolioPlanAction) -> PortfolioExecutionFollowUp:
    datasets = tuple(sorted(action.datasets))
    models = tuple(sorted(action.models))
    comparison_ids = tuple(sorted(action.comparison_ids))
    next_steps: list[str] = []
    if datasets and models:
        next_steps.append(
            "Rerun the affected dataset scope against the models already linked to this family "
            f"({', '.join(models)}) over dataset(s) {', '.join(datasets)}."
        )
    elif datasets:
        next_steps.append(
            f"Rerun the affected dataset scope for {', '.join(datasets)} to capture post-action results."
        )
    else:
        next_steps.append(
            "Rerun the affected family scope to collect post-action results before the next review."
        )
    if comparison_ids:
        next_steps.append(
            "Compare the new runs against the source comparison context "
            f"({', '.join(comparison_ids[:3])}) to verify health and priority changed as expected."
        )
    else:
        next_steps.append(
            "Compare the next saved runs against the most recent baseline/candidate pair tied to this family."
        )
    return PortfolioExecutionFollowUp(
        status="prepared",
        summary=(
            "Prepared deterministic rerun/compare scope from the saved plan action without "
            "launching any background work."
        ),
        datasets=datasets,
        models=models,
        comparison_ids=comparison_ids,
        next_steps=tuple(next_steps),
    )


def _build_rollback_guidance(
    *,
    action: str,
    before_snapshot: PortfolioExecutionSnapshot | None,
) -> str:
    if before_snapshot is None or before_snapshot.active_lifecycle_action is None:
        return (
            "No prior lifecycle action was recorded. Review the family manually before applying "
            "an alternative action."
        )
    if before_snapshot.active_lifecycle_action == action:
        return "No rollback is required because this lifecycle action was already active."
    return (
        "Reapply the prior lifecycle action "
        f"`{before_snapshot.active_lifecycle_action}` to restore the previous recorded family state."
    )


def _final_execution_status(
    *,
    receipts: tuple[PortfolioPlanExecutionReceipt, ...],
    remaining_family_ids: tuple[str, ...],
) -> str:
    if remaining_family_ids:
        return "checkpointed"
    if receipts and all(receipt.status == "already_applied" for receipt in receipts):
        return "already_applied"
    return "executed"


def _final_execution_rationale(
    *,
    status: str,
    receipts: tuple[PortfolioPlanExecutionReceipt, ...],
    remaining_family_ids: tuple[str, ...],
    preflight: PortfolioPlanPreflight,
) -> str:
    if status == "checkpointed":
        return (
            f"Executed {len(receipts)} checkpoints and left {len(remaining_family_ids)} ready "
            "family actions for the next explicit execution step."
        )
    if status == "already_applied":
        return "Selected saved plan actions were already reflected in the current lifecycle state."
    if preflight.ready_actions == 0:
        return "No ready actions remained after preflight review."
    return f"Executed all {preflight.ready_actions} ready saved plan actions."


def _resolve_ready_limit(*, mode: str, max_actions: int | None, ready_actions: int) -> int:
    if ready_actions <= 0:
        return 0
    if max_actions is not None:
        return max(1, min(int(max_actions), ready_actions))
    if mode == "stepwise":
        return 1
    return ready_actions


def _select_plan_actions(
    plan: SavedPortfolioPlan,
    family_ids: tuple[str, ...] | None,
) -> tuple[PortfolioPlanAction, ...]:
    if family_ids is None:
        return plan.actions
    requested = tuple(dict.fromkeys(family_ids))
    action_by_family = {action.family_id: action for action in plan.actions}
    missing = [family_id for family_id in requested if family_id not in action_by_family]
    if missing:
        raise ValueError(
            f"portfolio plan {plan.plan_id} does not contain family ids: {', '.join(missing)}"
        )
    return tuple(action_by_family[family_id] for family_id in requested)


def _preflight_summary(
    *,
    action: PortfolioPlanAction,
    status: str,
    blockers: tuple[str, ...],
    current_recommendation_action: str | None,
) -> str:
    if status == "blocked":
        return blockers[0]
    if status == "already_applied":
        return f"Lifecycle action `{action.action}` is already the active family state."
    if current_recommendation_action is not None and current_recommendation_action != action.action:
        return (
            f"Plan action `{action.action}` is ready, but review the updated recommendation "
            f"`{current_recommendation_action}` before continuing."
        )
    return f"Ready to apply `{action.action}` to `{action.family_id}`."


def _normalize_mode(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in _ALLOWED_EXECUTION_MODES:
        allowed = ", ".join(sorted(_ALLOWED_EXECUTION_MODES))
        raise ValueError(f"unsupported execution mode: {value}. Expected one of: {allowed}")
    return normalized


def _build_execution_id(
    *,
    plan_id: str,
    family_ids: tuple[str, ...],
    mode: str,
    executed_at: str,
) -> str:
    digest = hashlib.sha1(
        "|".join([plan_id, ",".join(family_ids), mode, executed_at]).encode("utf-8")
    ).hexdigest()[:16]
    return f"execution-{digest}"


def _write_execution(path: Path, execution: PortfolioPlanExecution) -> None:
    write_json(path, execution.to_payload())


def _execution_from_payload(payload: dict[str, JsonValue]) -> PortfolioPlanExecution:
    return PortfolioPlanExecution(
        execution_id=str(payload.get("execution_id", "")),
        plan_id=str(payload.get("plan_id", "")),
        created_at=str(payload.get("created_at", "")),
        completed_at=_string_or_none(payload.get("completed_at")),
        mode=str(payload.get("mode", "")),
        status=str(payload.get("status", "")),
        rationale=str(payload.get("rationale", "")),
        selected_family_ids=_string_tuple(payload.get("selected_family_ids")),
        remaining_family_ids=_string_tuple(payload.get("remaining_family_ids")),
        total_action_count=_int_or_zero(payload.get("total_action_count")),
        completed_checkpoint_count=_int_or_zero(payload.get("completed_checkpoint_count")),
        preflight=_preflight_from_payload(payload.get("preflight")),
        checkpoints=_checkpoints_from_payload(payload.get("checkpoints")),
        receipts=_receipts_from_payload(payload.get("receipts")),
    )


def _preflight_from_payload(value: object) -> PortfolioPlanPreflight:
    payload = value if isinstance(value, dict) else {}
    return PortfolioPlanPreflight(
        plan_id=str(payload.get("plan_id", "")),
        created_at=str(payload.get("created_at", "")),
        status=str(payload.get("status", "")),
        total_actions=_int_or_zero(payload.get("total_actions")),
        ready_actions=_int_or_zero(payload.get("ready_actions")),
        blocked_actions=_int_or_zero(payload.get("blocked_actions")),
        already_applied_actions=_int_or_zero(payload.get("already_applied_actions")),
        checks=_preflight_checks_from_payload(payload.get("checks")),
    )


def _preflight_checks_from_payload(value: object) -> tuple[PortfolioPlanPreflightCheck, ...]:
    if not isinstance(value, list):
        return ()
    checks: list[PortfolioPlanPreflightCheck] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        checks.append(
            PortfolioPlanPreflightCheck(
                family_id=str(entry.get("family_id", "")),
                action=str(entry.get("action", "")),
                status=str(entry.get("status", "")),
                summary=str(entry.get("summary", "")),
                blockers=_string_tuple(entry.get("blockers")),
                warnings=_string_tuple(entry.get("warnings")),
                dependency_family_ids=_string_tuple(entry.get("dependency_family_ids")),
                active_lifecycle_action=_string_or_none(entry.get("active_lifecycle_action")),
                active_lifecycle_action_id=_string_or_none(
                    entry.get("active_lifecycle_action_id")
                ),
                current_recommendation_action=_string_or_none(
                    entry.get("current_recommendation_action")
                ),
                target_family_id=_string_or_none(entry.get("target_family_id")),
            )
        )
    return tuple(checks)


def _snapshot_from_payload(value: object) -> PortfolioExecutionSnapshot | None:
    if not isinstance(value, dict):
        return None
    return PortfolioExecutionSnapshot(
        family_id=str(value.get("family_id", "")),
        captured_at=str(value.get("captured_at", "")),
        health_label=_string_or_none(value.get("health_label")),
        trend_label=_string_or_none(value.get("trend_label")),
        version_count=_int_or_none(value.get("version_count")),
        latest_dataset_id=_string_or_none(value.get("latest_dataset_id")),
        latest_version_tag=_string_or_none(value.get("latest_version_tag")),
        recent_fail_rate=_float_or_none(value.get("recent_fail_rate")),
        priority_rank=_int_or_none(value.get("priority_rank")),
        priority_band=_string_or_none(value.get("priority_band")),
        priority_score=_float_or_none(value.get("priority_score")),
        active_lifecycle_action=_string_or_none(value.get("active_lifecycle_action")),
        active_lifecycle_condition=_string_or_none(value.get("active_lifecycle_condition")),
        active_lifecycle_applied_at=_string_or_none(value.get("active_lifecycle_applied_at")),
    )


def _follow_up_from_payload(value: object) -> PortfolioExecutionFollowUp:
    payload = value if isinstance(value, dict) else {}
    return PortfolioExecutionFollowUp(
        status=str(payload.get("status", "")),
        summary=str(payload.get("summary", "")),
        datasets=_string_tuple(payload.get("datasets")),
        models=_string_tuple(payload.get("models")),
        comparison_ids=_string_tuple(payload.get("comparison_ids")),
        next_steps=_string_tuple(payload.get("next_steps")),
    )


def _checkpoints_from_payload(value: object) -> tuple[PortfolioPlanExecutionCheckpoint, ...]:
    if not isinstance(value, list):
        return ()
    checkpoints: list[PortfolioPlanExecutionCheckpoint] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        checkpoints.append(
            PortfolioPlanExecutionCheckpoint(
                checkpoint_index=_int_or_zero(entry.get("checkpoint_index")),
                family_id=str(entry.get("family_id", "")),
                action=str(entry.get("action", "")),
                status=str(entry.get("status", "")),
                recorded_at=str(entry.get("recorded_at", "")),
                summary=str(entry.get("summary", "")),
            )
        )
    return tuple(checkpoints)


def _receipts_from_payload(value: object) -> tuple[PortfolioPlanExecutionReceipt, ...]:
    if not isinstance(value, list):
        return ()
    receipts: list[PortfolioPlanExecutionReceipt] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        receipts.append(
            PortfolioPlanExecutionReceipt(
                checkpoint_index=_int_or_zero(entry.get("checkpoint_index")),
                family_id=str(entry.get("family_id", "")),
                action=str(entry.get("action", "")),
                status=str(entry.get("status", "")),
                recorded_at=str(entry.get("recorded_at", "")),
                rationale=str(entry.get("rationale", "")),
                lifecycle_action_id=_string_or_none(entry.get("lifecycle_action_id")),
                output_path=_string_or_none(entry.get("output_path")),
                rollback_guidance=str(entry.get("rollback_guidance", "")),
                before_snapshot=_snapshot_from_payload(entry.get("before_snapshot")),
                after_snapshot=_snapshot_from_payload(entry.get("after_snapshot")),
                preflight=_preflight_check_from_payload(entry.get("preflight")),
                follow_up=_follow_up_from_payload(entry.get("follow_up")),
            )
        )
    return tuple(receipts)


def _preflight_check_from_payload(value: object) -> PortfolioPlanPreflightCheck:
    payload = value if isinstance(value, dict) else {}
    return PortfolioPlanPreflightCheck(
        family_id=str(payload.get("family_id", "")),
        action=str(payload.get("action", "")),
        status=str(payload.get("status", "")),
        summary=str(payload.get("summary", "")),
        blockers=_string_tuple(payload.get("blockers")),
        warnings=_string_tuple(payload.get("warnings")),
        dependency_family_ids=_string_tuple(payload.get("dependency_family_ids")),
        active_lifecycle_action=_string_or_none(payload.get("active_lifecycle_action")),
        active_lifecycle_action_id=_string_or_none(payload.get("active_lifecycle_action_id")),
        current_recommendation_action=_string_or_none(
            payload.get("current_recommendation_action")
        ),
        target_family_id=_string_or_none(payload.get("target_family_id")),
    )


def _int_or_zero(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _float_or_none(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(entry for entry in value if isinstance(entry, str) and entry.strip())


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
