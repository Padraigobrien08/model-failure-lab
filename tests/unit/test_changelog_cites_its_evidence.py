"""A release note that names a command has to name the test that proves it.

Three releases running, this project's CHANGELOG overstated a guarantee:

* `0.11.0` said a dead manifest stack was deleted; part of it was still imported.
* `0.12.0` said a broken printed remedy was fixed; `git log -S` showed the string was never
  touched -- the entry was written and the code was not.
* `0.13.0` said "a stripped pack is now a disagreement between two committed files"; true for
  `dataset promote`, false for `dataset evolve`, which is the mode the console offers first.

Each was written from the fix rather than from the surface, and each was read back by its
author as evidence that the surface was covered. The habit that catches all three is cheap:
name the test. You cannot cite a test for a fix you only applied to one of two callers
without noticing the other one is not in it.

So: every bullet in the entry for the version in `pyproject.toml` that names a command or a
source module must also name a test file that exists. Earlier entries are released history
and are left exactly as they were written -- correcting them here would be rewriting the
record rather than keeping it.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHANGELOG = PROJECT_ROOT / "CHANGELOG.md"

#: A backticked reference to something executable: a CLI invocation, or a Python/TS module.
COMMAND = re.compile(r"`(?:failure-lab|model-failure-lab|python3? -m model_failure_lab)\s")
MODULE = re.compile(r"`[\w./]*\w+\.(?:py|ts|tsx)`|`[\w.]+\.[\w.]*(?:py)`")
#: A citation: a test file, named as a bare filename or a path.
CITATION = re.compile(r"`([\w./]*(?:test_[\w.]+\.py|[\w.]+\.test\.tsx?))`")
#: Bullets about documentation or release mechanics have no test to cite.
DOCS_ONLY = re.compile(r"^`?docs/|^`?README|^`?CHANGELOG")


def _current_version() -> str:
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as handle:
        return str(tomllib.load(handle)["project"]["version"])


def _bullets(version: str) -> list[str]:
    """Top-level bullets in the section for `version`, each joined into one line."""

    text = CHANGELOG.read_text(encoding="utf-8")
    start = text.index(f"## [{version}]")
    end = text.find("\n## [", start + 1)
    section = text[start : end if end != -1 else len(text)]

    bullets: list[str] = []
    for line in section.splitlines():
        if line.startswith("- "):
            bullets.append(line[2:].strip())
        elif line.startswith("  ") and bullets:
            bullets[-1] += " " + line.strip()
        elif not line.strip():
            continue
        elif line.startswith("#"):
            continue
    return bullets


def _needs_citation(bullet: str) -> bool:
    if DOCS_ONLY.match(bullet):
        return False
    refs = MODULE.findall(bullet)
    only_docs = refs and all("docs/" in ref or ref.endswith(".md`") for ref in refs)
    return bool(COMMAND.search(bullet) or refs) and not only_docs


def _test_files() -> set[str]:
    roots = (PROJECT_ROOT / "tests", PROJECT_ROOT / "frontend" / "src")
    names: set[str] = set()
    for root in roots:
        for path in root.rglob("*"):
            if path.is_file() and (
                path.name.startswith("test_") or ".test." in path.name
            ):
                names.add(path.name)
    return names


BULLETS = [b for b in _bullets(_current_version()) if _needs_citation(b)]


def test_the_current_entry_actually_has_bullets_to_check() -> None:
    assert len(BULLETS) >= 3, (
        f"only {len(BULLETS)} citable bullets found for {_current_version()}; either the "
        "entry is thin or the parser stopped matching the CHANGELOG's format."
    )


@pytest.mark.parametrize("bullet", BULLETS, ids=lambda b: b[:60])
def test_a_bullet_naming_a_command_cites_a_test(bullet: str) -> None:
    cited = CITATION.findall(bullet)
    assert cited, (
        "this CHANGELOG bullet names a command or module but cites no test:\n"
        f"    {bullet[:400]}\n"
        "Name the test that proves it. If there is no such test, the entry is a claim "
        "about code somebody read rather than about behaviour somebody checked -- which is "
        "how this file has overstated a guarantee in each of the last three releases."
    )

    known = _test_files()
    missing = [name for name in cited if Path(name).name not in known]
    assert missing == [], (
        f"this bullet cites tests that do not exist: {missing}. "
        f"Bullet: {bullet[:200]}"
    )
