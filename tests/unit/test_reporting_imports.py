from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest


def _purge_modules(*prefixes: str) -> None:
    for name in list(sys.modules):
        if any(name == prefix or name.startswith(f"{prefix}.") for prefix in prefixes):
            sys.modules.pop(name, None)


def test_reporting_package_import_stays_light() -> None:
    had_matplotlib = "matplotlib" in sys.modules
    _purge_modules("model_failure_lab.reporting")

    reporting = importlib.import_module("model_failure_lab.reporting")

    if not had_matplotlib:
        assert "matplotlib" not in sys.modules
    assert "build_run_report" in reporting.__all__
    assert "build_comparison_report" in reporting.__all__
    assert "build_robustness_report_metadata" in reporting.__all__


@pytest.mark.legacy
def test_reporting_package_keeps_representative_exports_reachable() -> None:
    # ``reporting.legacy.bundle`` pulls in the legacy ML stack (pandas); this assertion
    # only applies when that optional stack is installed and cleanly importable.
    _purge_modules("model_failure_lab.reporting")

    reporting = importlib.import_module("model_failure_lab.reporting")
    core = importlib.import_module("model_failure_lab.reporting.core")
    compare = importlib.import_module("model_failure_lab.reporting.compare")
    bundle = importlib.import_module("model_failure_lab.reporting.legacy.bundle")

    assert reporting.build_run_report is core.build_run_report
    assert reporting.build_comparison_report is compare.build_comparison_report
    assert (
        reporting.build_robustness_report_metadata
        is bundle.build_robustness_report_metadata
    )


# ---------------------------------------------------------------------------------------
# The friendly "not shipped" message must not swallow a missing optional dependency.
# ---------------------------------------------------------------------------------------
#
# `reporting.legacy` is excluded from the wheel, so on an installed package its exports
# resolve to nothing and `__getattr__` says so. But the far more common ModuleNotFoundError
# here is a third-party import *inside* a legacy module -- a checkout without the
# `[legacy]` extra, which is what `make install-dev` gives you. Reporting that as "not
# shipped in the installed package" replaced `No module named 'matplotlib'` with something
# false, and broke two scripts' import path.
#
# Deliberately NOT marked `legacy`: the bug only appears when the extra is *absent*, so a
# test that needs it would be skipped in exactly the configuration that is broken. That is
# how this shipped green.


def test_a_missing_optional_dependency_is_reported_as_itself() -> None:
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pandas" or name.startswith("pandas."):
            raise ModuleNotFoundError("No module named 'pandas'", name="pandas")
        return real_import(name, *args, **kwargs)

    _purge_modules("model_failure_lab.reporting")
    reporting = importlib.import_module("model_failure_lab.reporting")
    builtins.__import__ = fake_import
    try:
        with pytest.raises(ModuleNotFoundError) as excinfo:
            reporting.build_report_metadata
    finally:
        builtins.__import__ = real_import
        _purge_modules("model_failure_lab.reporting")

    assert excinfo.value.name == "pandas"
    assert "not shipped in the installed package" not in str(excinfo.value)


def test_a_genuinely_absent_legacy_package_still_gets_the_friendly_message(tmp_path) -> None:
    # Mirror the wheel: the production surface present, `reporting/legacy/` deleted.
    import shutil
    import subprocess
    import sys

    source = Path(__file__).resolve().parents[2] / "src" / "model_failure_lab"
    staged = tmp_path / "model_failure_lab"
    shutil.copytree(source, staged)
    shutil.rmtree(staged / "reporting" / "legacy")

    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import model_failure_lab.reporting as r\n"
            "try:\n"
            "    r.build_report_metadata\n"
            "except AttributeError as exc:\n"
            "    print(exc)\n",
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
    )
    assert "not shipped in the installed package" in completed.stdout
    assert "docs/legacy.md" in completed.stdout
