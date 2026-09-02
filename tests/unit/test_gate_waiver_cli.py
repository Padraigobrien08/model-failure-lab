"""The gate has to be exitable from inside the tool.

`evaluate_gate_conditions` blocks on fail-closed conditions as well as regressions -- runs
that are not comparable, a coverage drop, a candidate that deleted its failing cases -- and
the gate evaluates every recent comparison in the workspace. So one accidental
cross-dataset `compare` leaves a permanently red gate, and there was no command to delete,
prune or dismiss a saved comparison. The only way out was to hand-author
`governance/waivers.yml` from a description in the docs, or to `rm -rf` a report directory
outside the tool.

A waiver is the right primitive: it records *why* a comparison stopped blocking, which
deleting the artifact does not. `regressions waive` makes writing one a command.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from model_failure_lab.cli import main
from model_failure_lab.governance import list_waivers

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_RUNS = PROJECT_ROOT / "examples" / "regression_demo" / "runs"
REGRESSION_ID = "compare_8ba8496a_to_dda18a0e_66320e7c"


@pytest.fixture()
def blocked_workspace(tmp_path: Path) -> Path:
    """A workspace whose gate blocks on the bundled demo regression."""

    root = tmp_path / "workspace"
    (root / "runs").mkdir(parents=True)
    for name in ("baseline", "candidate"):
        shutil.copytree(DEMO_RUNS / name, root / "runs" / name)
    assert main(["compare", "baseline", "candidate", "--root", str(root)]) == 0
    assert main(["index", "rebuild", "--root", str(root)]) == 0
    assert main(["regressions", "gate", "--strict-exit", "--root", str(root)]) == 2
    return root


def test_waiving_unblocks_the_gate_and_removing_re_blocks_it(blocked_workspace: Path) -> None:
    root = blocked_workspace

    assert (
        main(
            [
                "regressions",
                "waive",
                REGRESSION_ID,
                "--reason",
                "fix tracked in JIRA-123",
                "--owner",
                "padraig",
                "--root",
                str(root),
            ]
        )
        == 0
    )
    assert main(["regressions", "gate", "--strict-exit", "--root", str(root)]) == 0

    assert main(["regressions", "waive", REGRESSION_ID, "--remove", "--root", str(root)]) == 0
    assert main(["regressions", "gate", "--strict-exit", "--root", str(root)]) == 2


def test_it_writes_the_file_the_engine_actually_discovers(blocked_workspace: Path) -> None:
    root = blocked_workspace
    # `docs/ci-governance.md` used to point at `.failure_lab/waivers.json` -- the derived
    # index directory, which `.gitignore` excludes -- while discovery looked in
    # `governance/`. A waiver written where nothing reads it is worse than none.
    main(["regressions", "waive", REGRESSION_ID, "--reason", "r", "--root", str(root)])

    written = root / "governance" / "waivers.yml"
    assert written.is_file()
    payload = yaml.safe_load(written.read_text(encoding="utf-8"))
    assert payload["waivers"] == [
        {"comparison_id": REGRESSION_ID, "reason": "r"},
    ]


def test_a_waiver_must_say_why(
    blocked_workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["regressions", "waive", REGRESSION_ID, "--root", str(blocked_workspace)]) != 0
    assert "why the comparison stops blocking" in capsys.readouterr().err
    assert not (blocked_workspace / "governance" / "waivers.yml").exists()


def test_an_already_expired_waiver_is_refused_at_write_time(
    blocked_workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Writing one that is inactive the moment it lands looks like it worked and changes
    # nothing; the gate stays red and the operator has no idea why.
    assert (
        main(
            [
                "regressions",
                "waive",
                REGRESSION_ID,
                "--reason",
                "r",
                "--expires-at",
                "2020-01-01T00:00:00Z",
                "--root",
                str(blocked_workspace),
            ]
        )
        != 0
    )
    assert "not a future UTC timestamp" in capsys.readouterr().err
    assert not (blocked_workspace / "governance" / "waivers.yml").exists()


def test_the_file_stays_sorted_so_two_waivers_do_not_reorder_the_diff(
    blocked_workspace: Path,
) -> None:
    root = blocked_workspace
    for comparison_id in ("cmp_zebra", "cmp_alpha", REGRESSION_ID):
        main(["regressions", "waive", comparison_id, "--reason", "r", "--root", str(root)])

    payload = yaml.safe_load((root / "governance" / "waivers.yml").read_text(encoding="utf-8"))
    ids = [row["comparison_id"] for row in payload["waivers"]]
    assert ids == sorted(ids)
    assert [waiver.comparison_id for waiver in list_waivers(root=root)] == sorted(ids)


def test_rewriting_one_waiver_updates_it_in_place(blocked_workspace: Path) -> None:
    root = blocked_workspace
    main(["regressions", "waive", REGRESSION_ID, "--reason", "first", "--root", str(root)])
    main(["regressions", "waive", REGRESSION_ID, "--reason", "second", "--root", str(root)])

    waivers = list_waivers(root=root)
    assert len(waivers) == 1
    assert waivers[0].reason == "second"


def test_removing_an_absent_waiver_is_not_an_error(blocked_workspace: Path) -> None:
    assert (
        main(["regressions", "waive", "cmp_never_seen", "--remove", "--root",
              str(blocked_workspace)])
        == 0
    )
