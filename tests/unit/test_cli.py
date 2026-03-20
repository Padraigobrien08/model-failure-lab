from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"


def _module_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT)
    return env


def test_python_module_entrypoint_prints_usage_without_args():
    result = subprocess.run(
        [sys.executable, "-m", "model_failure_lab"],
        cwd=PROJECT_ROOT,
        env=_module_env(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Usage: python -m model_failure_lab.cli <command> [args]" in result.stdout
    assert "run-baseline" in result.stdout


def test_python_module_cli_prints_usage_without_args():
    result = subprocess.run(
        [sys.executable, "-m", "model_failure_lab.cli"],
        cwd=PROJECT_ROOT,
        env=_module_env(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Usage: python -m model_failure_lab.cli <command> [args]" in result.stdout
    assert "build-perturbation-report" in result.stdout
