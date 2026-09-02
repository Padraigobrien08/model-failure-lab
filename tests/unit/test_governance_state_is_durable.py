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
how the second one survived the first fix, so this asserts the predicate: **run every
command that records a decision, then check what it wrote.**

Two properties, and the second one is why this file grew past waivers and baselines:

1. nothing a decision-recording command writes may land somewhere `make clean` deletes;
2. every such command must leave a trace under `governance/` -- a record outside the
   artifact it describes.

Property 2 is the one that was missing. The promotion ledger was added to close a bypass
where deleting a pack's own `metadata.integrity` deleted the evidence against it, and the
first version of this file exercised neither `dataset promote` nor `dataset evolve`. So the
ledger's own home went unpinned by the predicate written to pin exactly that, and
`dataset evolve` shipped writing no ledger entry at all.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from model_failure_lab.cli import main
from model_failure_lab.index import QUERY_INDEX_DIRNAME, QUERY_INDEX_FILENAME

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_RUNS = PROJECT_ROOT / "examples" / "regression_demo" / "runs"
REGRESSION_ID = "compare_8ba8496a_to_dda18a0e_66320e7c"
DRAFT_PATH = "datasets/harvested/durability-draft.json"


def _make_clean_targets() -> set[str]:
    """Paths `make clean` removes, read straight from the Makefile so the two cannot drift."""

    makefile = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")
    line = next(
        raw.strip()
        for raw in makefile.splitlines()
        if raw.strip().startswith("rm -rf") and ".failure_lab" in raw
    )
    return set(line.removeprefix("rm -rf").split())


def _snapshot(root: Path) -> dict[str, str]:
    """Every file in the workspace and a digest of its contents.

    Contents, not just names: the second command to touch the ledger *appends* to it, and a
    name-only diff reports that as writing nothing -- which is precisely the "evolve records
    no promotion" bug this file is supposed to catch, hidden by the test meant to catch it.
    """

    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def _changed(before: dict[str, str], after: dict[str, str]) -> set[str]:
    return {name for name, digest in after.items() if before.get(name) != digest}


def _decision_commands(root: Path) -> list[tuple[str, list[str]]]:
    """Every command that records something a human decided, in dependency order.

    A command belongs here when re-running the pipeline would not recreate its output:
    naming a baseline, waiving a gate, and promoting a pack are all choices, not results.
    """

    return [
        ("baselines set", ["baselines", "set", "--name", "release", "--run", "baseline"]),
        ("regressions waive", ["regressions", "waive", REGRESSION_ID, "--reason", "tracked"]),
        (
            "harvest",
            ["harvest", "--comparison", REGRESSION_ID, "--out", DRAFT_PATH],
        ),
        (
            "dataset promote",
            ["dataset", "promote", DRAFT_PATH, "--dataset-id", "durability-promoted"],
        ),
        (
            "dataset evolve",
            ["dataset", "evolve", "durability-family", "--from-comparison", REGRESSION_ID],
        ),
    ]


@pytest.fixture()
def writes_by_command(tmp_path: Path) -> dict[str, set[str]]:
    """Run each decision-recording command and record exactly what it added to the workspace."""

    root = tmp_path / "workspace"
    (root / "runs").mkdir(parents=True)
    for name in ("baseline", "candidate"):
        shutil.copytree(DEMO_RUNS / name, root / "runs" / name)
    assert main(["compare", "baseline", "candidate", "--root", str(root)]) == 0
    assert main(["index", "rebuild", "--root", str(root)]) == 0

    written: dict[str, set[str]] = {}
    before = _snapshot(root)
    for label, argv in _decision_commands(root):
        assert main([*argv, "--root", str(root)]) == 0, f"{label} failed"
        after = _snapshot(root)
        written[label] = _changed(before, after)
        before = after
    return written


def test_the_fixture_still_exercises_every_decision_surface(
    writes_by_command: dict[str, set[str]],
) -> None:
    # A command that stops writing anything reads as "nothing misplaced" below, so say so.
    silent = sorted(label for label, files in writes_by_command.items() if not files)
    assert silent == [], f"these commands wrote nothing, so they prove nothing: {silent}"
    assert set(writes_by_command) == {label for label, _ in _decision_commands(Path("."))}


