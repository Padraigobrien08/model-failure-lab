"""Aggregate report builders over saved Phase 46 run artifacts."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from model_failure_lab.runner import CaseExecution
from model_failure_lab.schemas import NO_FAILURE_TYPE, JsonValue, Report

from .load import SavedRunArtifacts

MAX_NOTABLE_CASES = 6
MISMATCH_VERDICTS = ("unexpected_failure", "missed_expected")
VERDICT_PRIORITY = {
    "unexpected_failure": 0,
    "missed_expected": 1,
    "matched_expected": 2,
    "no_failure_as_expected": 3,
    None: 4,
}


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
    expectation_verdict_counts: dict[str, int]
    expectation_verdict_breakdown: tuple[dict[str, JsonValue], ...]
    expectation_mismatches: dict[str, tuple[dict[str, JsonValue], ...]]
    tag_breakdown: tuple[dict[str, JsonValue], ...]
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
    notable_candidate_rows: list[dict[str, JsonValue]] = []
    failure_case_ids: dict[str, list[str]] = {}
    failure_counts: Counter[str] = Counter()
    expectation_verdict_counts: Counter[str] = Counter()
    expectation_verdict_case_ids: dict[str, list[str]] = {}
    expectation_mismatches: dict[str, list[dict[str, JsonValue]]] = {
        verdict: [] for verdict in MISMATCH_VERDICTS
    }
    tag_summary_map: dict[str, dict[str, Any]] = {}
    classified_case_count = 0
    execution_error_count = 0
    unclassified_count = 0

    for case in case_results:
        verdict = case.expectation.expectation_verdict
        if verdict is not None:
            expectation_verdict_counts[verdict] += 1
            expectation_verdict_case_ids.setdefault(verdict, []).append(case.case_id)

        for tag in case.prompt.tags:
            bucket = tag_summary_map.setdefault(
                tag,
                {
                    "attempted_case_count": 0,
                    "classified_case_count": 0,
                    "failure_case_count": 0,
                    "expectation_verdict_counts": Counter(),
                },
            )
            bucket["attempted_case_count"] += 1
            if verdict is not None:
                bucket["expectation_verdict_counts"][verdict] += 1

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
        for tag in case.prompt.tags:
            tag_summary_map[tag]["classified_case_count"] += 1

        failure_type = case.classification.failure_type
        if failure_type != NO_FAILURE_TYPE:
            failure_counts[failure_type] += 1
            failure_case_ids.setdefault(failure_type, []).append(case.case_id)
            for tag in case.prompt.tags:
                tag_summary_map[tag]["failure_case_count"] += 1

        if verdict in MISMATCH_VERDICTS:
            expectation_mismatches[verdict].append(_expectation_case_row(case))

        notable_row = _notable_case_row(case)
        if notable_row is not None:
            notable_candidate_rows.append(notable_row)

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
    expectation_verdict_count_dict = dict(sorted(expectation_verdict_counts.items()))
    expectation_verdict_breakdown = tuple(
        {
            "expectation_verdict": expectation_verdict,
            "count": count,
            "case_ids": list(expectation_verdict_case_ids.get(expectation_verdict, [])),
        }
        for expectation_verdict, count in expectation_verdict_count_dict.items()
    )
    tag_breakdown = tuple(
        _tag_breakdown_row(tag, tag_summary)
        for tag, tag_summary in sorted(
            tag_summary_map.items(),
            key=lambda item: (
                -_tag_failure_rate(item[1]),
                -int(item[1]["failure_case_count"]),
                item[0],
            ),
        )
    )
    notable_cases = tuple(
        row
        for _, row in sorted(
            ((_notable_sort_key(row), row) for row in notable_candidate_rows),
            key=lambda item: item[0],
        )[:MAX_NOTABLE_CASES]
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
        expectation_verdict_counts=expectation_verdict_count_dict,
        expectation_verdict_breakdown=expectation_verdict_breakdown,
        expectation_mismatches={
            verdict: tuple(rows)
            for verdict, rows in expectation_mismatches.items()
            if rows
        },
        tag_breakdown=tag_breakdown,
        execution_errors=tuple(execution_errors),
        unclassified_cases=tuple(unclassified_cases),
        notable_cases=notable_cases,
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
        "expectation_verdict_counts": dict(summary.expectation_verdict_counts),
        "expectation_verdict_breakdown": list(summary.expectation_verdict_breakdown),
        "expectation_mismatches": {
            verdict: list(rows) for verdict, rows in summary.expectation_mismatches.items()
        },
        "tag_breakdown": list(summary.tag_breakdown),
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


def _notable_case_row(case: CaseExecution) -> dict[str, JsonValue] | None:
    classification = case.classification
    if classification is None:
        return None
    verdict = case.expectation.expectation_verdict
    if classification.failure_type == NO_FAILURE_TYPE and verdict not in MISMATCH_VERDICTS:
        return None
    payload = _expectation_case_row(case)
    payload["failure_type"] = classification.failure_type
    if classification.failure_subtype is not None:
        payload["failure_subtype"] = classification.failure_subtype
    if classification.confidence is not None:
        payload["confidence"] = classification.confidence
    if classification.explanation is not None:
        payload["explanation"] = classification.explanation
    return payload


def _expectation_case_row(case: CaseExecution) -> dict[str, JsonValue]:
    payload: dict[str, JsonValue] = {
        "case_id": case.case_id,
        "prompt_id": case.prompt.id,
        "prompt": case.prompt.prompt,
        "tags": list(case.prompt.tags),
        "expectation_verdict": case.expectation.expectation_verdict,
    }
    if case.output is not None:
        payload["output_text"] = case.output.text
    if case.expectation.expected_failure is not None:
        payload["expected_failure"] = case.expectation.expected_failure.to_payload()
    if case.expectation.observed_failure is not None:
        payload["observed_failure"] = case.expectation.observed_failure.to_payload()
    classification = case.classification
    if classification is not None and classification.explanation is not None:
        payload["explanation"] = classification.explanation
    return payload


def _tag_breakdown_row(tag: str, tag_summary: dict[str, Any]) -> dict[str, JsonValue]:
    classified_case_count = int(tag_summary["classified_case_count"])
    failure_case_count = int(tag_summary["failure_case_count"])
    return {
        "tag": tag,
        "attempted_case_count": int(tag_summary["attempted_case_count"]),
        "classified_case_count": classified_case_count,
        "failure_case_count": failure_case_count,
        "failure_rate": (
            failure_case_count / classified_case_count if classified_case_count else None
        ),
        "expectation_verdict_counts": dict(
            sorted(tag_summary["expectation_verdict_counts"].items())
        ),
    }


def _tag_failure_rate(tag_summary: dict[str, Any]) -> float:
    classified_case_count = int(tag_summary["classified_case_count"])
    if not classified_case_count:
        return -1.0
    return float(tag_summary["failure_case_count"]) / classified_case_count


def _notable_sort_key(row: dict[str, JsonValue]) -> tuple[float, float, int, str]:
    verdict = row.get("expectation_verdict")
    confidence = row.get("confidence")
    return (
        float(VERDICT_PRIORITY.get(verdict, VERDICT_PRIORITY[None])),
        -(float(confidence) if isinstance(confidence, (int, float)) else -1.0),
        0 if row.get("failure_type") != NO_FAILURE_TYPE else 1,
        str(row["case_id"]),
    )
