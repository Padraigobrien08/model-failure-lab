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
