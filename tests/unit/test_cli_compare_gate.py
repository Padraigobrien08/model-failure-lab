"""CI gate contract for `failure-lab compare --gate` and `--format markdown`.

The gate exit code is a public contract consumed by the bundled GitHub Action
(`action.yml`): 0 = no regression, 1 = regression or incompatible runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from model_failure_lab.cli import _evaluate_compare_gate, main

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_RUNS = PROJECT_ROOT / "examples" / "regression_demo" / "runs"
BASELINE = str(DEMO_RUNS / "baseline")
CANDIDATE = str(DEMO_RUNS / "candidate")


@dataclass
class _FakeReport:
    """Minimal stand-in exposing the two attributes the gate reads."""

    comparison: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)


def _report_with(*, verdict: str, delta: dict) -> _FakeReport:
    return _FakeReport(
        comparison={"compatible": True, "signal": {"verdict": verdict}},
        metrics={"delta": delta},
    )


def test_gate_fails_when_candidate_drops_baseline_failing_cases() -> None:
    # Neutral verdict, no execution/coverage drop, but the candidate omitted a baseline
    # case that was failing -- hiding a regression by removing the broken case.
    exit_code, message = _evaluate_compare_gate(
        _report_with(verdict="neutral", delta={}),
        {"dropped_baseline_failure_case_ids": ["case-broken-1", "case-broken-2"]},
    )
    assert exit_code == 1
    assert "dropped 2 baseline failing case(s)" in message


def test_gate_passes_when_only_passing_baseline_cases_are_dropped() -> None:
    exit_code, message = _evaluate_compare_gate(
        _report_with(verdict="neutral", delta={}),
        {"dropped_baseline_failure_case_ids": []},
    )
    assert exit_code == 0
    assert "Gate: PASS" in message


def test_gate_fails_on_regression(tmp_path, capsys) -> None:
    exit_code = main(["compare", BASELINE, CANDIDATE, "--gate", "--root", str(tmp_path)])
    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Gate: FAIL (signal verdict: regression)" in output


def test_gate_passes_when_candidate_does_not_regress(tmp_path, capsys) -> None:
    exit_code = main(["compare", BASELINE, BASELINE, "--gate", "--root", str(tmp_path)])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Gate: PASS" in output


def test_compare_without_gate_keeps_zero_exit_code(tmp_path, capsys) -> None:
    exit_code = main(["compare", BASELINE, CANDIDATE, "--root", str(tmp_path)])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Gate:" not in output


def test_markdown_format_renders_verdict_table_and_drivers(tmp_path, capsys) -> None:
    exit_code = main(
        ["compare", BASELINE, CANDIDATE, "--gate", "--format", "markdown", "--root", str(tmp_path)]
    )
    output = capsys.readouterr().out
    assert exit_code == 1
    assert "## Failure Lab Compare" in output
    assert "**Verdict: 🔴 regression**" in output
    assert "| Failure rate delta | +50.0% |" in output
    assert "### Top drivers" in output
    assert "| instruction_following | +25.0% | regression |" in output
    assert "**Gate: FAIL (signal verdict: regression)**" in output


def test_markdown_format_is_deterministic(tmp_path, capsys) -> None:
    main(["compare", BASELINE, CANDIDATE, "--format", "markdown", "--root", str(tmp_path / "a")])
    first = capsys.readouterr().out
    main(["compare", BASELINE, CANDIDATE, "--format", "markdown", "--root", str(tmp_path / "b")])
    second = capsys.readouterr().out
    assert first == second


def test_gate_defense_in_depth_fails_on_execution_collapse_without_regression_verdict() -> None:
    # Belt for the signal fix: even if the verdict is not "regression", the gate must
    # fail closed when the candidate's execution success dropped.
    exit_code, message = _evaluate_compare_gate(
        _report_with(verdict="neutral", delta={"execution_success_rate": -1.0}),
        {},
    )
    assert exit_code == 1
    assert "execution success regressed" in message


def test_gate_defense_in_depth_fails_on_coverage_collapse() -> None:
    exit_code, message = _evaluate_compare_gate(
        _report_with(verdict="improvement", delta={"classification_coverage": -0.25}),
        {},
    )
    assert exit_code == 1
    assert "classification coverage regressed" in message


def test_gate_defense_in_depth_passes_when_execution_and_coverage_hold() -> None:
    exit_code, message = _evaluate_compare_gate(
        _report_with(
            verdict="neutral",
            delta={"execution_success_rate": 0.0, "classification_coverage": 0.0},
        ),
        {},
    )
    assert exit_code == 0
    assert "Gate: PASS" in message


def test_markdown_format_rejects_score_alert_explain(tmp_path, capsys) -> None:
    for flag in ("--score", "--alert", "--explain"):
        exit_code = main(
            ["compare", BASELINE, CANDIDATE, "--format", "markdown", flag, "--root", str(tmp_path)]
        )
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "`--format markdown` cannot be combined" in captured.err
