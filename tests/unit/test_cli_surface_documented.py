"""Every reachable CLI command must appear in `docs/api.md`.

The CLI surface table was written by hand and drifted: `failure-lab init` and
`failure-lab baselines` both shipped without a row, and the header still claimed "13 top-level
commands, 44 handlers" against 15 and 45. Users read that table to find out what the tool can
do, so an undocumented command is a feature nobody can find.

This walks the real argparse tree rather than a maintained list, so adding a command without
documenting it fails here.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from model_failure_lab.cli import build_parser

API_DOC = Path(__file__).resolve().parents[2] / "docs" / "api.md"


def _subcommands(parser: argparse.ArgumentParser) -> dict[str, argparse.ArgumentParser]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return dict(action.choices)
    return {}


def _documented_text() -> str:
    return API_DOC.read_text(encoding="utf-8")


def test_every_top_level_command_is_documented() -> None:
    documented = _documented_text()
    missing = [
        name for name in sorted(_subcommands(build_parser())) if f"`{name}`" not in documented
    ]
    assert not missing, (
        f"top-level commands missing from docs/api.md: {missing}. Add a row to the CLI surface "
        "table -- an undocumented command is a feature nobody can find."
    )


def test_every_subcommand_is_documented() -> None:
    documented = _documented_text()
    missing: list[str] = []
    for group, parser in sorted(_subcommands(build_parser()).items()):
        for subcommand in sorted(_subcommands(parser)):
            if f"`{subcommand}`" not in documented:
                missing.append(f"{group} {subcommand}")
    assert not missing, f"subcommands missing from docs/api.md: {missing}"


def test_documented_command_counts_are_current() -> None:
    # The prose counts drifted for two releases. Assert them so the numbers stay honest, and
    # so the doc's own summary cannot contradict its table.
    top_level = _subcommands(build_parser())
    handler_count = sum(
        1
        for line in (
            Path(__file__).resolve().parents[2] / "src" / "model_failure_lab" / "cli.py"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.startswith("def _handle_")
    )
    expected = f"({len(top_level)} top-level commands, {handler_count} `_handle_*` handlers)"
    assert expected in _documented_text(), (
        f"docs/api.md should state {expected!r}; update the sentence when the surface changes"
    )
