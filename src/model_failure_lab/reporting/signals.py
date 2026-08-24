"""Deterministic comparison signal scoring over persisted comparison deltas."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from model_failure_lab.schemas import JsonValue

SIGNAL_DRIVER_LIMIT = 4

# Transitions that represent a genuine, net-new regression on a shared case:
# a case that passed now fails, or a case that ran now errors. These are the
# ground truth of "a candidate broke something", independent of how many other
# cases improved. The verdict must never be able to hide one of these behind an
# offsetting improvement elsewhere. `failure_type_swap` (still failing, different
# type) and `error_stage_changed` (already erroring) are deliberately excluded --
# they are not net-new failures -- matching `_case_transition_counts` in compare.py.
REGRESSION_TRANSITION_TYPES = frozenset({"no_failure_to_failure", "new_error"})


def _count_transitions(
    case_deltas: Sequence[Mapping[str, JsonValue]],
    transition_types: frozenset[str],
) -> int:
    return sum(
        1
        for row in case_deltas
        if isinstance(row.get("transition_type"), str)
        and row["transition_type"] in transition_types
    )


def build_comparison_signal(
    *,
    failure_rate_deltas: Mapping[str, float],
    case_deltas: Sequence[Mapping[str, JsonValue]],
    shared_case_count: int | None = None,
    execution_success_delta: float | None = None,
) -> dict[str, JsonValue]:
    regression_score = sum(max(float(delta), 0.0) for delta in failure_rate_deltas.values())
    improvement_score = sum(
        abs(float(delta)) for delta in failure_rate_deltas.values() if float(delta) < 0.0
    )

    # Execution errors are excluded from the classified-case failure-rate denominator,
    # so a candidate that errors on cases the baseline completed never appears in
    # failure_rate_deltas -- it silently shrinks the denominator instead. Fold the
    # execution-success regression straight into the score so a candidate cannot pass
    # the gate simply by failing to run. execution_success_delta is candidate minus
    # baseline: negative means the candidate errored more (a regression).
    if execution_success_delta is not None:
        execution_regression = -float(execution_success_delta)
        if execution_regression > 0.0:
            regression_score += execution_regression
        elif execution_regression < 0.0:
            improvement_score += -execution_regression

    # Per-failure-type rate deltas net to zero when one case is fixed and another
    # regresses within the same type (e.g. one hallucination cleared while a new one
    # appears), hiding a real pass->fail regression from the rate-based score. Floor
    # regression_score at the fraction of shared cases that went pass->fail so such a
    # regression can never round to a zero severity the governance minimum-severity
    # floor would wave through. New errors are excluded here because they are already
    # folded into regression_score via execution_success_delta above -- counting them
    # again would double-represent them.
    # Denominator is the shared-case count (cases present in both runs); case_deltas
    # only carries CHANGED cases, so it cannot be used as the total. Fall back to the
    # delta count only when the caller does not supply the shared total.
    denominator = shared_case_count if shared_case_count else len(case_deltas)
    new_failure_cases = _count_transitions(case_deltas, frozenset({"no_failure_to_failure"}))
    if denominator > 0 and new_failure_cases > 0:
        regression_score = max(regression_score, new_failure_cases / denominator)

    # The verdict, however, must flip on ANY net-new failing or erroring case, since
    # a new error can be masked by offsetting rate improvements just as easily.
    case_regressions = _count_transitions(case_deltas, REGRESSION_TRANSITION_TYPES)

    regression_score = round(regression_score, 6)
    improvement_score = round(improvement_score, 6)
    net_score = round(improvement_score - regression_score, 6)

    # Any net-new failing/erroring case is a regression the gate must catch, even
    # when the candidate improved more cases elsewhere. Without this, a candidate
    # could ship a brand-new failure and still earn an "improvement" verdict (and a
    # PASS) simply by fixing enough unrelated cases -- the net-scoring gap.
    if case_regressions > 0 or regression_score > improvement_score:
        verdict = "regression"
        severity = regression_score
    elif improvement_score > regression_score:
        verdict = "improvement"
        severity = improvement_score
    else:
        verdict = "neutral"
        # regression_score == improvement_score in this branch; either is the churn level.
        severity = regression_score

    top_drivers = _top_signal_drivers(
        failure_rate_deltas=failure_rate_deltas,
        case_deltas=case_deltas,
    )
    return {
        "verdict": verdict,
        "regression_score": regression_score,
        "improvement_score": improvement_score,
        "net_score": net_score,
        "severity": severity,
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
