"""One workspace, one question, three answers that must match.

`evaluate_gate_conditions` unified the *conditions* every gate surface blocks on. It did not
unify everything a surface does with that decision, and the gap reopened one layer up: when
`regressions waive` made writing a waiver a command, `regressions gate` and the console's
gate endpoint honoured it and `compare --gate` did not -- and `compare --gate` is the surface
`action.yml` wraps and the README tells you to put in CI. Following the console's own printed
remedy turned the console green and left the build red.

`test_gate_surface_agreement.py` covers the conditions. This covers the *answer*: for each
scenario, all three surfaces are asked and their verdicts compared to each other, not to a
hardcoded expectation. A surface that grows a new input nobody else reads fails here.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from model_failure_lab.cli import main
from model_failure_lab.governance import evaluate_regression_gate

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_RUNS = PROJECT_ROOT / "examples" / "regression_demo" / "runs"
REGRESSION_ID = "compare_8ba8496a_to_dda18a0e_66320e7c"


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    (root / "runs").mkdir(parents=True)
    for name in ("baseline", "candidate"):
        shutil.copytree(DEMO_RUNS / name, root / "runs" / name)
    assert main(["compare", "baseline", "candidate", "--root", str(root)]) == 0
    assert main(["index", "rebuild", "--root", str(root)]) == 0
    return root


def _compare_gate_blocks(root: Path) -> bool:
    """Surface 1: `compare --gate`, which `action.yml` wraps."""

    return main(["compare", "baseline", "candidate", "--gate", "--root", str(root)]) != 0


def _regressions_gate_blocks(root: Path) -> bool:
    """Surface 2: the workspace-wide governance gate."""

    return main(["regressions", "gate", "--strict-exit", "--root", str(root)]) != 0


def _console_gate_blocks(root: Path) -> bool:
    """Surface 3: the payload the console's `gate.json` endpoint serves, verbatim."""

    result = evaluate_regression_gate(root=root)
    row = next(row for row in result.rows if row.comparison_id == REGRESSION_ID)
    return row.blocked


def _all_three(root: Path) -> dict[str, bool]:
    return {
        "compare --gate": _compare_gate_blocks(root),
        "regressions gate": _regressions_gate_blocks(root),
        "console gate.json": _console_gate_blocks(root),
    }


def test_an_unwaived_regression_blocks_every_surface(workspace: Path) -> None:
    answers = _all_three(workspace)
    assert set(answers.values()) == {True}, answers


def test_an_active_waiver_unblocks_every_surface(workspace: Path) -> None:
    assert (
        main(
            [
                "regressions",
                "waive",
                REGRESSION_ID,
                "--reason",
                "tracked in JIRA-123",
                "--owner",
                "padraig",
                "--root",
                str(workspace),
            ]
        )
        == 0
    )

    answers = _all_three(workspace)
    # The whole point: not "compare --gate passes", but "nobody disagrees".
    assert set(answers.values()) == {False}, (
        f"the gate surfaces disagree about a waived comparison: {answers}. A waiver the "
        "console honours and CI ignores is a green screen over a red build."
    )


def test_removing_the_waiver_re_blocks_every_surface(workspace: Path) -> None:
    main(["regressions", "waive", REGRESSION_ID, "--reason", "r", "--root", str(workspace)])
    main(["regressions", "waive", REGRESSION_ID, "--remove", "--root", str(workspace)])

    answers = _all_three(workspace)
    assert set(answers.values()) == {True}, answers


def test_an_expired_waiver_blocks_every_surface(workspace: Path) -> None:
    # Written directly: `regressions waive` refuses a past --expires-at at write time, and
    # the case that matters is a waiver that has since lapsed on disk.
    import yaml

    governance = workspace / "governance"
    governance.mkdir(parents=True, exist_ok=True)
    (governance / "waivers.yml").write_text(
        yaml.safe_dump(
            {
                "waivers": [
                    {
                        "comparison_id": REGRESSION_ID,
                        "reason": "lapsed",
                        "expires_at": "2020-01-01T00:00:00Z",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    answers = _all_three(workspace)
    assert set(answers.values()) == {True}, answers


def test_compare_gate_names_the_expired_waiver_rather_than_ignoring_it(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import yaml

    governance = workspace / "governance"
    governance.mkdir(parents=True, exist_ok=True)
    (governance / "waivers.yml").write_text(
        yaml.safe_dump(
            {
                "waivers": [
                    {
                        "comparison_id": REGRESSION_ID,
                        "reason": "lapsed",
                        "expires_at": "2020-01-01T00:00:00Z",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    assert main(["compare", "baseline", "candidate", "--gate", "--root", str(workspace)]) == 1
    output = capsys.readouterr().out
    # Behaving as though the file were empty leaves the operator staring at a waiver that
    # visibly exists and visibly does nothing.
    assert "waiver expired" in output


def test_an_ownerless_waiver_never_renders_the_word_null(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # `--owner` is optional. Interpolating it unguarded put "waived by null" on the
    # comparison detail; the CLI gate line must not do the same.
    main(["regressions", "waive", REGRESSION_ID, "--reason", "no owner", "--root", str(workspace)])
    capsys.readouterr()

    assert main(["compare", "baseline", "candidate", "--gate", "--root", str(workspace)]) == 0
    output = capsys.readouterr().out
    assert "Gate: PASS (waived: no owner)" in output
    assert "None" not in output.split("Gate:")[1]


def test_an_active_waiver_says_so_and_names_what_it_waived(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main(
        [
            "regressions",
            "waive",
            REGRESSION_ID,
            "--reason",
            "tracked in JIRA-123",
            "--owner",
            "padraig",
            "--root",
            str(workspace),
        ]
    )
    capsys.readouterr()

    assert main(["compare", "baseline", "candidate", "--gate", "--root", str(workspace)]) == 0
    output = capsys.readouterr().out
    assert "Gate: PASS (waived by padraig: tracked in JIRA-123)" in output
    # A PASS that hides what it suppressed is how a waiver becomes permanent by accident.
    assert "would block: signal verdict: regression" in output
