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

So the check is mechanical: extract every `failure-lab …` literal and hand it to the real
`argparse` tree, with placeholders substituted. A command argparse rejects -- unknown flag,
missing required argument, bad choice -- fails here.

The scan reads the **whole repository**, not the console. It was console-only for one
release, and two live instances of the same defect sat just outside it:

* `examples/regression_demo/run.sh` ended the README's two-minute demo -- the last line a
  first-time reader sees -- with `failure-lab dataset promote ...`, a literal ellipsis.
* `harvest/review.py` answered a promotion conflict with
  `failure-lab dataset evolve <id>`, which is missing the required `--from-comparison`.

A predicate scoped to the directory where the bug was found is the same mistake as a fix
scoped to the caller where the bug was found.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import io
import re
import shlex
import subprocess
from pathlib import Path

import pytest

from model_failure_lab.cli import build_parser

PROJECT_ROOT = Path(__file__).resolve().parents[2]

#: Anything a person could copy: source that prints, scripts they run, docs they read.
SCANNED_SUFFIXES = (".ts", ".tsx", ".py", ".sh", ".md")
#: Excluded, with reasons. Tests assert on broken commands on purpose; the CHANGELOG is a
#: record of what commands used to be; `docs/legacy.md` documents the unsupported surface.
EXCLUDED_PREFIXES = ("tests/", "CHANGELOG.md", "docs/legacy.md", "frontend/node_modules/")

#: One argv token: a word/flag/path, a `<placeholder>`, a JSX or f-string interpolation, or
#: a quoted value (`--reason "tracked in JIRA-123"` is two tokens, not one and a half).
_PIECE = r"(?:--\$?\{[^}]*\}|<[A-Za-z0-9_.\-]*>|\$?\{[^}]*\}|[A-Za-z0-9_./=:\-]+)"
#: A token is one or more pieces with no space between them, so a path with a placeholder
#: inside it (`datasets/harvested/<draft-id>.json`) stays one argv token.
TOKEN = re.compile(f"(?:{_PIECE})+")
#: `--reason "tracked in JIRA-123"` is two argv tokens, so a quoted run has to be one of
#: them. But in a `.ts` file a quote also *ends* the string, and treating every quote as the
#: start of a value made `remedy: "failure-lab compare <a> <b>",` swallow the rest of the
#: file. A quoted run is only a value when it follows a flag, which is true in the shell too.
#: Either a quoted run or a run of pieces -- never a concatenation of the two. Allowing
#: them to mix let `<model>` glue onto the `"` that closed the string it sat in, and the
#: token then ran to the next quote hundreds of characters later.
SHELL_TOKEN = re.compile(f'"[^"\n]*"|(?:{_PIECE})+')

#: A flag or subcommand chosen at runtime (`--${scope.kind}`, `failure-lab {command_name}`)
#: cannot be checked against argparse without enumerating the runtime values, so those are
#: reported rather than validated. The list is asserted to stay short: an escape hatch, not
#: a habit.
DYNAMIC = re.compile(r"--\$?\{|^\$?\{")

#: Fenced code blocks in Markdown. Prose *about* a command is a reference; only a block
#: someone copies has to parse. `mermaid` blocks are diagrams whose arrows are not argv.
FENCE = re.compile(r"^```(\w*)\n(.*?)^```", re.MULTILINE | re.DOTALL)
DIAGRAM_LANGUAGES = {"mermaid"}
#: A `failure-lab` occurrence inside a quoted string -- something the program prints.
QUOTED = re.compile(r"""["'`][^"'`\n]*failure-lab\s""")
#: `model-failure-lab` is the other console script name; do not match its tail.
INVOCATION = re.compile(r"(?<![-\w])failure-lab\s")

#: Top-level subcommands, read from the parser so this cannot drift.
COMMANDS = frozenset(
    next(
        action.choices
        for action in build_parser()._actions
        if isinstance(action, argparse._SubParsersAction)
    )
)


