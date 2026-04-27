"""Outcome attestation and measured follow-up helpers for saved plan executions."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from model_failure_lab.index import QueryFilters, query_comparison_signals
from model_failure_lab.reporting.load import load_saved_run_artifacts
from model_failure_lab.schemas import JsonValue
from model_failure_lab.storage import (
    portfolio_outcome_attestation_file,
    project_root,
    read_json,
    report_details_file,
    report_file,
    write_json,
)

from .execution import (
    PortfolioExecutionFollowUp,
    PortfolioExecutionSnapshot,
    PortfolioPlanExecutionReceipt,
    get_saved_portfolio_plan_execution,
    list_saved_portfolio_plan_executions,
)

_OUTCOME_STATES = {"open", "evidence_linked", "attested"}
_OUTCOME_VERDICTS = {"improved", "regressed", "inconclusive", "no_signal"}


@dataclass(slots=True, frozen=True)
class PortfolioOutcomeSignalSummary:
    comparison_id: str
    created_at: str
    dataset: str | None
    baseline_model: str | None
    candidate_model: str | None
    compatible: bool
    signal_verdict: str
    regression_score: float
    improvement_score: float
    severity: float

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "comparison_id": self.comparison_id,
            "created_at": self.created_at,
            "dataset": self.dataset,
            "baseline_model": self.baseline_model,
            "candidate_model": self.candidate_model,
            "compatible": self.compatible,
            "signal_verdict": self.signal_verdict,
            "regression_score": round(self.regression_score, 6),
            "improvement_score": round(self.improvement_score, 6),
            "severity": round(self.severity, 6),
        }


@dataclass(slots=True, frozen=True)
class PortfolioOutcomeDeltaSummary:
    source_comparison_count: int
    follow_up_comparison_count: int
    source_average_severity: float | None
    follow_up_average_severity: float | None
    severity_delta: float | None
    source_regression_count: int
    follow_up_regression_count: int
    source_improvement_count: int
    follow_up_improvement_count: int

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "source_comparison_count": self.source_comparison_count,
            "follow_up_comparison_count": self.follow_up_comparison_count,
            "source_average_severity": _rounded_or_none(self.source_average_severity),
            "follow_up_average_severity": _rounded_or_none(self.follow_up_average_severity),
            "severity_delta": _rounded_or_none(self.severity_delta),
            "source_regression_count": self.source_regression_count,
            "follow_up_regression_count": self.follow_up_regression_count,
            "source_improvement_count": self.source_improvement_count,
            "follow_up_improvement_count": self.follow_up_improvement_count,
        }


@dataclass(slots=True, frozen=True)
class PortfolioOutcomeVerdict:
    status: str
    rationale: str
    source_signals: tuple[PortfolioOutcomeSignalSummary, ...]
    follow_up_signals: tuple[PortfolioOutcomeSignalSummary, ...]
    delta_summary: PortfolioOutcomeDeltaSummary

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "status": self.status,
            "rationale": self.rationale,
            "source_signals": [row.to_payload() for row in self.source_signals],
            "follow_up_signals": [row.to_payload() for row in self.follow_up_signals],
            "delta_summary": self.delta_summary.to_payload(),
        }


@dataclass(slots=True, frozen=True)
class PortfolioOutcomeAttestation:
    attestation_id: str
    execution_id: str
    plan_id: str
    checkpoint_index: int
    family_id: str
    action: str
    receipt_recorded_at: str
    created_at: str
    updated_at: str
    state: str
    source_comparison_ids: tuple[str, ...]
    expected_datasets: tuple[str, ...]
    expected_models: tuple[str, ...]
    linked_run_ids: tuple[str, ...]
    linked_comparison_ids: tuple[str, ...]
    notes: tuple[str, ...]
    closed_at: str | None = None
    verdict: PortfolioOutcomeVerdict | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "attestation_id": self.attestation_id,
            "execution_id": self.execution_id,
            "plan_id": self.plan_id,
            "checkpoint_index": self.checkpoint_index,
            "family_id": self.family_id,
            "action": self.action,
            "receipt_recorded_at": self.receipt_recorded_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "state": self.state,
            "source_comparison_ids": list(self.source_comparison_ids),
            "expected_datasets": list(self.expected_datasets),
            "expected_models": list(self.expected_models),
            "linked_run_ids": list(self.linked_run_ids),
            "linked_comparison_ids": list(self.linked_comparison_ids),
            "notes": list(self.notes),
            "closed_at": self.closed_at,
            "verdict": self.verdict.to_payload() if self.verdict is not None else None,
        }


@dataclass(slots=True, frozen=True)
class PortfolioExecutionOutcome:
    execution_id: str
    plan_id: str
    execution_status: str
    execution_mode: str
    execution_created_at: str
    execution_completed_at: str | None
    checkpoint_index: int
    family_id: str
    action: str
    receipt_status: str
    recorded_at: str
    rationale: str
    rollback_guidance: str
    before_snapshot: PortfolioExecutionSnapshot | None
    after_snapshot: PortfolioExecutionSnapshot | None
    follow_up: PortfolioExecutionFollowUp
    attestation: PortfolioOutcomeAttestation

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "execution_id": self.execution_id,
            "plan_id": self.plan_id,
            "execution_status": self.execution_status,
            "execution_mode": self.execution_mode,
            "execution_created_at": self.execution_created_at,
            "execution_completed_at": self.execution_completed_at,
            "checkpoint_index": self.checkpoint_index,
            "family_id": self.family_id,
            "action": self.action,
            "receipt_status": self.receipt_status,
            "recorded_at": self.recorded_at,
            "rationale": self.rationale,
            "rollback_guidance": self.rollback_guidance,
            "before_snapshot": (
                self.before_snapshot.to_payload() if self.before_snapshot is not None else None
            ),
            "after_snapshot": (
                self.after_snapshot.to_payload() if self.after_snapshot is not None else None
            ),
            "follow_up": self.follow_up.to_payload(),
            "attestation": self.attestation.to_payload(),
        }


@dataclass(slots=True, frozen=True)
class PortfolioOutcomeFeedbackSummary:
    family_id: str
    open_count: int
    evidence_linked_count: int
    attested_count: int
    improved_count: int
    regressed_count: int
    inconclusive_count: int
    no_signal_count: int
    latest_state: str | None
    latest_verdict: str | None
    latest_updated_at: str | None

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "family_id": self.family_id,
            "open_count": self.open_count,
            "evidence_linked_count": self.evidence_linked_count,
            "attested_count": self.attested_count,
            "improved_count": self.improved_count,
            "regressed_count": self.regressed_count,
            "inconclusive_count": self.inconclusive_count,
            "no_signal_count": self.no_signal_count,
            "latest_state": self.latest_state,
            "latest_verdict": self.latest_verdict,
            "latest_updated_at": self.latest_updated_at,
        }


def list_portfolio_execution_outcomes(
    *,
    root: str | Path | None = None,
    family_id: str | None = None,
    plan_id: str | None = None,
    execution_id: str | None = None,
    include_attested: bool = True,
    limit: int = 20,
) -> tuple[PortfolioExecutionOutcome, ...]:
    active_root = project_root(root).resolve()
    execution_rows = list_saved_portfolio_plan_executions(
        root=active_root,
        plan_id=plan_id,
        family_id=family_id,
        limit=max(limit * 10, 50),
    )
    outcomes: list[PortfolioExecutionOutcome] = []
    for execution in execution_rows:
        if execution_id is not None and execution.execution_id != execution_id:
            continue
        for receipt in execution.receipts:
            if family_id is not None and receipt.family_id != family_id:
                continue
            outcome = _build_execution_outcome(
                execution=execution,
                receipt=receipt,
                root=active_root,
            )
            if not include_attested and outcome.attestation.state == "attested":
                continue
            outcomes.append(outcome)
    outcomes.sort(
        key=lambda row: (row.attestation.updated_at, row.recorded_at, row.execution_id),
        reverse=True,
    )
    return tuple(outcomes[: max(limit, 1)])


def get_portfolio_execution_outcome(
    execution_id: str,
    checkpoint_index: int,
    *,
    root: str | Path | None = None,
) -> PortfolioExecutionOutcome:
    active_root = project_root(root).resolve()
    execution, receipt = _resolve_execution_receipt(
        execution_id,
        checkpoint_index,
        root=active_root,
    )
    return _build_execution_outcome(execution=execution, receipt=receipt, root=active_root)


def link_portfolio_execution_outcome_evidence(
    execution_id: str,
    checkpoint_index: int,
    *,
    root: str | Path | None = None,
    run_ids: tuple[str, ...] = (),
    comparison_ids: tuple[str, ...] = (),
    note: str | None = None,
    recorded_at: str | None = None,
) -> PortfolioExecutionOutcome:
    active_root = project_root(root).resolve()
    execution, receipt = _resolve_execution_receipt(
        execution_id,
        checkpoint_index,
        root=active_root,
    )
    _validate_run_ids(run_ids, root=active_root)
    _validate_comparison_ids(comparison_ids, root=active_root)
    existing = _read_attestation_or_default(
        execution=execution,
        receipt=receipt,
        root=active_root,
    )
    linked_run_ids = _merge_string_values(existing.linked_run_ids, run_ids)
    linked_comparison_ids = _merge_string_values(existing.linked_comparison_ids, comparison_ids)
    notes = _append_note(existing.notes, note)
    state = "evidence_linked" if linked_run_ids or linked_comparison_ids else existing.state
    if existing.state == "attested" and (
        linked_run_ids != existing.linked_run_ids
        or linked_comparison_ids != existing.linked_comparison_ids
    ):
        state = "evidence_linked"
    updated = PortfolioOutcomeAttestation(
        attestation_id=existing.attestation_id,
        execution_id=existing.execution_id,
        plan_id=existing.plan_id,
        checkpoint_index=existing.checkpoint_index,
        family_id=existing.family_id,
        action=existing.action,
        receipt_recorded_at=existing.receipt_recorded_at,
        created_at=existing.created_at,
        updated_at=recorded_at or _now_timestamp(),
        state=state,
        source_comparison_ids=existing.source_comparison_ids,
        expected_datasets=existing.expected_datasets,
        expected_models=existing.expected_models,
        linked_run_ids=linked_run_ids,
        linked_comparison_ids=linked_comparison_ids,
        notes=notes,
        closed_at=None if state != "attested" else existing.closed_at,
        verdict=None if state != "attested" else existing.verdict,
    )
    _write_attestation(updated, root=active_root)
    return _build_execution_outcome(execution=execution, receipt=receipt, root=active_root)


def attest_portfolio_execution_outcome(
    execution_id: str,
    checkpoint_index: int,
    *,
    root: str | Path | None = None,
    note: str | None = None,
    recorded_at: str | None = None,
) -> PortfolioExecutionOutcome:
    active_root = project_root(root).resolve()
    execution, receipt = _resolve_execution_receipt(
        execution_id,
        checkpoint_index,
        root=active_root,
    )
    existing = _read_attestation_or_default(
        execution=execution,
        receipt=receipt,
        root=active_root,
    )
    if not existing.linked_run_ids and not existing.linked_comparison_ids:
        raise ValueError(
            "outcome attestation requires at least one linked run or comparison artifact"
        )
    updated_at = recorded_at or _now_timestamp()
    verdict = _build_outcome_verdict(existing, root=active_root)
    updated = PortfolioOutcomeAttestation(
        attestation_id=existing.attestation_id,
        execution_id=existing.execution_id,
        plan_id=existing.plan_id,
        checkpoint_index=existing.checkpoint_index,
        family_id=existing.family_id,
        action=existing.action,
        receipt_recorded_at=existing.receipt_recorded_at,
        created_at=existing.created_at,
        updated_at=updated_at,
        state="attested",
        source_comparison_ids=existing.source_comparison_ids,
        expected_datasets=existing.expected_datasets,
        expected_models=existing.expected_models,
        linked_run_ids=existing.linked_run_ids,
        linked_comparison_ids=existing.linked_comparison_ids,
        notes=_append_note(existing.notes, note),
        closed_at=updated_at,
        verdict=verdict,
    )
    _write_attestation(updated, root=active_root)
    return _build_execution_outcome(execution=execution, receipt=receipt, root=active_root)


def summarize_portfolio_outcomes_for_family(
    family_id: str,
    *,
    root: str | Path | None = None,
) -> PortfolioOutcomeFeedbackSummary | None:
    rows = list_portfolio_execution_outcomes(
        root=root,
        family_id=family_id,
        include_attested=True,
        limit=100,
    )
    if not rows:
        return None
    latest = rows[0].attestation
    verdict_counts = {
        verdict: sum(
            1 for row in rows if row.attestation.verdict is not None and row.attestation.verdict.status == verdict
        )
        for verdict in sorted(_OUTCOME_VERDICTS)
    }
    return PortfolioOutcomeFeedbackSummary(
        family_id=family_id,
        open_count=sum(1 for row in rows if row.attestation.state == "open"),
        evidence_linked_count=sum(
            1 for row in rows if row.attestation.state == "evidence_linked"
        ),
        attested_count=sum(1 for row in rows if row.attestation.state == "attested"),
        improved_count=verdict_counts["improved"],
        regressed_count=verdict_counts["regressed"],
        inconclusive_count=verdict_counts["inconclusive"],
        no_signal_count=verdict_counts["no_signal"],
        latest_state=latest.state,
        latest_verdict=latest.verdict.status if latest.verdict is not None else None,
        latest_updated_at=latest.updated_at,
    )


def _build_execution_outcome(
    *,
    execution,
    receipt: PortfolioPlanExecutionReceipt,
    root: Path,
) -> PortfolioExecutionOutcome:
    attestation = _read_attestation_or_default(
        execution=execution,
        receipt=receipt,
        root=root,
    )
    return PortfolioExecutionOutcome(
        execution_id=execution.execution_id,
        plan_id=execution.plan_id,
        execution_status=execution.status,
        execution_mode=execution.mode,
        execution_created_at=execution.created_at,
        execution_completed_at=execution.completed_at,
        checkpoint_index=receipt.checkpoint_index,
        family_id=receipt.family_id,
        action=receipt.action,
        receipt_status=receipt.status,
        recorded_at=receipt.recorded_at,
        rationale=receipt.rationale,
        rollback_guidance=receipt.rollback_guidance,
        before_snapshot=receipt.before_snapshot,
        after_snapshot=receipt.after_snapshot,
        follow_up=receipt.follow_up,
        attestation=attestation,
    )


def _resolve_execution_receipt(
    execution_id: str,
    checkpoint_index: int,
    *,
    root: Path,
):
    execution = get_saved_portfolio_plan_execution(execution_id, root=root)
    if execution is None:
        raise ValueError(f"portfolio plan execution not found: {execution_id}")
    receipt = next(
        (
            row
            for row in execution.receipts
            if row.checkpoint_index == checkpoint_index
        ),
        None,
    )
    if receipt is None:
        raise ValueError(
            f"portfolio plan execution {execution_id} does not contain checkpoint {checkpoint_index}"
        )
    return execution, receipt


def _read_attestation_or_default(
    *,
    execution,
    receipt: PortfolioPlanExecutionReceipt,
    root: Path,
) -> PortfolioOutcomeAttestation:
    attestation_id = _build_attestation_id(
        execution_id=execution.execution_id,
        checkpoint_index=receipt.checkpoint_index,
        family_id=receipt.family_id,
    )
    artifact_path = portfolio_outcome_attestation_file(
        attestation_id,
        root=root,
        create=False,
    )
    if artifact_path.exists():
        return _attestation_from_payload(read_json(artifact_path))
    return PortfolioOutcomeAttestation(
        attestation_id=attestation_id,
        execution_id=execution.execution_id,
        plan_id=execution.plan_id,
        checkpoint_index=receipt.checkpoint_index,
        family_id=receipt.family_id,
        action=receipt.action,
        receipt_recorded_at=receipt.recorded_at,
        created_at=receipt.recorded_at,
        updated_at=receipt.recorded_at,
        state="open",
        source_comparison_ids=receipt.follow_up.comparison_ids,
        expected_datasets=receipt.follow_up.datasets,
        expected_models=receipt.follow_up.models,
        linked_run_ids=(),
        linked_comparison_ids=(),
        notes=(),
        closed_at=None,
        verdict=None,
    )


def _write_attestation(attestation: PortfolioOutcomeAttestation, *, root: Path) -> None:
    write_json(
        portfolio_outcome_attestation_file(
            attestation.attestation_id,
            root=root,
            create=True,
        ),
        attestation.to_payload(),
    )


def _build_outcome_verdict(
    attestation: PortfolioOutcomeAttestation,
    *,
    root: Path,
) -> PortfolioOutcomeVerdict:
    source_signals = _load_signal_summaries(attestation.source_comparison_ids, root=root)
    follow_up_signals = _load_signal_summaries(attestation.linked_comparison_ids, root=root)
    delta_summary = _build_delta_summary(
        source_signals=source_signals,
        follow_up_signals=follow_up_signals,
    )
    if not follow_up_signals:
        status = "no_signal"
        rationale = "No linked comparison evidence was available when the outcome was attested."
    elif not any(row.compatible for row in follow_up_signals):
        status = "no_signal"
        rationale = (
            "Linked follow-up comparisons are incompatible, so the attestation cannot measure a "
            "deterministic post-action outcome."
        )
    elif not source_signals:
        status = "inconclusive"
        rationale = (
            "Follow-up comparisons were linked, but the source comparison context could not be "
            "resolved for a deterministic before/after signal comparison."
        )
    else:
        severity_delta = delta_summary.severity_delta or 0.0
        follow_up_regressions = delta_summary.follow_up_regression_count
        source_regressions = delta_summary.source_regression_count
        follow_up_improvements = delta_summary.follow_up_improvement_count
        if (
            severity_delta <= -0.05
            and follow_up_regressions <= max(source_regressions - 1, 0)
        ) or (
            severity_delta <= -0.08
            and follow_up_regressions <= source_regressions
        ) or (
            severity_delta <= -0.02
            and follow_up_regressions == 0
            and follow_up_improvements > 0
        ):
            status = "improved"
            rationale = (
                f"Follow-up severity moved by {severity_delta:.3f} with "
                f"{follow_up_regressions} regression comparison(s) versus "
                f"{source_regressions} in the source context."
            )
        elif (
            severity_delta >= 0.05
            or follow_up_regressions > source_regressions
            or (
                delta_summary.follow_up_average_severity is not None
                and delta_summary.source_average_severity is not None
                and delta_summary.follow_up_average_severity
                >= delta_summary.source_average_severity
                and follow_up_regressions > 0
            )
        ):
            status = "regressed"
            rationale = (
                f"Follow-up severity moved by {severity_delta:.3f} with "
                f"{follow_up_regressions} regression comparison(s) versus "
                f"{source_regressions} in the source context."
            )
        else:
            status = "inconclusive"
            rationale = (
                "Follow-up evidence exists, but the linked comparisons did not shift severity or "
                "regression counts enough to prove a deterministic improvement or regression."
            )
    return PortfolioOutcomeVerdict(
        status=status,
        rationale=rationale,
        source_signals=source_signals,
        follow_up_signals=follow_up_signals,
        delta_summary=delta_summary,
    )


def _build_delta_summary(
    *,
    source_signals: tuple[PortfolioOutcomeSignalSummary, ...],
    follow_up_signals: tuple[PortfolioOutcomeSignalSummary, ...],
) -> PortfolioOutcomeDeltaSummary:
    source_average = _average([row.severity for row in source_signals])
    follow_up_average = _average([row.severity for row in follow_up_signals])
    severity_delta = None
    if source_average is not None and follow_up_average is not None:
        severity_delta = follow_up_average - source_average
    return PortfolioOutcomeDeltaSummary(
        source_comparison_count=len(source_signals),
        follow_up_comparison_count=len(follow_up_signals),
        source_average_severity=source_average,
        follow_up_average_severity=follow_up_average,
        severity_delta=severity_delta,
        source_regression_count=sum(
            1 for row in source_signals if row.signal_verdict == "regression"
        ),
        follow_up_regression_count=sum(
            1 for row in follow_up_signals if row.signal_verdict == "regression"
        ),
        source_improvement_count=sum(
            1 for row in source_signals if row.signal_verdict == "improvement"
        ),
        follow_up_improvement_count=sum(
            1 for row in follow_up_signals if row.signal_verdict == "improvement"
        ),
    )


def _load_signal_summaries(
    comparison_ids: tuple[str, ...],
    *,
    root: Path,
) -> tuple[PortfolioOutcomeSignalSummary, ...]:
    rows: list[PortfolioOutcomeSignalSummary] = []
    for comparison_id in comparison_ids:
        matches = query_comparison_signals(
            QueryFilters(report_id=comparison_id, limit=1),
            verdict=None,
            root=root,
        )
        if not matches:
            continue
        row = matches[0]
        rows.append(
            PortfolioOutcomeSignalSummary(
                comparison_id=str(row["report_id"]),
                created_at=str(row["created_at"]),
                dataset=_string_or_none(row.get("dataset")),
                baseline_model=_string_or_none(row.get("baseline_model")),
                candidate_model=_string_or_none(row.get("candidate_model")),
                compatible=bool(row.get("compatible", False)),
                signal_verdict=str(row.get("signal_verdict", "")),
                regression_score=float(row.get("regression_score", 0.0) or 0.0),
                improvement_score=float(row.get("improvement_score", 0.0) or 0.0),
                severity=float(row.get("severity", 0.0) or 0.0),
            )
        )
    return tuple(rows)


def _validate_run_ids(run_ids: tuple[str, ...], *, root: Path) -> None:
    for run_id in run_ids:
        load_saved_run_artifacts(run_id, root=root)


def _validate_comparison_ids(comparison_ids: tuple[str, ...], *, root: Path) -> None:
    for comparison_id in comparison_ids:
        if not report_file(comparison_id, root=root, create=False).exists():
            raise ValueError(f"saved comparison report not found: {comparison_id}")
        if not report_details_file(comparison_id, root=root, create=False).exists():
            raise ValueError(f"saved comparison detail report not found: {comparison_id}")


def _build_attestation_id(
    *,
    execution_id: str,
    checkpoint_index: int,
    family_id: str,
) -> str:
    digest = hashlib.sha1(
        f"{execution_id}|{checkpoint_index}|{family_id}".encode("utf-8")
    ).hexdigest()[:16]
    return f"outcome-{digest}"


def _attestation_from_payload(payload: dict[str, JsonValue]) -> PortfolioOutcomeAttestation:
    state = str(payload.get("state", "open"))
    if state not in _OUTCOME_STATES:
        state = "open"
    verdict_payload = payload.get("verdict")
    return PortfolioOutcomeAttestation(
        attestation_id=str(payload.get("attestation_id", "")),
        execution_id=str(payload.get("execution_id", "")),
        plan_id=str(payload.get("plan_id", "")),
        checkpoint_index=_int_or_zero(payload.get("checkpoint_index")),
        family_id=str(payload.get("family_id", "")),
        action=str(payload.get("action", "")),
        receipt_recorded_at=str(payload.get("receipt_recorded_at", "")),
        created_at=str(payload.get("created_at", "")),
        updated_at=str(payload.get("updated_at", "")),
        state=state,
        source_comparison_ids=_string_tuple(payload.get("source_comparison_ids")),
        expected_datasets=_string_tuple(payload.get("expected_datasets")),
        expected_models=_string_tuple(payload.get("expected_models")),
        linked_run_ids=_string_tuple(payload.get("linked_run_ids")),
        linked_comparison_ids=_string_tuple(payload.get("linked_comparison_ids")),
        notes=_string_tuple(payload.get("notes")),
        closed_at=_string_or_none(payload.get("closed_at")),
        verdict=_verdict_from_payload(verdict_payload),
    )


def _verdict_from_payload(value: object) -> PortfolioOutcomeVerdict | None:
    if not isinstance(value, dict):
        return None
    status = str(value.get("status", ""))
    if status not in _OUTCOME_VERDICTS:
        return None
    return PortfolioOutcomeVerdict(
        status=status,
        rationale=str(value.get("rationale", "")),
        source_signals=_signal_summaries_from_payload(value.get("source_signals")),
        follow_up_signals=_signal_summaries_from_payload(value.get("follow_up_signals")),
        delta_summary=_delta_summary_from_payload(value.get("delta_summary")),
    )


def _signal_summaries_from_payload(value: object) -> tuple[PortfolioOutcomeSignalSummary, ...]:
    if not isinstance(value, list):
        return ()
    rows: list[PortfolioOutcomeSignalSummary] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        rows.append(
            PortfolioOutcomeSignalSummary(
                comparison_id=str(entry.get("comparison_id", "")),
                created_at=str(entry.get("created_at", "")),
                dataset=_string_or_none(entry.get("dataset")),
                baseline_model=_string_or_none(entry.get("baseline_model")),
                candidate_model=_string_or_none(entry.get("candidate_model")),
                compatible=bool(entry.get("compatible", False)),
                signal_verdict=str(entry.get("signal_verdict", "")),
                regression_score=float(entry.get("regression_score", 0.0) or 0.0),
                improvement_score=float(entry.get("improvement_score", 0.0) or 0.0),
                severity=float(entry.get("severity", 0.0) or 0.0),
            )
        )
    return tuple(rows)


def _delta_summary_from_payload(value: object) -> PortfolioOutcomeDeltaSummary:
    payload = value if isinstance(value, dict) else {}
    return PortfolioOutcomeDeltaSummary(
        source_comparison_count=_int_or_zero(payload.get("source_comparison_count")),
        follow_up_comparison_count=_int_or_zero(payload.get("follow_up_comparison_count")),
        source_average_severity=_float_or_none(payload.get("source_average_severity")),
        follow_up_average_severity=_float_or_none(payload.get("follow_up_average_severity")),
        severity_delta=_float_or_none(payload.get("severity_delta")),
        source_regression_count=_int_or_zero(payload.get("source_regression_count")),
        follow_up_regression_count=_int_or_zero(payload.get("follow_up_regression_count")),
        source_improvement_count=_int_or_zero(payload.get("source_improvement_count")),
        follow_up_improvement_count=_int_or_zero(payload.get("follow_up_improvement_count")),
    )


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _merge_string_values(existing: tuple[str, ...], incoming: tuple[str, ...]) -> tuple[str, ...]:
    merged = list(existing)
    seen = set(existing)
    for value in incoming:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        merged.append(normalized)
        seen.add(normalized)
    return tuple(merged)


def _append_note(notes: tuple[str, ...], note: str | None) -> tuple[str, ...]:
    if note is None:
        return notes
    normalized = note.strip()
    if not normalized:
        return notes
    return (*notes, normalized)


def _rounded_or_none(value: float | None) -> float | None:
    return round(value, 6) if value is not None else None


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(
        entry.strip()
        for entry in value
        if isinstance(entry, str) and entry.strip()
    )


def _int_or_zero(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value


def _float_or_none(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _now_timestamp() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
