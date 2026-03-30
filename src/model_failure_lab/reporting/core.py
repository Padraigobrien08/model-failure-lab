"""Aggregate report builders over saved Phase 46 run artifacts."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone

from model_failure_lab.runner import CaseExecution
from model_failure_lab.schemas import JsonValue, NO_FAILURE_TYPE, Report

from .load import SavedRunArtifacts

@dataclass(slots=True, frozen=True)
class CaseSummary:
    """Aggregated case metrics and supporting detail rows."""

    attempted_case_count: int
    classified_case_count: int
    execution_error_count: int
    unclassified_count: int
    successful_model_invocation_count: int
    failure_case_count: int
    failure_counts: dict[str, int]
    failure_rates: dict[str, float]
    failure_breakdown: tuple[dict[str, JsonValue], ...]
    execution_errors: tuple[dict[str, JsonValue], ...]
    unclassified_cases: tuple[dict[str, JsonValue], ...]
    notable_cases: tuple[dict[str, JsonValue], ...]

    def metrics_payload(self) -> dict[str, JsonValue]:
        attempted = self.attempted_case_count
        classified = self.classified_case_count
        successful = self.successful_model_invocation_count
        return {
            "attempted_case_count": attempted,
            "classified_case_count": classified,
            "execution_error_count": self.execution_error_count,
            "unclassified_count": self.unclassified_count,
            "successful_model_invocation_count": successful,
            "failure_case_count": self.failure_case_count,
            "failure_rate": self.failure_case_count / classified if classified else None,
            "classification_coverage": classified / attempted if attempted else None,
            "execution_success_rate": successful / attempted if attempted else None,
        }


@dataclass(slots=True, frozen=True)
class BuiltReport:
    """Compact summary report plus deeper detail payload."""

    report: Report
    details: dict[str, JsonValue]


def summarize_case_executions(case_results: tuple[CaseExecution, ...]) -> CaseSummary:
    """Summarize per-case runner outputs into aggregate reporting metrics."""

    attempted = len(case_results)
    successful_invocations = 0
    execution_errors: list[dict[str, JsonValue]] = []
    unclassified_cases: list[dict[str, JsonValue]] = []
    notable_cases: list[dict[str, JsonValue]] = []
    failure_case_ids: dict[str, list[str]] = {}
    failure_counts: Counter[str] = Counter()
    classified_case_count = 0
    execution_error_count = 0
    unclassified_count = 0

    for case in case_results:
        if case.output is not None:
            successful_invocations += 1
        if case.output is None:
            execution_error_count += 1
            execution_errors.append(_error_row(case))
            continue

        if case.classification is None:
            unclassified_count += 1
            unclassified_cases.append(_unclassified_row(case))
            continue

        classified_case_count += 1
        failure_type = case.classification.failure_type
        if failure_type != NO_FAILURE_TYPE:
            failure_counts[failure_type] += 1
            failure_case_ids.setdefault(failure_type, []).append(case.case_id)
            notable_cases.append(_notable_case_row(case))

    failure_count_dict = dict(sorted(failure_counts.items()))
    failure_rates = {
        failure_type: count / classified_case_count
        for failure_type, count in failure_count_dict.items()
        if classified_case_count
    }
    failure_breakdown = tuple(
        {
            "failure_type": failure_type,
            "count": count,
            "rate": failure_rates.get(failure_type),
            "case_ids": list(failure_case_ids.get(failure_type, [])),
        }
        for failure_type, count in failure_count_dict.items()
    )

    return CaseSummary(
        attempted_case_count=attempted,
        classified_case_count=classified_case_count,
        execution_error_count=execution_error_count,
        unclassified_count=unclassified_count,
        successful_model_invocation_count=successful_invocations,
        failure_case_count=sum(failure_count_dict.values()),
        failure_counts=failure_count_dict,
        failure_rates=failure_rates,
        failure_breakdown=failure_breakdown,
        execution_errors=tuple(execution_errors),
        unclassified_cases=tuple(unclassified_cases),
        notable_cases=tuple(notable_cases),
    )


def build_run_report(
    saved_run: SavedRunArtifacts,
    *,
    now: datetime | None = None,
) -> BuiltReport:
    """Build the compact summary and detail artifacts for one saved run."""

    summary = summarize_case_executions(saved_run.case_results)
    report_id = build_run_report_id(saved_run.run.run_id)
    report = Report(
        report_id=report_id,
        run_ids=(saved_run.run.run_id,),
        created_at=_iso_now(now),
        total_cases=summary.attempted_case_count,
        failure_counts=summary.failure_counts,
        failure_rates=summary.failure_rates,
        metrics=summary.metrics_payload(),
        status={"overall": saved_run.status},
        metadata={
            "report_kind": "single_run",
            "source_run_id": saved_run.run.run_id,
            "dataset_id": saved_run.dataset_id,
            "model": saved_run.run.model,
            "adapter_id": saved_run.adapter_id,
            "classifier_id": saved_run.classifier_id,
            "run_status": saved_run.status,
            "run_seed": saved_run.run.metadata.get("run_seed"),
            "detail_artifact": "report_details.json",
        },
    )
    details: dict[str, JsonValue] = {
        "report_id": report_id,
        "report_kind": "single_run",
        "source_run_id": saved_run.run.run_id,
        "dataset_id": saved_run.dataset_id,
        "metrics": summary.metrics_payload(),
        "failure_type_breakdown": list(summary.failure_breakdown),
        "execution_errors": list(summary.execution_errors),
        "unclassified_cases": list(summary.unclassified_cases),
        "notable_cases": list(summary.notable_cases),
    }
    return BuiltReport(report=report, details=details)


def build_run_report_id(run_id: str) -> str:
    """Return the canonical deterministic report id for one saved run."""

    return f"{run_id}_report"


def _iso_now(now: datetime | None) -> str:
    current = now or datetime.now(timezone.utc)
    return current.isoformat().replace("+00:00", "Z")


def _error_row(case: CaseExecution) -> dict[str, JsonValue]:
    if case.error is None:
        return {"case_id": case.case_id}
    return {
        "case_id": case.case_id,
        "stage": case.error.stage,
        "type": case.error.type,
        "message": case.error.message,
    }


def _unclassified_row(case: CaseExecution) -> dict[str, JsonValue]:
    payload: dict[str, JsonValue] = {"case_id": case.case_id}
    if case.error is not None:
        payload["stage"] = case.error.stage
        payload["type"] = case.error.type
        payload["message"] = case.error.message
    return payload


def _notable_case_row(case: CaseExecution) -> dict[str, JsonValue]:
    classification = case.classification
    payload: dict[str, JsonValue] = {"case_id": case.case_id}
    if classification is not None:
        payload["failure_type"] = classification.failure_type
        if classification.confidence is not None:
            payload["confidence"] = classification.confidence
        if classification.explanation is not None:
            payload["explanation"] = classification.explanation
    return payload
