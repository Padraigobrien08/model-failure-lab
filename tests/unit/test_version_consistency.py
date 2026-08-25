"""One version, stated once per surface, and all of them agreeing.

The audit found four different versions visible without opening a source file: the README
hero screenshot showed `v0.9.0`, the console shell hardcoded `v0.10.0`, `pyproject.toml` said
`0.10.1`, and the PyPI badge rendered `0.1.0`. A tool whose product is artifact provenance
should not misreport its own version.

The console now reads the version from `pyproject.toml` at build time (see `define` in
`frontend/vite.config.ts`), and the screenshots are recaptured on release. This pins the
remaining hand-maintained copies.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import model_failure_lab

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _pyproject_version() -> str:
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as handle:
        return str(tomllib.load(handle)["project"]["version"])


def test_package_version_matches_pyproject() -> None:
    assert model_failure_lab.__version__ == _pyproject_version(), (
        "src/model_failure_lab/__init__.py and pyproject.toml disagree; bump both together"
    )


def test_readme_project_status_matches_the_package() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(r"Pre-1\.0 \(`([^`]+)`, public beta\)", readme)
    assert match, "README should state the current version in its Project status section"
    assert match.group(1) == _pyproject_version(), (
        "the README's Project status version is stale; it is the version a reader sees"
    )


def test_changelog_documents_the_current_version() -> None:
    changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    version = _pyproject_version()
    assert f"## [{version}]" in changelog, (
        f"CHANGELOG.md has no entry for {version}. A version bump without an entry leaves "
        "consumers unable to see what changed -- including the behavior changes."
    )


def test_console_reads_its_version_rather_than_hardcoding_one() -> None:
    # The specific regression: `const APP_VERSION = "v0.10.0 · local"` had already drifted by
    # the time it shipped. Assert the shell interpolates the injected value instead.
    shell = (
        PROJECT_ROOT / "frontend" / "src" / "components" / "layout" / "ConsoleShell.tsx"
    ).read_text(encoding="utf-8")
    assert "__APP_VERSION__" in shell, "the console shell must read the injected package version"
    assert not re.search(r'APP_VERSION\s*=\s*"v\d', shell), (
        "the console shell hardcodes a version string again"
    )
