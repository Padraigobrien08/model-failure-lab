#!/usr/bin/env python3
"""Print the countable facts a release note is likely to state.

Five releases running, this project's notes have carried a number that was wrong: a count of
argparse collisions, a count of files a check reads, a "up from N" that was not N. Every one
was typed from memory a few hours after the work, and every one cited a real test -- the
citation rule added in `0.14.0` cannot catch arithmetic, and says so in its own docstring.

So: `make release-facts`, then paste. A number in a release note should have a command behind
it. Run from the repository root, against the working tree as it stands.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _version() -> str:
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as handle:
        return str(tomllib.load(handle)["project"]["version"])


def _pytest_count() -> str:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--collect-only"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    for line in reversed(result.stdout.splitlines()):
        if "test" in line and "collected" in line:
            # "N tests collected" counts skips too; say so rather than let it be quoted as
            # a pass count.
            return f"{line.strip()} (collected, including skips)"
    return "unavailable"


def _vitest_count() -> str:
    result = subprocess.run(
        ["npm", "--prefix", "frontend", "test", "--", "--run", "--reporter=json"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "numTotalTests" in payload:
            # `numTotalTestSuites` counts describe blocks, not files -- reporting it as
            # "files" would be exactly the kind of number this script exists to stop.
            return f"{payload['numTotalTests']} tests"
    return "unavailable (run `npm --prefix frontend test` directly)"


def _cli_shape() -> str:
    source = (PROJECT_ROOT / "src" / "model_failure_lab" / "cli.py").read_text(encoding="utf-8")
    functions = [
        (node.end_lineno - node.lineno + 1, node.name)
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef)
    ]
    size, name = max(functions)
    return f"{len(source.splitlines())} lines, {len(functions)} functions, largest {name} at {size}"


def _printed_commands() -> str:
    sys.path.insert(0, str(PROJECT_ROOT / "tests" / "unit"))
    try:
        import test_console_commands_are_runnable as scan
    except Exception as error:  # pragma: no cover - defensive
        return f"unavailable ({error})"
    files = {source for source, _ in scan._ALL}
    return (
        f"{len(files)} files, {len(scan.CHECKABLE)} checkable commands, "
        f"{len(scan.REFERENCES)} bare references, {len(scan.RUNTIME_CHOSEN)} runtime-chosen"
    )


def _option_collisions() -> str:
    sys.path.insert(0, str(PROJECT_ROOT / "tests" / "unit"))
    try:
        import test_cli_option_inheritance as inheritance
    except Exception as error:  # pragma: no cover - defensive
        return f"unavailable ({error})"
    return f"{len(inheritance.COLLISIONS)} inherited-option collisions, all suppressed"


def _gate_attack_grid() -> str:
    sys.path.insert(0, str(PROJECT_ROOT / "tests" / "unit"))
    try:
        import test_gate_resists_a_motivated_operator as attacks
    except Exception as error:  # pragma: no cover - defensive
        return f"unavailable ({error})"
    return (
        f"{len(attacks.RUN_EDITS)} run edits x {len(attacks.RUN_TARGETS)} targets + "
        f"{len(attacks.DATASET_EDITS)} dataset edits = {len(attacks.CASES)} combinations, "
        f"{len(attacks.DOCUMENTED_GAPS)} documented gaps"
    )


FACTS = {
    "version": _version,
    "python tests": _pytest_count,
    "frontend tests": _vitest_count,
    "cli.py": _cli_shape,
    "printed-command scan": _printed_commands,
    "cli option inheritance": _option_collisions,
    "gate attack grid": _gate_attack_grid,
}


def main() -> int:
    width = max(len(name) for name in FACTS)
    for name, resolve in FACTS.items():
        print(f"{name:<{width}}  {resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
