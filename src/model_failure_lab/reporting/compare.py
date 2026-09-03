"""Directional baseline-to-candidate comparison over saved run artifacts."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone

from model_failure_lab.schemas import NO_FAILURE_TYPE, JsonValue, Report

from .core import BuiltReport, summarize_case_executions
from .load import SavedRunArtifacts
from .signals import build_comparison_signal, build_incompatible_signal

TRANSITION_LABELS = {
    "failure_to_no_failure": "failure -> no_failure",
    "no_failure_to_failure": "no_failure -> failure",
    "failure_type_swap": "failure type swap",
    "error_cleared": "error cleared",
    "new_error": "new error",
    "error_stage_changed": "error stage changed",
}
TRANSITION_ORDER = (
    "failure_to_no_failure",
    "no_failure_to_failure",
    "failure_type_swap",
    "error_cleared",
    "new_error",
    "error_stage_changed",
)


def _case_is_failure(case) -> bool:
    """True when a case was a classified failure (not a pass and not an error).

    Used on both runs. It was named and documented for the baseline while only the baseline
    called it, which is how the scope rule built on it ended up covering one direction.
    """

    if case.output is None or case.classification is None:
        return False
    return case.classification.failure_type != NO_FAILURE_TYPE


def _prompt_content_fingerprint(case) -> str:
    """Deterministic digest of the load-bearing prompt content for one case.

    Covers the prompt text and its expectations -- the two things a regression
    comparison depends on -- but not cosmetic fields (tags, id), so a reordering
    does not spuriously flag a mismatch.
    """

    snapshot = case.prompt.to_payload()
    material = {
        "prompt": snapshot.get("prompt"),
        "expectations": snapshot.get("expectations"),
    }
    canonical = json.dumps(material, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _build_incompatible_comparison(
    baseline: SavedRunArtifacts,
    candidate: SavedRunArtifacts,
    *,
    report_id: str,
    created_at: str,
    reason: str,
    status_overall: str,
    baseline_full,
    candidate_full,
    shared_case_count: int,
    baseline_only_case_count: int,
    candidate_only_case_count: int,
) -> BuiltReport:
    """Assemble one incompatible comparison report (no verdict math is meaningful)."""

    signal = build_incompatible_signal(reason=reason)
    comparison = {
        "baseline_run_id": baseline.run.run_id,
        "candidate_run_id": candidate.run.run_id,
        "baseline_dataset_id": baseline.dataset_id,
        "candidate_dataset_id": candidate.dataset_id,
        "compatible": False,
        "reason": reason,
        "shared_case_count": shared_case_count,
        "baseline_only_case_count": baseline_only_case_count,
        "candidate_only_case_count": candidate_only_case_count,
        "signal": signal,
    }
    report = Report(
        report_id=report_id,
        run_ids=(baseline.run.run_id, candidate.run.run_id),
        created_at=created_at,
        total_cases=0,
        failure_counts={},
        failure_rates={},
        comparison=comparison,
        metrics={
            "baseline": baseline_full.metrics_payload(),
            "candidate": candidate_full.metrics_payload(),
            "delta": {},
        },
        status={"overall": status_overall},
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
        "compatibility": dict(comparison),
        "baseline_full_metrics": baseline_full.metrics_payload(),
        "candidate_full_metrics": candidate_full.metrics_payload(),
        "baseline_case_ids": list(baseline.case_ids),
        "candidate_case_ids": list(candidate.case_ids),
        "signal": signal,
        "case_transition_counts": {},
        "case_transition_summary": [],
        "case_deltas": [],
    }
    return BuiltReport(report=report, details=details)


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
        # Different dataset ids: nothing is comparable.
        return _build_incompatible_comparison(
            baseline,
            candidate,
            report_id=report_id,
            created_at=created_at,
            reason="dataset_mismatch",
            status_overall="incompatible_dataset",
            baseline_full=baseline_full,
            candidate_full=candidate_full,
            shared_case_count=0,
            baseline_only_case_count=len(baseline.case_ids),
            candidate_only_case_count=len(candidate.case_ids),
        )

    if not shared_case_ids:
        # Same dataset id but no case id is shared -- e.g. the candidate renamed every
        # case. Verdict math over an empty shared set would score "neutral" and pass the
        # gate, so treat a zero-overlap comparison as incompatible instead.
        return _build_incompatible_comparison(
            baseline,
            candidate,
            report_id=report_id,
            created_at=created_at,
            reason="no_shared_cases",
            status_overall="incompatible_cases",
            baseline_full=baseline_full,
            candidate_full=candidate_full,
            shared_case_count=0,
            baseline_only_case_count=len(baseline_only_case_ids),
            candidate_only_case_count=len(candidate_only_case_ids),
        )

    baseline_map = baseline.case_map()
    candidate_map = candidate.case_map()

    content_mismatch_ids = tuple(
        case_id
        for case_id in shared_case_ids
        if _prompt_content_fingerprint(baseline_map[case_id])
        != _prompt_content_fingerprint(candidate_map[case_id])
    )
    if content_mismatch_ids:
        # Same case id, different prompt/expectation content: the dataset was mutated
        # under a stable id, so the runs are not comparable on those cases. Fail closed
        # rather than silently comparing across changed prompts.
        return _build_incompatible_comparison(
            baseline,
            candidate,
            report_id=report_id,
            created_at=created_at,
            reason="dataset_content_mismatch",
            status_overall="incompatible_cases",
            baseline_full=baseline_full,
            candidate_full=candidate_full,
            shared_case_count=len(shared_case_ids),
            baseline_only_case_count=len(baseline_only_case_ids),
            candidate_only_case_count=len(candidate_only_case_ids),
        )

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

    case_deltas = _case_deltas(shared_case_ids, baseline_map, candidate_map)
    execution_success_delta = delta_metrics["execution_success_rate"]
    signal = build_comparison_signal(
        failure_rate_deltas=failure_rate_deltas,
        case_deltas=case_deltas,
        shared_case_count=len(shared_case_ids),
        execution_success_delta=(
            float(execution_success_delta)
            if isinstance(execution_success_delta, (int, float))
            else None
        ),
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
            "signal": signal,
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
    dropped_baseline_failure_case_ids = tuple(
        case_id
        for case_id in baseline_only_case_ids
        if _case_is_failure(baseline_map[case_id])
    )
    # The mirror of `baseline_only_case_ids`, narrowed to the ones that matter.
    #
    # Every metric here is computed on the shared set, so a case in only one run is invisible
    # to all of them. `0.15.0` blocked the gate on cases missing from the *candidate* and said
    # nothing about the other direction, so shrinking the *baseline* instead had the identical
    # effect: the four regressed cases became candidate-only, the shared set was four clean
    # cases, and the gate passed.
    #
    # The two directions warrant different rules, and the difference is what is known:
    #
    #   * a case the candidate did not run has an *unknown* candidate outcome. It might have
    #     regressed. Every one of them is a hole.
    #   * a case the baseline did not run has a *known* candidate outcome. If it passed, the
    #     candidate is fine on it and adding coverage should not need a waiver. If it failed,
    #     it is a known-bad result that no comparison examined.
    #
    # So: all of the first, and the failing subset of the second. The rule is not "block on
    # failures" -- a failure present in both runs is compared and found unchanged, and passes.
    # It is "block on a case whose candidate outcome is unknown or bad and was never compared".
    unexamined_candidate_failure_case_ids = tuple(
        case_id
        for case_id in candidate_only_case_ids
        if _case_is_failure(candidate_map[case_id])
    )
    details: dict[str, JsonValue] = {
        "report_id": report_id,
        "report_kind": "comparison",
        "comparison_mode": "baseline_to_candidate",
        "compatibility": dict(report.comparison),
        "signal": signal,
        "shared_case_ids": list(shared_case_ids),
        "baseline_only_case_ids": list(baseline_only_case_ids),
        "candidate_only_case_ids": list(candidate_only_case_ids),
        "dropped_baseline_failure_case_ids": list(dropped_baseline_failure_case_ids),
        "unexamined_candidate_failure_case_ids": list(unexamined_candidate_failure_case_ids),
        "baseline_full_metrics": baseline_full.metrics_payload(),
        "candidate_full_metrics": candidate_full.metrics_payload(),
        "baseline_shared_metrics": baseline_shared.metrics_payload(),
        "candidate_shared_metrics": candidate_shared.metrics_payload(),
        "baseline_failure_breakdown": list(baseline_shared.failure_breakdown),
        "candidate_failure_breakdown": list(candidate_shared.failure_breakdown),
        "failure_count_deltas": dict(failure_count_deltas),
        "failure_rate_deltas": dict(failure_rate_deltas),
        "case_transition_counts": _case_transition_counts(case_deltas),
        "case_transition_summary": _case_transition_summary(case_deltas),
        "case_deltas": case_deltas,
    }
    return BuiltReport(report=report, details=details)


def build_comparison_report_id(baseline_run_id: str, candidate_run_id: str) -> str:
    """Return a deterministic directional comparison report id."""

    baseline_digest = hashlib.sha256(baseline_run_id.encode("utf-8")).hexdigest()[:8]
    candidate_digest = hashlib.sha256(candidate_run_id.encode("utf-8")).hexdigest()[:8]
    pair_digest = hashlib.sha256(
        f"{baseline_run_id}:{candidate_run_id}:baseline_to_candidate".encode("utf-8")
    ).hexdigest()[:8]
    return f"compare_{baseline_digest}_to_{candidate_digest}_{pair_digest}"


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
        transition_type = _transition_type(
            baseline_failure_type=baseline_failure_type,
            candidate_failure_type=candidate_failure_type,
            baseline_error_stage=baseline_error_stage,
            candidate_error_stage=candidate_error_stage,
        )
        rows.append(
            {
                "case_id": case_id,
                "prompt_id": baseline_case.prompt.id,
                "prompt": _prompt_text(baseline_case),
                "tags": _tags(baseline_case),
                "transition_type": transition_type,
                "transition_label": TRANSITION_LABELS[transition_type],
                "baseline_failure_type": baseline_failure_type,
                "candidate_failure_type": candidate_failure_type,
                "baseline_expectation_verdict": _expectation_verdict(baseline_case),
                "candidate_expectation_verdict": _expectation_verdict(candidate_case),
                "baseline_error_stage": baseline_error_stage,
                "candidate_error_stage": candidate_error_stage,
                "baseline_explanation": _explanation(baseline_case),
                "candidate_explanation": _explanation(candidate_case),
                "changed": True,
            }
        )
    return rows


def _case_transition_counts(case_deltas: list[dict[str, JsonValue]]) -> dict[str, int]:
    transition_counts = Counter(
        str(row["transition_type"])
        for row in case_deltas
        if isinstance(row.get("transition_type"), str)
    )
    return {
        "improvements": transition_counts["failure_to_no_failure"],
        "regressions": transition_counts["no_failure_to_failure"],
        "failure_type_swaps": transition_counts["failure_type_swap"],
        "error_changes": (
            transition_counts["error_cleared"]
            + transition_counts["new_error"]
            + transition_counts["error_stage_changed"]
        ),
    }


def _case_transition_summary(
    case_deltas: list[dict[str, JsonValue]],
) -> list[dict[str, JsonValue]]:
    rows_by_transition: dict[str, list[dict[str, JsonValue]]] = {}
    for row in case_deltas:
        transition_type = row.get("transition_type")
        if isinstance(transition_type, str):
            rows_by_transition.setdefault(transition_type, []).append(row)

    summary: list[dict[str, JsonValue]] = []
    for transition_type in TRANSITION_ORDER:
        rows = rows_by_transition.get(transition_type, [])
        if not rows:
            continue
        summary.append(
            {
                "transition_type": transition_type,
                "label": TRANSITION_LABELS[transition_type],
                "count": len(rows),
                "case_ids": [str(row["case_id"]) for row in rows],
            }
        )
    return summary


def _transition_type(
    *,
    baseline_failure_type: str | None,
    candidate_failure_type: str | None,
    baseline_error_stage: str | None,
    candidate_error_stage: str | None,
) -> str:
    if baseline_error_stage != candidate_error_stage:
        if baseline_error_stage is not None and candidate_error_stage is None:
            return "error_cleared"
        if baseline_error_stage is None and candidate_error_stage is not None:
            return "new_error"
        return "error_stage_changed"

    if (
        baseline_failure_type is not None
        and baseline_failure_type != NO_FAILURE_TYPE
        and candidate_failure_type == NO_FAILURE_TYPE
    ):
        return "failure_to_no_failure"
    if (
        baseline_failure_type == NO_FAILURE_TYPE
        and candidate_failure_type is not None
        and candidate_failure_type != NO_FAILURE_TYPE
    ):
        return "no_failure_to_failure"
    return "failure_type_swap"


def _failure_type(case: object) -> str | None:
    classification = getattr(case, "classification", None)
    return getattr(classification, "failure_type", None)


def _explanation(case: object) -> str | None:
    classification = getattr(case, "classification", None)
    return getattr(classification, "explanation", None)


def _expectation_verdict(case: object) -> str | None:
    expectation = getattr(case, "expectation", None)
    return getattr(expectation, "expectation_verdict", None)


def _prompt_text(case: object) -> str | None:
    prompt = getattr(case, "prompt", None)
    return getattr(prompt, "prompt", None)


def _tags(case: object) -> list[str]:
    prompt = getattr(case, "prompt", None)
    tags = getattr(prompt, "tags", ())
    return [str(tag) for tag in tags]


def _error_stage(case: object) -> str | None:
    error = getattr(case, "error", None)
    return getattr(error, "stage", None)


def _iso_now(now: datetime | None) -> str:
    current = now or datetime.now(timezone.utc)
    return current.isoformat().replace("+00:00", "Z")
