"""Version consistency + CLI `--version` flag."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

import model_failure_lab
from model_failure_lab.cli import CANONICAL_COMMAND, _package_version, main

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _pyproject_version() -> str:
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["version"]


def test_in_tree_version_sources_agree() -> None:
    # Guards against the dual-source drift between pyproject.toml and __init__.py.
    assert model_failure_lab.__version__ == _pyproject_version()


def test_cli_version_flag_prints_installed_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out.strip()
    assert out == f"{CANONICAL_COMMAND} {_package_version()}"
