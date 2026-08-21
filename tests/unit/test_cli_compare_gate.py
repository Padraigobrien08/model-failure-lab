"""CI gate contract for `failure-lab compare --gate` and `--format markdown`.

The gate exit code is a public contract consumed by the bundled GitHub Action
(`action.yml`): 0 = no regression, 1 = regression or incompatible runs.
"""

from __future__ import annotations

from pathlib import Path

from model_failure_lab.cli import main

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_RUNS = PROJECT_ROOT / "examples" / "regression_demo" / "runs"
BASELINE = str(DEMO_RUNS / "baseline")
CANDIDATE = str(DEMO_RUNS / "candidate")


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


def test_markdown_format_rejects_score_alert_explain(tmp_path, capsys) -> None:
    for flag in ("--score", "--alert", "--explain"):
        exit_code = main(
            ["compare", BASELINE, CANDIDATE, "--format", "markdown", flag, "--root", str(tmp_path)]
        )
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "`--format markdown` cannot be combined" in captured.err
