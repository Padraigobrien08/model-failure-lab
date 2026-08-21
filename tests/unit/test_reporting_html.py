"""Tests for the `--html` single-file export on `report` and `compare`."""

from __future__ import annotations

from pathlib import Path

import pytest

from model_failure_lab.cli import main

EXAMPLES_ROOT = Path(__file__).resolve().parents[2] / "examples" / "regression_demo" / "runs"
BASELINE_RUN = EXAMPLES_ROOT / "baseline"
CANDIDATE_RUN = EXAMPLES_ROOT / "candidate"


def _run_id_from_output(capsys: pytest.CaptureFixture[str]) -> str:
    output = capsys.readouterr().out
    for line in output.splitlines():
        if line.startswith("Run ID: "):
            return line.removeprefix("Run ID: ").strip()
    raise AssertionError(f"no run id in demo output:\n{output}")


def test_report_html_export(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    assert main(["demo", "--root", str(root)]) == 0
    run_id = _run_id_from_output(capsys)

    html_path = tmp_path / "out" / "report.html"
    assert (
        main(["report", "--run", run_id, "--root", str(root), "--html", str(html_path)]) == 0
    )
    output = capsys.readouterr().out
    assert f"HTML report: {html_path}" in output

    html = html_path.read_text(encoding="utf-8")
    assert html.startswith("<!DOCTYPE html>")
    assert "Failure Lab Report" in html
    assert "<script" not in html
    assert "http://" not in html and "https://" not in html
    # Per-case table content from the deterministic demo dataset.
    assert "<code>case-001</code>" in html
    assert "<code>case-004</code>" in html
    assert "PASS" in html
    assert "FAIL" in html
    assert "hallucination" in html
    assert "Failure rate" in html

    # Deterministic across renders.
    second_path = tmp_path / "out" / "report2.html"
    assert (
        main(["report", "--run", run_id, "--root", str(root), "--html", str(second_path)]) == 0
    )
    capsys.readouterr()
    assert second_path.read_text(encoding="utf-8") == html


def test_compare_html_export(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    html_path = tmp_path / "compare.html"
    exit_code = main(
        [
            "compare",
            str(BASELINE_RUN),
            str(CANDIDATE_RUN),
            "--root",
            str(root),
            "--html",
            str(html_path),
        ]
    )
    assert exit_code == 0
    output = capsys.readouterr().out
    assert f"HTML report: {html_path}" in output

    html = html_path.read_text(encoding="utf-8")
    assert html.startswith("<!DOCTYPE html>")
    assert "Failure Lab Compare" in html
    assert "<script" not in html
    # Verdict, delta, and signal scores.
    assert "regression" in html
    assert "Failure rate delta" in html
    assert "+50.0%" in html
    assert "Severity" in html
    # Top drivers with evidence case ids.
    assert "instruction_following" in html
    assert "<code>citation-latency</code>" in html
    # Per-case transitions with baseline vs candidate classification.
    assert "Case transitions" in html
    assert "regressed" in html
    assert "<code>factual-apollo</code>" in html
    assert "no_failure" in html

    # Deterministic across renders.
    second_path = tmp_path / "compare2.html"
    assert (
        main(
            [
                "compare",
                str(BASELINE_RUN),
                str(CANDIDATE_RUN),
                "--root",
                str(root),
                "--html",
                str(second_path),
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert second_path.read_text(encoding="utf-8") == html


def test_compare_html_composes_with_gate_and_format(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    html_path = tmp_path / "gated.html"
    exit_code = main(
        [
            "compare",
            str(BASELINE_RUN),
            str(CANDIDATE_RUN),
            "--root",
            str(root),
            "--gate",
            "--format",
            "markdown",
            "--html",
            str(html_path),
        ]
    )
    assert exit_code == 1  # candidate regresses, gate fails
    output = capsys.readouterr().out
    assert "Gate: FAIL" in output
    assert f"HTML report: {html_path}" in output
    assert html_path.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")
