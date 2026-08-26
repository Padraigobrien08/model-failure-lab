"""Governance state has to survive `make clean` and be visible to `git`.

`.failure_lab/` is the derived query index: `docs/artifact-model.md` calls it "rebuildable;
not a source artifact", `.gitignore` excludes it, and `make clean` deletes it. Anything
written there is disposable by construction.

The shared baseline registry was written there. So a registry the tool calls *shared* was
never committed, invisible to every collaborator, and destroyed irrecoverably by the
project's own cleanup target -- it is not derived, so no `index rebuild` brings it back.
`docs/artifact-model.md` had always said it lived in `governance/`.

That was the second instance of the same mistake; the first was `docs/ci-governance.md`
telling operators to put policy and waiver files there. Fixing instances one at a time is
how the second one survived the first fix, so this asserts the predicate: **run the
governance-writing surfaces, then check that nothing they wrote lands somewhere disposable.**
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from model_failure_lab.cli import main

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_RUNS = PROJECT_ROOT / "examples" / "regression_demo" / "runs"
REGRESSION_ID = "compare_8ba8496a_to_dda18a0e_66320e7c"

#: Paths `make clean` removes, read straight from the Makefile so the two cannot drift.
def _make_clean_targets() -> set[str]:
    makefile = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")
    line = next(
        raw.strip()
        for raw in makefile.splitlines()
        if raw.strip().startswith("rm -rf") and ".failure_lab" in raw
    )
    return set(line.removeprefix("rm -rf").split())


def _files(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
    }


def _governance_writes(root: Path) -> set[str]:
    """Files that appeared only once the governance commands ran."""

    return _files(root) - _BEFORE_GOVERNANCE[root]


#: Workspace contents captured before the governance surfaces are exercised.
_BEFORE_GOVERNANCE: dict[Path, set[str]] = {}


@pytest.fixture()
def governed_workspace(tmp_path: Path) -> Path:
    """A workspace after every governance-writing command has run."""

    root = tmp_path / "workspace"
    (root / "runs").mkdir(parents=True)
    for name in ("baseline", "candidate"):
        shutil.copytree(DEMO_RUNS / name, root / "runs" / name)
    assert main(["compare", "baseline", "candidate", "--root", str(root)]) == 0
    assert main(["index", "rebuild", "--root", str(root)]) == 0
    _BEFORE_GOVERNANCE[root] = _files(root)

    assert main(
        ["baselines", "set", "--name", "release", "--run", "baseline", "--root", str(root)]
    ) == 0
    assert main(
        ["regressions", "waive", REGRESSION_ID, "--reason", "tracked", "--root", str(root)]
    ) == 0
    return root


def test_the_governance_surfaces_write_only_under_governance(
    governed_workspace: Path,
) -> None:
    """The predicate, not the instance.

    `runs/` and `reports/` are regenerable and deliberately disposable. Governance state is
    not: a waiver and a baseline are decisions a human made, and no rebuild recreates them.
    So the rule is about *where the governance commands write*, and the check is a diff of
    the workspace before and after running them.
    """

    disposable = _make_clean_targets()
    assert ".failure_lab" in disposable, "the Makefile stopped cleaning .failure_lab"

    written = _governance_writes(governed_workspace)
    assert written, "the fixture stopped exercising the governance surfaces"

    misplaced = sorted(
        name for name in written if name.split("/")[0] in disposable
    )
    assert misplaced == [], (
        f"these governance files land where `make clean` deletes them: {misplaced}. "
        ".failure_lab/ is the derived index -- rebuildable, gitignored, and removed by "
        "`make clean`. A decision a human recorded belongs in governance/."
    )
    assert all(name.startswith("governance/") for name in written), sorted(written)


def test_governance_state_survives_a_clean(
    governed_workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = governed_workspace
    shutil.rmtree(root / ".failure_lab")  # i.e. `make clean`
    capsys.readouterr()

    assert main(["baselines", "list", "--root", str(root)]) == 0
    assert "release" in capsys.readouterr().out

    # And the waiver still un-blocks the gate once the derived index is rebuilt.
    assert main(["index", "rebuild", "--root", str(root)]) == 0
    assert main(["regressions", "gate", "--strict-exit", "--root", str(root)]) == 0


def test_governance_state_is_not_gitignored() -> None:
    # A committed home is only committed if git will actually take it.
    for candidate in ("governance/baselines.json", "governance/waivers.yml",
                      "governance/policy.yml"):
        ignored = subprocess.run(
            ["git", "check-ignore", "-q", candidate],
            cwd=PROJECT_ROOT,
            capture_output=True,
        )
        assert ignored.returncode != 0, f"{candidate} is gitignored; it must be committable"


def test_a_pre_migration_workspace_keeps_its_baselines(tmp_path: Path) -> None:
    # Upgrading must not lose a registry that is still under the old path.
    import json

    root = tmp_path / "legacy-workspace"
    (root / ".failure_lab").mkdir(parents=True)
    (root / ".failure_lab" / "baseline_registry.json").write_text(
        json.dumps({"baselines": [{"name": "old", "run_id": "run_1"}]}),
        encoding="utf-8",
    )

    from model_failure_lab.governance import list_baselines

    assert [entry.name for entry in list_baselines(root=root)] == ["old"]
