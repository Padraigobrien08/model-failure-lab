from __future__ import annotations

import importlib
import sys


def _purge_modules(*prefixes: str) -> None:
    for name in list(sys.modules):
        if any(name == prefix or name.startswith(f"{prefix}.") for prefix in prefixes):
            sys.modules.pop(name, None)


def test_reporting_package_import_stays_light() -> None:
    _purge_modules("model_failure_lab.reporting", "matplotlib")

    reporting = importlib.import_module("model_failure_lab.reporting")

    assert "matplotlib" not in sys.modules
    assert "build_run_report" in reporting.__all__
    assert "build_comparison_report" in reporting.__all__
    assert "build_robustness_report_metadata" in reporting.__all__


def test_reporting_package_keeps_representative_exports_reachable() -> None:
    _purge_modules("model_failure_lab.reporting", "matplotlib")

    reporting = importlib.import_module("model_failure_lab.reporting")
    core = importlib.import_module("model_failure_lab.reporting.core")
    compare = importlib.import_module("model_failure_lab.reporting.compare")
    bundle = importlib.import_module("model_failure_lab.reporting.bundle")

    assert reporting.build_run_report is core.build_run_report
    assert reporting.build_comparison_report is compare.build_comparison_report
    assert (
        reporting.build_robustness_report_metadata
        is bundle.build_robustness_report_metadata
    )