def test_no_decision_lands_where_make_clean_deletes_it(
    writes_by_command: dict[str, set[str]],
) -> None:
    disposable = _make_clean_targets()
    assert ".failure_lab" in disposable, "the Makefile stopped cleaning .failure_lab"

    # The derived index is *supposed* to be here and several commands refresh it. It earns
    # the exemption by being reproducible, which `test_governance_state_survives_a_clean`
    # checks by deleting it and rebuilding. Naming it from the code, not the string, so an
    # index that moves does not silently widen the exemption to whatever is there instead.
    derived = f"{QUERY_INDEX_DIRNAME}/{QUERY_INDEX_FILENAME}"
    assert derived.split("/")[0] in disposable, derived

    misplaced = {
        label: sorted(
            name
            for name in files
            if name.split("/")[0] in disposable and name != derived
        )
        for label, files in writes_by_command.items()
    }
    misplaced = {label: names for label, names in misplaced.items() if names}
    assert misplaced == {}, (
        f"these commands write decisions where `make clean` deletes them: {misplaced}. "
        f"{QUERY_INDEX_DIRNAME}/ is the derived index -- rebuildable, gitignored, and "
        "removed by `make clean`. A decision a human recorded belongs in governance/."
    )


def test_every_decision_leaves_a_record_under_governance(
    writes_by_command: dict[str, set[str]],
) -> None:
    """A record outside the artifact it describes is the whole guarantee.

    A promoted pack's digest lives inside the pack, so deleting it deletes the evidence.
    The ledger entry is the second file that has to be edited to hide a tampered pack --
    and it only works if every command that writes a curated pack writes one.
    """

    # `harvest` produces a draft: an intermediate, re-derivable from the comparison, and
    # deliberately not a decision until somebody promotes it.
    expected = {label for label in writes_by_command if label != "harvest"}
    unrecorded = sorted(
        label
        for label in expected
        if not any(name.startswith("governance/") for name in writes_by_command[label])
    )
    assert unrecorded == [], (
        f"these commands record a decision with nothing committed outside the artifact: "
        f"{unrecorded}. Curated packs go through "
        "`datasets.integrity.write_curated_dataset`, which stamps, writes, and records in "
        "one call precisely so a writer cannot take two of the three."
    )


def test_both_curated_writers_land_in_one_ledger(
    writes_by_command: dict[str, set[str]], tmp_path: Path
) -> None:
    ledger_writes = {
        label
        for label, files in writes_by_command.items()
        if "governance/promotions.json" in files
    }
    assert ledger_writes == {"dataset promote", "dataset evolve"}, (
        f"the promotion ledger was touched by {sorted(ledger_writes)}. Both commands write "
        "a lifecycle: curated pack, so both must record one."
    )

    root = tmp_path / "workspace"
    ledger = json.loads((root / "governance" / "promotions.json").read_text(encoding="utf-8"))
    recorded = {row["dataset_id"] for row in ledger["promotions"]}
    assert recorded == {"durability-promoted", "durability-family-v1"}, (
        f"the ledger knows about {sorted(recorded)}. Both `dataset promote` and "
        "`dataset evolve` write a lifecycle: curated pack, so both must be recorded -- "
        "0.13.0 wired only the first and left the bypass open on the other."
    )


def test_governance_state_survives_a_clean(
    writes_by_command: dict[str, set[str]], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "workspace"
    shutil.rmtree(root / ".failure_lab")  # i.e. `make clean`
    capsys.readouterr()

    assert main(["baselines", "list", "--root", str(root)]) == 0
    assert "release" in capsys.readouterr().out

    # And the waiver still un-blocks the gate once the derived index is rebuilt.
    assert main(["index", "rebuild", "--root", str(root)]) == 0
    assert main(["regressions", "gate", "--strict-exit", "--root", str(root)]) == 0

    # The ledger still catches a tampered pack, which is the point of it outliving `clean`.
    assert main(["index", "validate", "--root", str(root)]) == 0


def test_governance_state_is_not_gitignored() -> None:
    # A committed home is only committed if git will actually take it.
    for candidate in (
        "governance/baselines.json",
        "governance/waivers.yml",
        "governance/policy.yml",
        "governance/promotions.json",
    ):
        ignored = subprocess.run(
            ["git", "check-ignore", "-q", candidate],
            cwd=PROJECT_ROOT,
            capture_output=True,
        )
        assert ignored.returncode != 0, f"{candidate} is gitignored; it must be committable"


def test_a_pre_migration_workspace_keeps_its_baselines(tmp_path: Path) -> None:
    # Upgrading must not lose a registry that is still under the old path.
    root = tmp_path / "legacy-workspace"
    (root / ".failure_lab").mkdir(parents=True)
    (root / ".failure_lab" / "baseline_registry.json").write_text(
        json.dumps({"baselines": [{"name": "old", "run_id": "run_1"}]}),
        encoding="utf-8",
    )

    from model_failure_lab.governance import list_baselines

    assert [entry.name for entry in list_baselines(root=root)] == ["old"]
