"""A ratchet on the one file that keeps growing.

`cli.py` is the whole command surface, and every round of this project's audits has flagged
its size. Round one flagged a 1,164-line `build_parser`; that was split, and the file grew
anyway, with `_add_dataset_parser` reaching 453 lines and 21 subcommands across three
unrelated concerns. Splitting it again fixes today's number and nothing else.

So the numbers are asserted, and they may only ever go down. The ceilings below sit just
above the current maxima: adding a subcommand is fine, growing a single function past the
ceiling is a decision somebody has to make deliberately by editing this file, with the
reason in the commit message.

This is not a style rule. A 453-line function that builds 21 subparsers is where the
`regressions --root` clobber lived unnoticed through two audits: it was structurally
identical to the `baselines` bug that was found, in a function nobody reads end to end.
"""

from __future__ import annotations

import ast
import warnings
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLI = PROJECT_ROOT / "src" / "model_failure_lab" / "cli.py"

#: Ratchets. Lower these when the file shrinks; raising one needs a reason in the commit.
MAX_FUNCTION_LINES = 175
MAX_FILE_LINES = 5000


def _functions() -> list[tuple[str, int, int]]:
    source = CLI.read_text(encoding="utf-8")
    tree = ast.parse(source)
    return [
        (node.name, node.end_lineno - node.lineno + 1, node.lineno)
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    ]


def test_no_cli_function_grows_past_the_ceiling() -> None:
    oversized = sorted(
        ((size, name, line) for name, size, line in _functions() if size > MAX_FUNCTION_LINES),
        reverse=True,
    )
    assert oversized == [], (
        f"these cli.py functions exceed {MAX_FUNCTION_LINES} lines: "
        + ", ".join(f"{name} ({size} lines, cli.py:{line})" for size, name, line in oversized)
        + ". Split by concern -- the parser builders are grouped that way already -- and "
        "prove it is pure motion by diffing the resolved argparse tree before and after."
    )


def test_cli_does_not_keep_growing() -> None:
    total = len(CLI.read_text(encoding="utf-8").splitlines())
    assert total <= MAX_FILE_LINES, (
        f"cli.py is {total} lines, over the {MAX_FILE_LINES} ratchet. Handlers and renderers "
        "for a subcommand group can move to their own module; the argparse tree is the "
        "contract, and `tests/unit/test_cli_option_inheritance.py` pins its shape."
    )


def test_a_loose_ratchet_says_so_without_failing() -> None:
    """A ceiling far above the real value stops being a ratchet -- but so does a red build.

    This assertion used to run the other way: it *failed* when the ceiling sat more than
    400 lines (or 60) above the real value, to stop the ratchet going stale. The effect was
    that shrinking `cli.py` by 400 lines, or splitting the largest function in half, turned
    CI red. A guard that punishes the behaviour it exists to encourage gets deleted the
    first time it blocks somebody, and it deserves to be.

    So slack is a warning. It is visible in the test output and in CI logs, it names the
    number to change, and it never stands between an author and a green build for making
    the file smaller.
    """

    largest = max(size for _, size, _ in _functions())
    total = len(CLI.read_text(encoding="utf-8").splitlines())
    for label, actual, ceiling, slack in (
        ("largest function", largest, MAX_FUNCTION_LINES, 60),
        ("cli.py", total, MAX_FILE_LINES, 400),
    ):
        if ceiling - actual > slack:
            warnings.warn(
                f"{label} is {actual} lines against a ceiling of {ceiling}. Lower the "
                f"ratchet in {Path(__file__).name} to lock the improvement in.",
                stacklevel=2,
            )
