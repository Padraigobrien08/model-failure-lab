"""Deterministic comparison signal scoring over persisted comparison deltas."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from model_failure_lab.schemas import JsonValue

SIGNAL_DRIVER_LIMIT = 4


def build_comparison_signal(
    *,
    failure_rate_deltas: Mapping[str, float],
    case_deltas: Sequence[Mapping[str, JsonValue]],
) -> dict[str, JsonValue]:
    regression_score = round(
        sum(max(float(delta), 0.0) for delta in failure_rate_deltas.values()),
        6,
    )
    improvement_score = round(
        sum(abs(float(delta)) for delta in failure_rate_deltas.values() if float(delta) < 0.0),
        6,
    )
    net_score = round(improvement_score - regression_score, 6)
    if regression_score > improvement_score:
        verdict = "regression"
    elif improvement_score > regression_score:
        verdict = "improvement"
    else:
        verdict = "neutral"

    top_drivers = _top_signal_drivers(
        failure_rate_deltas=failure_rate_deltas,
        case_deltas=case_deltas,
    )
    return {
        "verdict": verdict,
        "regression_score": regression_score,
        "improvement_score": improvement_score,
        "net_score": net_score,
        "severity": max(regression_score, improvement_score),
        "top_drivers": top_drivers,
    }


def build_incompatible_signal(*, reason: str) -> dict[str, JsonValue]:
    return {
        "verdict": "incompatible",
        "reason": reason,
        "regression_score": 0.0,
        "improvement_score": 0.0,
        "net_score": 0.0,
        "severity": 0.0,
        "top_drivers": [],
    }


def _top_signal_drivers(
    *,
    failure_rate_deltas: Mapping[str, float],
    case_deltas: Sequence[Mapping[str, JsonValue]],
) -> list[dict[str, JsonValue]]:
    ranked_rows = sorted(
        (
            (failure_type, float(delta))
            for failure_type, delta in failure_rate_deltas.items()
            if abs(float(delta)) > 0.0
        ),
        key=lambda item: (
            -abs(item[1]),
            0 if item[1] > 0 else 1,
            item[0],
        ),
    )

    drivers: list[dict[str, JsonValue]] = []
    for failure_type, delta in ranked_rows[:SIGNAL_DRIVER_LIMIT]:
        case_ids = _driver_case_ids(
            failure_type=failure_type,
            delta=delta,
            case_deltas=case_deltas,
        )
        drivers.append(
            {
                "failure_type": failure_type,
                "delta": round(delta, 6),
                "direction": "regression" if delta > 0 else "improvement",
                "case_ids": case_ids,
            }
        )
    return drivers


def _driver_case_ids(
    *,
    failure_type: str,
    delta: float,
    case_deltas: Sequence[Mapping[str, JsonValue]],
) -> list[str]:
    matched: list[str] = []
    for row in case_deltas:
        case_id = row.get("case_id")
        baseline_failure_type = row.get("baseline_failure_type")
        candidate_failure_type = row.get("candidate_failure_type")
        if not isinstance(case_id, str):
            continue
        if delta > 0:
            if candidate_failure_type == failure_type and baseline_failure_type != failure_type:
                matched.append(case_id)
        elif baseline_failure_type == failure_type and candidate_failure_type != failure_type:
            matched.append(case_id)
    return sorted(set(matched))
