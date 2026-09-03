"""`make release-facts` has to produce real numbers, or the notes get typed from memory again.

Every release from `0.11.0` to `0.15.0` carried at least one figure that was wrong: a count of
argparse collisions, a count of files a check reads, an "up from N" that was not N. The
citation rule added in `0.14.0` requires a bullet to name a test and cannot check arithmetic,
which it says in its own docstring -- and `0.15.0` promptly miscounted anyway.

`scripts/release_facts.py` is the answer, so it is itself a thing that can rot. Each fact is
resolved by importing a test module or parsing a source file; any of those can start throwing
and the script degrades to the string "unavailable", which reads like a number nobody needed
rather than a broken tool. This asserts every fact resolves to something with a digit in it.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "scripts" / "release_facts.py"


def _module():
    spec = importlib.util.spec_from_file_location("release_facts", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FACTS = _module().FACTS

#: Facts that shell out to a full test run. Correct, and far too slow for this suite; the
#: script is exercised end to end by `make release-facts` in the release checklist.
SLOW = {"python tests", "frontend tests"}


def test_the_makefile_exposes_it() -> None:
    makefile = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "release-facts:" in makefile
    assert "scripts/release_facts.py" in makefile


def test_the_release_checklist_tells_you_to_run_it() -> None:
    notes = (PROJECT_ROOT / "docs" / "release.md").read_text(encoding="utf-8")
    assert "make release-facts" in notes, (
        "docs/release.md is the file a maintainer reads before tagging; if it does not say "
        "to run the numbers, they will be typed from memory, which is the whole problem."
    )


@pytest.mark.parametrize("name", [n for n in FACTS if n not in SLOW])
def test_every_fact_resolves_to_a_number(name: str) -> None:
    value = FACTS[name]()
    assert "unavailable" not in value, f"{name}: {value}"
    assert re.search(r"\d", value), f"{name} produced no number: {value!r}"
