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

`docs/release.md` is checked too. It was not for one release, and the overstatement moved
there immediately: `0.14.0`'s notes said `--root` "and every other inherited flag resolve
identically wherever they are written" while two options on `regressions pr-comment` did
not, and the branch's own test output said so in two `SKIPPED` lines. A rule that reads one
release-note file just relocates the problem to the other one.

What this cannot check is arithmetic. The same entry said "56 other collisions" across
"seven" subcommands where the tree had 58 across eight -- both cited a test, and the test
was real. A number in a release note should come from a command, not from memory.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHANGELOG = PROJECT_ROOT / "CHANGELOG.md"
RELEASE_NOTES = PROJECT_ROOT / "docs" / "release.md"

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
    #: Bullets under `### Docs` describe documentation, which has no behaviour to test.
    heading = ""
    #: `Errata` corrects a number in a released entry and `Chore` records repository
    #: housekeeping -- branches removed, files moved. Neither makes a claim about how the
    #: software behaves, which is the only kind of claim a test can settle. A bullet that
    #: does make one belongs under Fixed, Added or Changed, where it owes a citation.
    exempt_headings = {"docs", "documentation", "errata", "chore"}
    for line in section.splitlines():
        if line.startswith("###"):
            heading = line.lstrip("#").strip().lower()
        elif line.startswith("- "):
            if heading in exempt_headings:
                continue
            bullets.append(line[2:].strip())
        elif line.startswith("  ") and bullets and heading not in exempt_headings:
            bullets[-1] += " " + line.strip()
    return bullets


def _needs_citation(bullet: str) -> bool:
    """Whether this bullet is a claim about behaviour, and so owes a test.

    The first version keyed on backticks -- a command in `code` or a module path. Dropping
    the backticks was therefore a one-keystroke exemption: "The regression gate no longer
    exits 0 against the wrong workspace" is the same claim, needs the same evidence, and
    was waved through. Since every bullet under Fixed and Changed is by definition a claim
    that behaviour is different, the rule is now the section, not the punctuation. A bullet
    with nothing to cite belongs under Docs.
    """

    if DOCS_ONLY.match(bullet):
        return False
    refs = MODULE.findall(bullet)
    only_docs = refs and all("docs/" in ref or ref.endswith(".md`") for ref in refs)
    if only_docs:
        return False
    return True


def _test_files() -> set[str]:
    # `frontend/server/__tests__` holds the bridge's HTTP tests and sits outside `src`.
    # Missing it made a real citation look invented, which is the failure mode most likely
    # to get this check switched off.
    roots = (
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "frontend" / "src",
        PROJECT_ROOT / "frontend" / "server",
    )
    names: set[str] = set()
    for root in roots:
        for path in root.rglob("*"):
            if path.is_file() and (
                path.name.startswith("test_") or ".test." in path.name
            ):
                names.add(path.name)
    return names


BULLETS = [b for b in _bullets(_current_version()) if _needs_citation(b)]


def _release_note_claims() -> list[str]:
    """Sentences in `docs/release.md` that describe what the current tree does.

    Only the "Publishing the current tree" paragraph: the rest of that file is process
    (how to tag, which tags conflict, what is deferred), not claims about behaviour.
    """

    text = RELEASE_NOTES.read_text(encoding="utf-8")
    version = _current_version()
    marker = f"`{version}` is the current tree"
    if marker not in text:
        return []
    start = text.index(marker)
    end = text.find("\n\n", start)
    paragraph = text[start : end if end != -1 else len(text)]
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.:])\s", paragraph.replace("\n", " "))
        if sentence.strip()
    ]


def test_the_release_notes_describe_the_version_in_pyproject() -> None:
    version = _current_version()
    text = RELEASE_NOTES.read_text(encoding="utf-8")
    assert f"`{version}` is the current tree" in text, (
        f"docs/release.md does not describe {version}. It is the file a maintainer reads "
        "before tagging, so a stale version there is a release cut from the wrong notes."
    )


#: Words that turn a description into a guarantee. The `0.14.0` notes said `--root` "and
#: every other inherited flag" resolved identically wherever written; two options did not,
#: and the branch's own test output said so in two SKIPPED lines. The paragraph is a
#: summary and should not have to cite a test for every sentence -- but a sentence claiming
#: totality does, because totality is the thing that keeps turning out to be false.
ABSOLUTE = re.compile(
    r"\b(every|all|always|never|any|none|no other|cannot|guarantees?)\b", re.IGNORECASE
)


@pytest.mark.parametrize("claim", _release_note_claims(), ids=lambda c: c[:60])
def test_a_release_note_does_not_claim_totality_without_evidence(claim: str) -> None:
    quantifier = ABSOLUTE.search(claim)
    if quantifier is None:
        return
    assert CITATION.findall(claim), (
        f"this docs/release.md sentence claims {quantifier.group(0)!r} without citing a "
        f"test:\n    {claim[:400]}\n"
        "Cite the test that proves the whole set, or describe the change without the "
        "quantifier. Four releases running, the overstatement has been an absolute word."
    )


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