def _tracked_sources() -> list[tuple[str, str]]:
    """Every tracked file that could carry a command, by `git ls-files` so it matches ship."""

    listed = subprocess.run(
        ["git", "ls-files"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    files: list[tuple[str, str]] = []
    for name in sorted(listed):
        if name.startswith(EXCLUDED_PREFIXES) or "__tests__" in name:
            continue
        if not name.endswith(SCANNED_SUFFIXES):
            continue
        try:
            files.append((name, (PROJECT_ROOT / name).read_text(encoding="utf-8")))
        except (OSError, UnicodeDecodeError):  # pragma: no cover - defensive
            continue
    return files


def _fstring_parts(node: ast.JoinedStr) -> list[str]:
    return [
        part.value if isinstance(part, ast.Constant) and isinstance(part.value, str) else "{}"
        for part in node.values
    ]


def _segments(name: str, text: str) -> list[str]:
    """The independent pieces of one file that could each hold a whole command.

    Scanning per segment rather than per flattened file is what lets this read the entire
    repository. Flattening works for JSX, where one string wraps across lines, and is wrong
    everywhere else: it welds a command in a fenced block to the sample output beneath it,
    and it welds each entry of a list of strings to the next.

    Python is parsed rather than pattern-matched, because `ast` folds implicitly
    concatenated literals into one constant -- which is exactly how a long remedy is
    written, and exactly what a regex gets wrong.
    """

    if name.endswith(".py"):
        try:
            tree = ast.parse(text)
        except SyntaxError:  # pragma: no cover - defensive
            return []
        inside_fstring = {
            id(part)
            for node in ast.walk(tree)
            if isinstance(node, ast.JoinedStr)
            for part in node.values
        }
        segments = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in inside_fstring
        ]
        # An f-string reaches `ast` as a JoinedStr whose literal halves are separate nodes.
        # Yielding those halves splits `f"… promote {path} " f"--dataset-id {id} --force"`
        # into two fragments, neither of which is a command. Rebuild it with `{}` standing
        # in for each interpolation, which is what the placeholder substitution expects.
        segments += ["".join(_fstring_parts(node)) for node in ast.walk(tree)
                     if isinstance(node, ast.JoinedStr)]
        return segments

    if name.endswith((".ts", ".tsx")):
        # JSX wraps one string across lines, so this is the one place flattening is right.
        # Comment lines are dropped first: a backticked command in a comment is a reference.
        body = "\n".join(
            line
            for line in text.splitlines()
            if not line.lstrip().startswith(("//", "*", "/*"))
        )
        return [re.sub(r"\n\s+", " ", body).replace("&lt;", "<").replace("&gt;", ">")]

    if name.endswith(".md"):
        blocks = [
            body
            for language, body in FENCE.findall(text)
            if language.lower() not in DIAGRAM_LANGUAGES
        ]
        text = "\n".join(blocks)

    # Shell and fenced blocks are line-oriented, with a trailing backslash for continuation.
    return re.sub(r"\\\n\s*", " ", text).splitlines()


def _scan(segment: str, *, shell: bool = False) -> list[str]:
    """Every `failure-lab …` command in one segment."""

    token_re = SHELL_TOKEN if shell else TOKEN
    flat = segment.replace("&lt;", "<").replace("&gt;", ">")
    commands: list[str] = []
    for match in INVOCATION.finditer(flat):
        tokens: list[str] = []
        position = match.end()
        while True:
            follows_a_flag = bool(tokens) and tokens[-1].startswith("--")
            token = (token_re if follows_a_flag else TOKEN).match(flat, position)
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
        if not tokens:
            continue
        # `the failure-lab CLI works end-to-end` is a sentence, not an invocation. Requiring
        # a real subcommand first is what lets this scan read the whole repository without
        # drowning in prose -- and a broken remedy always starts with a real subcommand,
        # because that is what makes it look runnable.
        if tokens[0] not in COMMANDS and not DYNAMIC.search(tokens[0]):
            continue
        commands.append(" ".join(tokens))
    return commands


def _extract_commands() -> list[tuple[str, str]]:
    return [
        (name, command)
        for name, text in _tracked_sources()
        for segment in _segments(name, text)
        for command in _scan(segment, shell=name.endswith((".sh", ".md", ".ts")))
    ]


def _argv(command: str) -> list[str]:
    """The command as `argv`, the way a shell would build it.

    `shlex`, not `str.split`: `--reason "fix tracked in JIRA-123"` is two arguments, and
    splitting on whitespace turns it into six and then blames argparse for rejecting them.
    """

    try:
        words = shlex.split(command)
    except ValueError:  # pragma: no cover - unbalanced quotes in a doc
        words = command.split()
    return [
        "PLACEHOLDER" if word.startswith(("<", "{", "${")) or word == "..." else word
        for word in words
    ]


_ALL = _extract_commands()
#: A bare `failure-lab <command>` with nothing after it names a command rather than giving
#: one to run. Kept out of the parse check and counted below, so the exemption stays visible.
REFERENCES = [(s, c) for s, c in _ALL if " " not in c]
CHECKABLE = [(s, c) for s, c in _ALL if " " in c and not DYNAMIC.search(c)]
RUNTIME_CHOSEN = [(s, c) for s, c in _ALL if " " in c and DYNAMIC.search(c)]


def test_the_extractor_finds_the_console_remedies() -> None:
    commands = {command for _, command in _extract_commands()}
    assert len(commands) >= 10, sorted(commands)
    joined = " | ".join(sorted(commands))
    # The shapes that shipped broken, so a regression in the extractor cannot hide them.
    for expected in ("harvest", "baselines set", "dataset promote", "dataset evolve"):
        assert expected in joined, f"{expected!r} not extracted from the console: {joined}"


def test_runtime_chosen_flags_stay_the_exception() -> None:
    # A command whose flag or subcommand name is interpolated cannot be validated here.
    # Keeping the list short is what stops "make it dynamic" becoming the way around this.
    assert len(RUNTIME_CHOSEN) <= 4, [command for _, command in RUNTIME_CHOSEN]


def test_bare_command_references_stay_the_exception() -> None:
    # Same reasoning: a one-word invocation is exempt from parsing, so the number of them
    # is capped rather than left to grow into a place broken remedies can hide.
    assert len(REFERENCES) <= 12, sorted({f"{s}: {c}" for s, c in REFERENCES})


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
