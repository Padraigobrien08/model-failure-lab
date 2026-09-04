"""Run what `action.yml` runs, against a workspace that broke the promise.

Every other test here checks a command. This checks a *composition*: the sequence a user
actually gets when they follow the README's CI section, against the attack that sequence is
supposed to stop.

That distinction is the whole reason this file exists. The immutability machinery -- content
digests, a promotion ledger kept outside the pack, an error naming the recorded digest and
the remedy -- was correct, tested, and three releases deep. It lived in `index validate`,
and `action.yml` ran `failure-lab compare --gate` and nothing else. So an operator could
delete the promoted regression pack, re-run both sides, and ship green: the comparison had
nothing to notice, and the command that would notice was one the product never told anyone
to run. Every part worked. The edge between them did not exist, and no test of a part could
have found that.

So the assertion is deliberately indirect: read the commands out of `action.yml` itself,
execute them in order, and require the sequence to fail. Hardcoding the sequence here would
re-create the same gap one level up -- the test would keep passing while the shipped file
changed underneath it.
"""

from __future__ import annotations

import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_RUNS = PROJECT_ROOT / "examples" / "regression_demo" / "runs"
COMPARISON_ID = "compare_8ba8496a_to_dda18a0e_66320e7c"
DATASET_ID = "permanent-regressions"

#: A `failure-lab …` invocation in one of the action's shell steps.
COMMAND = re.compile(r"(?<![-\w])failure-lab\s+([^\n]*)")


def _action_commands() -> list[list[str]]:
    """Every `failure-lab` invocation `action.yml` makes, in order, as argv.

    Backslash continuations are joined first. Without that the `compare` line parses as
    `compare baseline candidate` and silently loses `--root`, so the command runs against
    the wrong directory and this file grades the action on a workspace it never opened --
    a false pass, in the test written to catch a false pass.
    """

    action = yaml.safe_load((PROJECT_ROOT / "action.yml").read_text(encoding="utf-8"))
    argv: list[list[str]] = []
    for step in action["runs"]["steps"]:
        script = re.sub(r"\\\n\s*", " ", step.get("run", ""))
        for match in COMMAND.finditer(script):
            words = shlex.split(match.group(1))
            # Everything from the first redirect on belongs to the shell, not to argv.
            redirect = next((i for i, w in enumerate(words) if w.startswith(">")), len(words))
            words = words[:redirect]
            # The action passes inputs through the environment and carries the optional
            # gate flag in `$GATE_FLAG`; `gate` defaults to true, so resolve it that way.
            resolved = ["--gate" if w == "$GATE_FLAG" else w for w in words]
            argv.append([_ENV.get(w, w) for w in resolved])
    return argv


#: The environment `action.yml` sets, as this test resolves it. `gate` and
#: `validate_artifacts` both default to `"true"`, which is the configuration a user gets.
_ENV = {"$ROOT": "ROOT", "$BASELINE": "baseline", "$CANDIDATE": "candidate"}


def _run(argv: list[str], root: Path) -> int:
    assert "ROOT" in argv, (
        f"`failure-lab {' '.join(argv)}` carries no --root, so it would run against the "
        "repository instead of the workspace under test. The extractor lost an argument."
    )
    concrete = [str(root) if word == "ROOT" else word for word in argv]
    result = subprocess.run(
        [sys.executable, "-m", "model_failure_lab", *concrete],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(PROJECT_ROOT / "src")},
    )
    return result.returncode


@pytest.fixture()
def workspace_whose_permanent_test_was_deleted(tmp_path: Path) -> Path:
    """The documented loop, followed, and then undone."""

    root = tmp_path / "ws"
    (root / "runs").mkdir(parents=True)
    for name in ("baseline", "candidate"):
        shutil.copytree(DEMO_RUNS / name, root / "runs" / name)

    from model_failure_lab.cli import main

    assert main(["compare", "baseline", "candidate", "--root", str(root)]) == 0
    assert main(["index", "rebuild", "--root", str(root)]) == 0
    draft = "datasets/harvested/draft.json"
    assert main(["harvest", "--comparison", COMPARISON_ID, "--out", draft,
                 "--root", str(root)]) == 0
    assert main(["dataset", "promote", draft, "--dataset-id", DATASET_ID,
                 "--root", str(root)]) == 0

    # Now retire the permanent test and re-run: delete the pack, and drop its cases from
    # both runs so the comparison has nothing left to object to.
    (root / "datasets" / f"{DATASET_ID}.json").unlink()
    promoted = json.loads(
        (root / "governance" / "promotions.json").read_text(encoding="utf-8")
    )
    assert any(row["dataset_id"] == DATASET_ID for row in promoted["promotions"])

    baseline_clean = {
        case["case_id"]
        for case in json.loads(
            (root / "runs" / "baseline" / "results.json").read_text(encoding="utf-8")
        )["cases"]
        if (case.get("classification") or {}).get("failure_type") == "no_failure"
    }
    for run in ("baseline", "candidate"):
        path = root / "runs" / run / "results.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        broke = {
            case["case_id"]
            for case in json.loads(
                (root / "runs" / "candidate" / "results.json").read_text(encoding="utf-8")
            )["cases"]
            if case["case_id"] in baseline_clean
            and (case.get("classification") or {}).get("failure_type") != "no_failure"
        }
        payload["cases"] = [c for c in payload["cases"] if c["case_id"] not in broke]
        payload["total_cases"] = len(payload["cases"])
        path.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")
    return root


def test_the_action_actually_invokes_more_than_one_command() -> None:
    commands = _action_commands()
    assert len(commands) >= 2, commands
    verbs = {argv[0] for argv in commands}
    assert "compare" in verbs
    assert "validate" in {argv[1] for argv in commands if argv[0] == "index"}, (
        "action.yml no longer runs `index validate`. Comparing two runs cannot notice a "
        "promoted test that was deleted and stopped being run; this is the check that can."
    )


def test_following_the_action_fails_when_the_permanent_test_was_deleted(
    workspace_whose_permanent_test_was_deleted: Path,
) -> None:
    root = workspace_whose_permanent_test_was_deleted
    codes = {
        " ".join(argv): _run(argv, root) for argv in _action_commands()
    }
    assert any(code != 0 for code in codes.values()), (
        "every command the shipped action runs succeeded against a workspace whose promoted "
        f"regression pack was deleted and stopped being run: {codes}. The README sells this "
        "as a permanent test; a green build here means it is not one."
    )
