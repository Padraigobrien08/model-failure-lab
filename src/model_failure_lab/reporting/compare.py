"""Directional baseline-to-candidate comparison over saved run artifacts."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from model_failure_lab.schemas import JsonValue, Report

from .core import BuiltReport, summarize_case_executions
from .load import SavedRunArtifacts


def build_comparison_report(
    baseline: SavedRunArtifacts,
    candidate: SavedRunArtifacts,
    *,
    now: datetime | None = None,
) -> BuiltReport:
    """Build one deterministic baseline-to-candidate comparison report."""

    report_id = build_comparison_report_id(baseline.run.run_id, candidate.run.run_id)
    created_at = _iso_now(now)
    baseline_full = summarize_case_executions(baseline.case_results)
    candidate_full = summarize_case_executions(candidate.case_results)

    shared_case_ids = tuple(sorted(set(baseline.case_ids) & set(candidate.case_ids)))
    baseline_only_case_ids = tuple(sorted(set(baseline.case_ids) - set(candidate.case_ids)))
    candidate_only_case_ids = tuple(sorted(set(candidate.case_ids) - set(baseline.case_ids)))

    if baseline.dataset_id != candidate.dataset_id:
        report = Report(
            report_id=report_id,
            run_ids=(baseline.run.run_id, candidate.run.run_id),
            created_at=created_at,
            total_cases=0,
            failure_counts={},
            failure_rates={},
            comparison={
                "baseline_run_id": baseline.run.run_id,
                "candidate_run_id": candidate.run.run_id,
                "baseline_dataset_id": baseline.dataset_id,
                "candidate_dataset_id": candidate.dataset_id,
                "compatible": False,
                "reason": "dataset_mismatch",
                "shared_case_count": 0,
                "baseline_only_case_count": len(baseline.case_ids),
                "candidate_only_case_count": len(candidate.case_ids),
            },
            metrics={
                "baseline": baseline_full.metrics_payload(),
                "candidate": candidate_full.metrics_payload(),
                "delta": {},
            },
            status={"overall": "incompatible_dataset"},
            metadata={
                "report_kind": "comparison",
                "comparison_mode": "baseline_to_candidate",
                "detail_artifact": "report_details.json",
            },
        )
        details: dict[str, JsonValue] = {
            "report_id": report_id,
            "report_kind": "comparison",
            "comparison_mode": "baseline_to_candidate",
            "compatibility": dict(report.comparison),
            "baseline_full_metrics": baseline_full.metrics_payload(),
            "candidate_full_metrics": candidate_full.metrics_payload(),
            "baseline_case_ids": list(baseline.case_ids),
            "candidate_case_ids": list(candidate.case_ids),
        }
        return BuiltReport(report=report, details=details)

    baseline_map = baseline.case_map()
    candidate_map = candidate.case_map()
    baseline_shared_cases = tuple(baseline_map[case_id] for case_id in shared_case_ids)
    candidate_shared_cases = tuple(candidate_map[case_id] for case_id in shared_case_ids)
    baseline_shared = summarize_case_executions(baseline_shared_cases)
    candidate_shared = summarize_case_executions(candidate_shared_cases)

    failure_count_deltas = _delta_int_map(
        baseline_shared.failure_counts,
        candidate_shared.failure_counts,
    )
    failure_rate_deltas = _delta_float_map(
        baseline_shared.failure_rates,
        candidate_shared.failure_rates,
    )
    delta_metrics = {
        "failure_rate": _delta_metric(
            baseline_shared.metrics_payload().get("failure_rate"),
            candidate_shared.metrics_payload().get("failure_rate"),
        ),
        "classification_coverage": _delta_metric(
            baseline_shared.metrics_payload().get("classification_coverage"),
            candidate_shared.metrics_payload().get("classification_coverage"),
        ),
        "execution_success_rate": _delta_metric(
            baseline_shared.metrics_payload().get("execution_success_rate"),
            candidate_shared.metrics_payload().get("execution_success_rate"),
        ),
    }
    overall_status = _overall_status(
        failure_rate_delta=delta_metrics["failure_rate"],
        coverage_delta=delta_metrics["classification_coverage"],
    )

    report = Report(
        report_id=report_id,
        run_ids=(baseline.run.run_id, candidate.run.run_id),
        created_at=created_at,
        total_cases=len(shared_case_ids),
        failure_counts=failure_count_deltas,
        failure_rates=failure_rate_deltas,
        comparison={
            "baseline_run_id": baseline.run.run_id,
            "candidate_run_id": candidate.run.run_id,
            "dataset_id": baseline.dataset_id,
            "compatible": True,
            "shared_case_count": len(shared_case_ids),
            "baseline_only_case_count": len(baseline_only_case_ids),
            "candidate_only_case_count": len(candidate_only_case_ids),
            "metrics_computed_on": "shared_cases_only",
        },
        metrics={
            "baseline": baseline_shared.metrics_payload(),
            "candidate": candidate_shared.metrics_payload(),
            "delta": delta_metrics,
        },
        status={"overall": overall_status},
        metadata={
            "report_kind": "comparison",
            "comparison_mode": "baseline_to_candidate",
            "detail_artifact": "report_details.json",
        },
    )
    details: dict[str, JsonValue] = {
        "report_id": report_id,
        "report_kind": "comparison",
        "comparison_mode": "baseline_to_candidate",
        "compatibility": dict(report.comparison),
        "shared_case_ids": list(shared_case_ids),
        "baseline_only_case_ids": list(baseline_only_case_ids),
        "candidate_only_case_ids": list(candidate_only_case_ids),
        "baseline_full_metrics": baseline_full.metrics_payload(),
        "candidate_full_metrics": candidate_full.metrics_payload(),
        "baseline_shared_metrics": baseline_shared.metrics_payload(),
        "candidate_shared_metrics": candidate_shared.metrics_payload(),
        "baseline_failure_breakdown": list(baseline_shared.failure_breakdown),
        "candidate_failure_breakdown": list(candidate_shared.failure_breakdown),
        "failure_count_deltas": dict(failure_count_deltas),
        "failure_rate_deltas": dict(failure_rate_deltas),
        "case_deltas": _case_deltas(shared_case_ids, baseline_map, candidate_map),
    }
    return BuiltReport(report=report, details=details)


def build_comparison_report_id(baseline_run_id: str, candidate_run_id: str) -> str:
    """Return a deterministic directional comparison report id."""

    digest = hashlib.sha256(
        f"{baseline_run_id}:{candidate_run_id}:baseline_to_candidate".encode("utf-8")
    ).hexdigest()[:8]
    return f"compare_{baseline_run_id}_to_{candidate_run_id}_{digest}"


def _delta_metric(baseline_value: object, candidate_value: object) -> float | None:
    if isinstance(baseline_value, (int, float)) and isinstance(candidate_value, (int, float)):
        return float(candidate_value) - float(baseline_value)
    return None


def _delta_int_map(baseline: dict[str, int], candidate: dict[str, int]) -> dict[str, int]:
    keys = sorted(set(baseline) | set(candidate))
    return {key: candidate.get(key, 0) - baseline.get(key, 0) for key in keys}


def _delta_float_map(
    baseline: dict[str, float],
    candidate: dict[str, float],
) -> dict[str, float]:
    keys = sorted(set(baseline) | set(candidate))
    return {key: candidate.get(key, 0.0) - baseline.get(key, 0.0) for key in keys}


def _overall_status(
    *,
    failure_rate_delta: object,
    coverage_delta: object,
) -> str:
    coverage_changed = coverage_delta not in (None, 0, 0.0)
    if isinstance(failure_rate_delta, (int, float)):
        if failure_rate_delta < 0:
            return "improved_with_coverage_change" if coverage_changed else "improved"
        if failure_rate_delta > 0:
            return "regressed_with_coverage_change" if coverage_changed else "regressed"
        if coverage_changed:
            return "unchanged_with_coverage_change"
        return "unchanged"
    return "inconclusive"


def _case_deltas(
    shared_case_ids: tuple[str, ...],
    baseline_map: dict[str, object],
    candidate_map: dict[str, object],
) -> list[dict[str, JsonValue]]:
    rows: list[dict[str, JsonValue]] = []
    for case_id in shared_case_ids:
        baseline_case = baseline_map[case_id]
        candidate_case = candidate_map[case_id]
        baseline_failure_type = _failure_type(baseline_case)
        candidate_failure_type = _failure_type(candidate_case)
        baseline_error_stage = _error_stage(baseline_case)
        candidate_error_stage = _error_stage(candidate_case)
        changed = (
            baseline_failure_type != candidate_failure_type
            or baseline_error_stage != candidate_error_stage
        )
        if not changed:
            continue
        rows.append(
            {
                "case_id": case_id,
                "baseline_failure_type": baseline_failure_type,
                "candidate_failure_type": candidate_failure_type,
                "baseline_error_stage": baseline_error_stage,
                "candidate_error_stage": candidate_error_stage,
                "changed": True,
            }
        )
    return rows


def _failure_type(case: object) -> str | None:
    classification = getattr(case, "classification", None)
    return getattr(classification, "failure_type", None)


def _error_stage(case: object) -> str | None:
    error = getattr(case, "error", None)
    return getattr(error, "stage", None)


def _iso_now(now: datetime | None) -> str:
    current = now or datetime.now(timezone.utc)
    return current.isoformat().replace("+00:00", "Z")
