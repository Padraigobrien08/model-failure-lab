"""Every command the console prints has to parse against the real CLI.

The console's empty states and remedy lines exist to tell an operator what to run next.
DESIGN.md requires them: "an empty state naming the path it read plus the CLI command to fix
it", and "errors state what failed and which file, then what to run". A command that does not
run fails that requirement in the one place the reader is most stuck.

Several shipped broken, and fixing them one at a time did not work:

* `harvest --report <comparison>` omits the required `--out`. The `0.12.0` CHANGELOG says
  this was fixed. It was not -- the entry was written and the string never touched. That is
  the failure mode this file exists to make impossible: a claim about a remedy, verified by
  reading the claim rather than the remedy.
* `baselines set <name>` passes a positional where the CLI wants `--name`.
* `dataset promote <draft>` and `dataset evolve <family>` omit their required arguments.

So the check is mechanical: extract every `failure-lab …` literal from the console source and
hand it to the real `argparse` tree, with placeholders substituted. A command argparse
rejects -- unknown flag, missing required argument, bad choice -- fails here.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import re
from pathlib import Path

import pytest

from model_failure_lab.cli import build_parser

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONSOLE_DIRS = (
    PROJECT_ROOT / "frontend" / "src" / "app" / "routes",
    PROJECT_ROOT / "frontend" / "src" / "components" / "console",
    PROJECT_ROOT / "frontend" / "src" / "components" / "layout",
)

#: One argv token as the console writes it: a word/flag/path, a `<placeholder>`, or a JSX
#: interpolation. Deliberately narrow so the scan stops at the markup that follows a string
#: -- `</div>` and `<table` are not tokens, `<run-id>` is.
_PIECE = r"(?:--\$?\{[^}]*\}|<[A-Za-z0-9_.\-]*>|\$?\{[^}]*\}|[A-Za-z0-9_./=:\-]+)"
#: A token is one or more pieces with no space between them, so a path with a placeholder
#: inside it (`datasets/harvested/<draft-id>.json`) stays one argv token.
TOKEN = re.compile(f"(?:{_PIECE})+")

#: A flag whose *name* is chosen at runtime (`--${scope.kind}`) cannot be checked against
#: argparse without enumerating the runtime values, so those commands are reported rather
#: than validated. The list is asserted to stay short: it is an escape hatch, not a habit.
DYNAMIC_FLAG = re.compile(r"--\$?\{")


def _console_sources() -> list[tuple[str, str]]:
    files: list[tuple[str, str]] = []
    for directory in CONSOLE_DIRS:
        for path in sorted(directory.glob("*.ts*")):
            if "__tests__" in path.parts:
                continue
            files.append((str(path.relative_to(PROJECT_ROOT)), path.read_text(encoding="utf-8")))
    return files


def _scan(text: str) -> list[str]:
    """Every `failure-lab …` command in one source file."""

    # JSX line-wraps long strings, and writes angle brackets as entities.
    flat = re.sub(r"\n\s+", " ", text).replace("&lt;", "<").replace("&gt;", ">")
    commands: list[str] = []
    for match in re.finditer(r"failure-lab\s", flat):
        tokens: list[str] = []
        position = match.end()
        while True:
            token = TOKEN.match(flat, position)
            if token is None:
                break
            word = token.group(0)
            # `or`/`and` join two commands in one sentence; the next `failure-lab` match
            # picks up the second one.
            if word in {"or", "and", "then"}:
                break
            tokens.append(word)
            position = token.end()
            spaces = re.match(r"[ ]+", flat[position:])
            if spaces is None:
                break
            position += spaces.end()
        if tokens:
            commands.append(" ".join(tokens))
    return commands


def _extract_commands() -> list[tuple[str, str]]:
    return [(name, command) for name, text in _console_sources() for command in _scan(text)]


def _argv(command: str) -> list[str]:
    return [
        "PLACEHOLDER" if token.startswith(("<", "{", "${")) else token
        for token in command.split()
    ]


CHECKABLE = [
    (source, command)
    for source, command in _extract_commands()
    if not DYNAMIC_FLAG.search(command)
]
DYNAMIC = [
    (source, command) for source, command in _extract_commands() if DYNAMIC_FLAG.search(command)
]


def test_the_extractor_finds_the_console_remedies() -> None:
    commands = {command for _, command in _extract_commands()}
    assert len(commands) >= 10, sorted(commands)
    joined = " | ".join(sorted(commands))
    # The shapes that shipped broken, so a regression in the extractor cannot hide them.
    for expected in ("harvest", "baselines set", "dataset promote", "dataset evolve"):
        assert expected in joined, f"{expected!r} not extracted from the console: {joined}"


def test_runtime_chosen_flags_stay_the_exception() -> None:
    # A command whose flag name is interpolated cannot be validated here. Keeping the list
    # short is what stops "make it dynamic" becoming the way around this test.
    assert len(DYNAMIC) <= 2, [command for _, command in DYNAMIC]


@pytest.mark.parametrize(("source", "command"), CHECKABLE, ids=lambda value: str(value))
def test_every_printed_command_parses(source: str, command: str) -> None:
    parser = build_parser()
    argv = _argv(command)
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stderr(buffer):
            parser.parse_args(argv)
    except SystemExit as exit_error:  # argparse's failure path
        detail = buffer.getvalue().strip().splitlines()
        pytest.fail(
            f"{source} prints a command that does not parse:\n"
            f"    failure-lab {command}\n"
            f"  argv: {argv}\n"
            f"  argparse (exit {exit_error.code}): {detail[-1] if detail else '?'}"
        )
    except argparse.ArgumentError as error:  # pragma: no cover - defensive
        pytest.fail(f"{source}: failure-lab {command} -> {error}")
