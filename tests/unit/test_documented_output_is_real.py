"""Output shown in the README must be output the tool actually prints.

The README labelled a block "Real output" for a single `failure-lab compare` invocation. It
was not: seven lines were missing, the order differed, the driver rows were re-padded for
alignment the tool does not produce, and the `Top drivers:` section does not exist in
`compare` output at all -- it comes from the separate `--summary` surface. For a tool whose
product is trustworthy verdicts, the first concrete evidence a reader sees has to be literal.

`examples/regression_demo/expected_compare.txt` had the same problem in reverse: it was
committed as the demo's expected output and nothing checked it.

Both are now pinned to what the CLI prints.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from model_failure_lab.cli import main

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO = PROJECT_ROOT / "examples" / "regression_demo"
README = PROJECT_ROOT / "README.md"
EXPECTED_COMPARE = DEMO / "expected_compare.txt"


def _run_compare(tmp_path: Path, capsys: pytest.CaptureFixture[str], *extra: str) -> list[str]:
    exit_code = main(
        [
            "compare",
            str(DEMO / "runs" / "baseline"),
            str(DEMO / "runs" / "candidate"),
            *extra,
            "--root",
            str(tmp_path),
        ]
    )
    assert exit_code == 0
    # `Artifacts:` prints absolute paths. Rewrite them relative to the workspace so the
    # comparison is portable while still covering the lines themselves.
    output = capsys.readouterr().out.strip().replace(f"{tmp_path}/", "")
    return output.splitlines()


def _without_artifact_paths(lines: list[str]) -> list[str]:
    """Drop the `Artifacts:` path lines, which are machine-specific.

    Matched narrowly on the trailing `.json` so the driver rows -- which also start with
    "- " -- are preserved. Dropping those too would make this test vacuous.
    """

    return [
        line for line in lines if not (line.startswith("- ") and line.rstrip().endswith(".json"))
    ]


def test_expected_compare_fixture_matches_the_cli(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    actual = _run_compare(tmp_path, capsys, "--summary")
    expected = EXPECTED_COMPARE.read_text(encoding="utf-8").strip().splitlines()

    assert actual == expected, (
        "examples/regression_demo/expected_compare.txt no longer matches "
        "`failure-lab compare ... --summary`."
    )


def _readme_code_blocks(language: str) -> list[str]:
    pattern = re.compile(rf"^```{language}\n(.*?)^```", re.MULTILINE | re.DOTALL)
    return [match.group(1) for match in pattern.finditer(README.read_text(encoding="utf-8"))]


def test_readme_shows_the_real_compare_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    actual = _without_artifact_paths(_run_compare(tmp_path, capsys, "--summary"))

    documented = [
        block
        for block in _readme_code_blocks("text")
        if "Failure Lab Compare" in block and "Top drivers:" in block
    ]
    assert len(documented) == 1, "expected exactly one compare-output block in the README"
    shown = _without_artifact_paths(documented[0].strip().splitlines())

    assert shown == actual, (
        "the README's compare output block no longer matches what the CLI prints. Paste the "
        "real output rather than editing the block by hand -- a doctored sample is the one "
        "thing a regression-detection tool cannot ship."
    )


def test_readme_does_not_promise_a_pypi_install_that_predates_the_docs() -> None:
    # `pip install model-failure-lab` currently resolves to 0.1.0, which has no `init`, no
    # `compare --gate`, no `--html` and no openai-compat adapter. Until the published version
    # catches up, the README must not present it as the way in.
    readme = README.read_text(encoding="utf-8")
    intro = readme.split("## The workflow", 1)[0]
    assert "git clone" in intro, "the intro must show the install path that actually works"
    assert "Install from source for now" in intro, (
        "the intro must state that the PyPI release lags the source tree; drop this "
        "assertion in the same commit that publishes a matching release"
    )
