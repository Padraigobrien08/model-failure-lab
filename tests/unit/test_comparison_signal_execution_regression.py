"""Regression guard: execution-error collapse must not slip the comparison gate.

Execution errors are excluded from the classified-case failure-rate denominator, so a
candidate that errors on cases the baseline completed never appears in
``failure_rate_deltas``. Without folding the execution-success delta into the signal, an
all-error candidate scores as ``neutral``/``improvement`` and passes ``compare --gate``.
"""

from __future__ import annotations

from model_failure_lab.reporting.signals import build_comparison_signal


def test_execution_success_collapse_scores_as_regression() -> None:
    # No classified-failure movement at all; the candidate simply errored everywhere.
    signal = build_comparison_signal(
        failure_rate_deltas={},
        case_deltas=[],
        execution_success_delta=-1.0,
    )
    assert signal["verdict"] == "regression"
    assert signal["regression_score"] == 1.0
    assert signal["improvement_score"] == 0.0
    assert signal["severity"] == 1.0


def test_execution_regression_outweighs_classified_improvement() -> None:
    # Candidate "fixes" classified failures only because it errored those cases out.
    signal = build_comparison_signal(
        failure_rate_deltas={"reasoning": -0.5},
        case_deltas=[],
        execution_success_delta=-1.0,
    )
    assert signal["verdict"] == "regression"
    assert signal["regression_score"] == 1.0
    assert signal["improvement_score"] == 0.5


def test_execution_recovery_counts_as_improvement() -> None:
    # Symmetric direction: the candidate cleared baseline execution errors.
    signal = build_comparison_signal(
        failure_rate_deltas={},
        case_deltas=[],
        execution_success_delta=0.25,
    )
    assert signal["verdict"] == "improvement"
    assert signal["improvement_score"] == 0.25
    assert signal["regression_score"] == 0.0


def test_absent_execution_delta_preserves_legacy_scoring() -> None:
    # Backward-compatible default: comparisons with no execution change are untouched.
    without_delta = build_comparison_signal(
        failure_rate_deltas={"reasoning": 0.25},
        case_deltas=[],
    )
    with_zero_delta = build_comparison_signal(
        failure_rate_deltas={"reasoning": 0.25},
        case_deltas=[],
        execution_success_delta=0.0,
    )
    assert without_delta["verdict"] == "regression"
    assert without_delta["regression_score"] == 0.25
    assert without_delta == with_zero_delta


def _delta(case_id: str, transition: str, base: str, cand: str) -> dict:
    return {
        "case_id": case_id,
        "transition_type": transition,
        "baseline_failure_type": base,
        "candidate_failure_type": cand,
    }


def test_net_improvement_cannot_mask_a_new_failure() -> None:
    """The net-scoring gap: a candidate that fixes more cases than it breaks used to
    earn an "improvement" verdict (and a gate PASS) despite shipping a brand-new
    failure. Any net-new pass->fail case must force a regression verdict."""
    signal = build_comparison_signal(
        # Rate view favors the candidate: format down 0.25, hallucination up 0.125.
        failure_rate_deltas={"format": -0.25, "hallucination": 0.125},
        case_deltas=[
            _delta("f1", "failure_to_no_failure", "format", "no_failure"),
            _delta("f2", "failure_to_no_failure", "format", "no_failure"),
            _delta("h1", "no_failure_to_failure", "no_failure", "hallucination"),
        ],
        shared_case_count=8,
    )
    assert signal["verdict"] == "regression"
    assert signal["severity"] > 0.0


def test_new_failure_masked_by_same_type_fix_still_regresses() -> None:
    """Per-type rate deltas net to zero when one case of a type is fixed while another
    of the same type appears. Severity must still be non-zero (floored at the
    case-regression fraction) so the governance minimum-severity floor cannot wave it
    through."""
    signal = build_comparison_signal(
        failure_rate_deltas={"hallucination": 0.0},  # one cleared, one introduced -> nets to 0
        case_deltas=[
            _delta("h_old", "failure_to_no_failure", "hallucination", "no_failure"),
            _delta("h_new", "no_failure_to_failure", "no_failure", "hallucination"),
        ],
        shared_case_count=5,
    )
    assert signal["verdict"] == "regression"
    assert signal["severity"] == 0.2  # 1 of 5 shared cases regressed


def test_pure_improvement_without_new_failures_stays_improvement() -> None:
    """Guardrail: the fix must not over-flag. A candidate that only fixes cases, with
    no net-new failure, remains an improvement."""
    signal = build_comparison_signal(
        failure_rate_deltas={"reasoning": -0.5},
        case_deltas=[
            _delta("r1", "failure_to_no_failure", "reasoning", "no_failure"),
            _delta("r2", "failure_to_no_failure", "reasoning", "no_failure"),
        ],
        shared_case_count=4,
    )
    assert signal["verdict"] == "improvement"


def test_failure_type_swap_alone_is_not_a_regression() -> None:
    """A case that stays failing but changes type is not a net-new failure, so it does
    not by itself force a regression verdict."""
    signal = build_comparison_signal(
        failure_rate_deltas={"reasoning": -0.25, "instruction_following": 0.25},
        case_deltas=[
            _delta("s1", "failure_type_swap", "reasoning", "instruction_following"),
        ],
        shared_case_count=4,
    )
    assert signal["verdict"] in {"neutral", "improvement"}
    assert signal["verdict"] != "regression"
