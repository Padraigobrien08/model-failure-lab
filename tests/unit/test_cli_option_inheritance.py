"""An option accepted before the subcommand has to mean what it says.

`argparse` parses a subcommand into a fresh namespace and copies every attribute of it onto
the outer one. Any option a subcommand redeclares therefore writes its *default* over the
value the parent already parsed. The operator-visible result was a silent one:

    failure-lab regressions --root /some/workspace gate --strict-exit

evaluated the current directory, printed "No comparisons matched the current filters", and
exited 0 -- a clean CI pass for a workspace it never opened. The CLI's own `--help`
advertises that placement (`usage: failure-lab regressions [-h] [--root ROOT] ...`).

0.13.0 fixed this for `baselines` by hand, with a helper named for the general case and
called from one command. The fix left 56 other collisions: every filter flag on all seven
`regressions` subcommands, `--model` and `--limit` and `--json` among them. So this file
tests the *property* over the assembled tree rather than the two examples somebody noticed:

1. structurally -- no subcommand anywhere may redeclare an ancestor's option with a live
   default, so a subcommand added next year fails here rather than in front of an operator;
2. behaviourally -- each collision is parsed with the option in the outer position and the
   value has to survive;
3. end to end -- the gate that shipped exiting 0 on the wrong workspace exits 2.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pytest

from model_failure_lab.cli import INHERITED_OPTION_DIVERGENCES, build_parser, main

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_RUNS = PROJECT_ROOT / "examples" / "regression_demo" / "runs"


def _options(parser: argparse.ArgumentParser) -> dict[str, argparse.Action]:
    """Real options only -- `-h` is declared by every parser and is already SUPPRESS."""

    return {
        option: action
        for action in parser._actions
        if not isinstance(action, argparse._SubParsersAction | argparse._HelpAction)
        for option in action.option_strings
    }


def _subparsers(
    parser: argparse.ArgumentParser,
) -> list[tuple[str, argparse.ArgumentParser]]:
    return [
        (name, child)
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
        for name, child in action.choices.items()
    ]


def _collisions() -> list[tuple[str, str]]:
    """Every ("<command path>", "<option>") a subcommand shares with one of its ancestors."""

    found: list[tuple[str, str]] = []

    def walk(
        parser: argparse.ArgumentParser,
        path: tuple[str, ...],
        ancestors: tuple[dict[str, argparse.Action], ...],
    ) -> None:
        declared = _options(parser)
        for option in sorted(declared):
            if any(option in scope for scope in ancestors):
                found.append((" ".join(path), option))
        for name, child in _subparsers(parser):
            walk(child, (*path, name), (*ancestors, declared))

    walk(build_parser(), (), ())
    return found


COLLISIONS = _collisions()


def _resolve(path: str) -> tuple[argparse.ArgumentParser, list[str], argparse.ArgumentParser]:
    """The root parser, the command path as argv, and the leaf parser it names."""

    root = build_parser()
    leaf = root
    for name in path.split():
        leaf = dict(_subparsers(leaf))[name]
    return root, path.split(), leaf


def test_no_subcommand_redeclares_an_inherited_option_with_different_behaviour() -> None:
    """The case suppression cannot fix, reported here rather than at the user's terminal.

    Suppressing a child option whose type or default differs from its parent's makes the
    parent's default win -- a behaviour change dressed up as a fix. `build_parser` records
    those instead, because it used to raise, and `main` builds the parser before doing
    anything else: one bad subcommand answered `failure-lab --help` with a traceback.
    """

    build_parser()
    assert INHERITED_OPTION_DIVERGENCES == [], "\n".join(INHERITED_OPTION_DIVERGENCES)


def test_the_scan_still_sees_the_options_this_file_exists_for() -> None:
    # A refactor that stops finding collisions must not read as "all clear".
    assert ("regressions gate", "--root") in COLLISIONS, sorted(COLLISIONS)
    assert ("baselines list", "--root") in COLLISIONS, sorted(COLLISIONS)
    assert len(COLLISIONS) >= 50, len(COLLISIONS)


@pytest.mark.parametrize(("path", "option"), COLLISIONS, ids=lambda v: str(v))
def test_no_subcommand_overwrites_an_inherited_option(path: str, option: str) -> None:
    _, argv, leaf = _resolve(path)
    action = _options(leaf)[option]
    assert action.default is argparse.SUPPRESS, (
        f"`failure-lab {' '.join(argv[:-1])} {option} ... {argv[-1]}` would be discarded: "
        f"{argv[-1]} redeclares {option} with default={action.default!r}, which argparse "
        f"copies over the parent's parsed value. Declare it with default=argparse.SUPPRESS "
        "-- `_suppress_inherited_defaults` does this for the whole tree in `build_parser`."
    )


def _placeholders(parser: argparse.ArgumentParser, skip: str) -> list[str] | None:
    """Argv satisfying the subcommand's own required arguments, or None if we cannot.

    `skip` is the inherited option under test: it is supplied in the outer position
    instead, which is the whole point of the exercise.
    """

    argv: list[str] = []
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return None  # a group, not a leaf; its own children are covered separately
        if isinstance(action, argparse._HelpAction) or skip in action.option_strings:
            continue
        if action.option_strings and not action.required:
            continue
        if not action.option_strings and action.nargs in {"*", "?"}:
            continue
        if action.nargs not in (None, 1):
            return None
        value = str(next(iter(action.choices))) if action.choices else "PLACEHOLDER"
        argv.extend([*action.option_strings[:1], value])
    return argv


@pytest.mark.parametrize(("path", "option"), COLLISIONS, ids=lambda v: str(v))
def test_an_inherited_option_survives_the_subcommand(path: str, option: str) -> None:
    """Parse it for real, with the option where `--help` says it may go."""

    parser, argv, leaf = _resolve(path)
    action = _options(leaf)[option]
    if action.required:
        # The subcommand insists on its own copy, so argparse rejects the outer placement
        # loudly rather than dropping it. Wrong-but-silent is what this file is about.
        pytest.skip(f"{path} marks {option} required, so it cannot be inherited")
    tail = _placeholders(leaf, option)
    if tail is None:
        pytest.skip(f"{path} takes arguments this test cannot synthesise")

    if isinstance(action, argparse._StoreTrueAction):
        given: list[str] = [option]
        expected: object = True
    elif isinstance(action, argparse._StoreFalseAction):
        given, expected = [option], False
    elif action.type is int:
        given, expected = [option, "77"], 77
    elif action.type is Path:
        given, expected = [option, "/tmp/inherited-marker"], Path("/tmp/inherited-marker")
    elif action.choices:
        choice = str(next(iter(c for c in action.choices if c != action.default), None))
        given, expected = [option, choice], choice
    else:
        given, expected = [option, "inherited-marker"], "inherited-marker"

    args = parser.parse_args([*argv[:-1], *given, argv[-1], *tail])
    assert getattr(args, action.dest) == expected, (
        f"`failure-lab {' '.join(argv[:-1])} {' '.join(given)} {argv[-1]}` lost {option}: "
        f"{action.dest}={getattr(args, action.dest)!r}, expected {expected!r}"
    )


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    (root / "runs").mkdir(parents=True)
    for name in ("baseline", "candidate"):
        shutil.copytree(DEMO_RUNS / name, root / "runs" / name)
    assert main(["compare", "baseline", "candidate", "--root", str(root)]) == 0
    assert main(["index", "rebuild", "--root", str(root)]) == 0
    return root


def test_the_gate_blocks_from_either_position(
    workspace: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The regression this file is named for, at the exit code CI reads.

    Run from somewhere else entirely, so a `--root` that goes missing cannot accidentally
    still be looking at the workspace.
    """

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    after = main(["regressions", "gate", "--strict-exit", "--root", str(workspace)])
    before = main(["regressions", "--root", str(workspace), "gate", "--strict-exit"])
    assert (before, after) == (2, 2), (
        f"the gate disagrees with itself about where --root may go: "
        f"before the subcommand -> {before}, after -> {after}. "
        "Exit 0 here is a green build for a workspace the gate never read."
    )
