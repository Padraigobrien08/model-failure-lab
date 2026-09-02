"""A path the console prints has to be a path the engine writes.

`DESIGN.md` requires an empty state to name "the path it read plus the CLI command to fix
it", so these strings are load-bearing: they are what an operator opens when nothing is
there. They are also plain text in a `.tsx` file, with nothing tying them to the engine.

The gate screen shipped telling operators the shared baseline registry lived at
`.failure_lab/baseline_registry.json` for a full release after `0.13.0` moved it to
`governance/baselines.json` -- and the whole point of that move was that `.failure_lab/` is
the derived index, which `.gitignore` excludes and `make clean` deletes irrecoverably. The
console was sending people to look for their registry in the one directory the release notes
had just finished explaining it must not be in.

`test_console_commands_are_runnable.py` covers the commands these strings print. This covers
the paths beside them: every workspace-relative path the console names is resolved against
`storage/layout.py` and the engine's own path constants, so a path that moves in the engine
and not in the console fails here.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from model_failure_lab.datasets.integrity import PROMOTION_LEDGER_PATH
from model_failure_lab.governance.baselines import (
    BASELINE_REGISTRY_PATH,
    LEGACY_BASELINE_REGISTRY_PATH,
)
from model_failure_lab.index import QUERY_INDEX_DIRNAME, QUERY_INDEX_FILENAME
from model_failure_lab.storage import layout

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONSOLE_DIRS = (
    PROJECT_ROOT / "frontend" / "src" / "app" / "routes",
    PROJECT_ROOT / "frontend" / "src" / "components" / "console",
    PROJECT_ROOT / "frontend" / "src" / "components" / "layout",
)

#: A workspace-relative path literal: one of the engine's top-level directories, then more.
PATH_LITERAL = re.compile(
    r"(?:governance|datasets|runs|reports|\.failure_lab)/[A-Za-z0-9_./<>-]*"
)
#: `<draft-id>.json` and friends stand for a filename chosen at runtime.
PLACEHOLDER = re.compile(r"<[^>]*>")


def _engine_paths(tmp_root: Path) -> set[str]:
    """Every workspace-relative path the engine resolves, from the engine itself."""

    known = {
        f"{QUERY_INDEX_DIRNAME}/{QUERY_INDEX_FILENAME}",
        BASELINE_REGISTRY_PATH,
        LEGACY_BASELINE_REGISTRY_PATH,
        PROMOTION_LEDGER_PATH,
        # Harvest drafts: `harvest --out` defaults under the datasets root.
        "datasets/harvested",
    }
    for name in dir(layout):
        if not name.endswith("_root"):
            continue
        resolver = getattr(layout, name)
        if not callable(name and resolver):
            continue
        try:
            resolved = resolver(root=tmp_root, create=False)
        except TypeError:  # project_root takes a positional argument
            continue
        known.add(resolved.relative_to(tmp_root).as_posix())
    return known


def _console_paths() -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for directory in CONSOLE_DIRS:
        for path in sorted(directory.glob("*.ts*")):
            if "__tests__" in path.parts:
                continue
            # JSX line-wraps long strings and writes angle brackets as entities.
            flat = (
                re.sub(r"\n\s+", " ", path.read_text(encoding="utf-8"))
                .replace("&lt;", "<")
                .replace("&gt;", ">")
            )
            for match in PATH_LITERAL.findall(flat):
                found.append((str(path.relative_to(PROJECT_ROOT)), match.rstrip("/.")))
    return sorted(set(found))


CONSOLE_PATHS = _console_paths()


def test_the_scan_still_finds_the_paths_the_console_prints() -> None:
    printed = {path for _, path in CONSOLE_PATHS}
    assert len(printed) >= 4, sorted(printed)
    assert "governance/baselines.json" in printed, (
        "the gate screen's empty state should name the baseline registry; it named the "
        f"pre-0.13.0 location for a release. Found: {sorted(printed)}"
    )


@pytest.mark.parametrize(("source", "printed"), CONSOLE_PATHS, ids=lambda v: str(v))
def test_a_path_the_console_prints_is_one_the_engine_uses(
    source: str, printed: str, tmp_path: Path
) -> None:
    known = _engine_paths(tmp_path)
    #: A printed file path is fine if the engine owns its directory; a printed directory
    #: must be one the engine resolves.
    stem = PLACEHOLDER.sub("", printed).rstrip("/")
    accepted = stem in known or any(
        stem.startswith(f"{candidate}/") or candidate.startswith(f"{stem}/")
        for candidate in known
    )
    assert accepted, (
        f"{source} prints `{printed}`, which the engine does not resolve. "
        f"Engine paths: {sorted(known)}. A path in an empty state is what an operator "
        "opens when nothing is there -- pointing at the wrong one is worse than silence."
    )


def test_the_console_does_not_send_operators_to_the_disposable_directory() -> None:
    """`.failure_lab/` is derived: gitignored, and deleted by `make clean`.

    The query index legitimately lives there. Anything a human recorded does not, which is
    exactly the mistake the gate screen shipped.
    """

    derived_index = f"{QUERY_INDEX_DIRNAME}/{QUERY_INDEX_FILENAME}"
    offenders = sorted(
        (source, printed)
        for source, printed in CONSOLE_PATHS
        if printed.startswith(f"{QUERY_INDEX_DIRNAME}/") and printed != derived_index
    )
    assert offenders == [], (
        f"these screens point an operator at {QUERY_INDEX_DIRNAME}/, which `make clean` "
        f"deletes: {offenders}. Only the derived index ({derived_index}) belongs there."
    )
