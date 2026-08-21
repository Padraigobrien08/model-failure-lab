"""Regression guard: the production CLI must not pull in the legacy ML stack.

The supported run -> report -> compare workflow has no dependency on the optional
``[legacy]`` extra (torch / pandas / numpy / scikit-learn / matplotlib / ...).
Importing the production surface in a fresh interpreter must therefore load none
of those packages. This test fails loudly if a future change reconnects the
production path to a heavy dependency at import time.

A subprocess is used so the assertion sees a pristine ``sys.modules`` table that
is unaffected by whatever the rest of the test session has already imported.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Make the subprocess work on a plain checkout too: pytest resolves the package via
# ``pythonpath = ["src"]``, but a fresh interpreter only sees installed packages, so
# put the repo's ``src`` on PYTHONPATH explicitly.
_SRC_DIR = Path(__file__).resolve().parents[2] / "src"

# Heavy/optional roots that the production import path must never trigger.
FORBIDDEN_LEGACY_MODULES = (
    "numpy",
    "pandas",
    "torch",
    "torchvision",
    "sklearn",
    "matplotlib",
    "transformers",
    "wilds",
    "pyarrow",
    "streamlit",
    "sentence_transformers",
)

# The production import surface exercised by run / report / compare / harvest.
PRODUCTION_IMPORTS = (
    "model_failure_lab.cli",
    "model_failure_lab.runner.execute",
    "model_failure_lab.runner.artifacts",
    "model_failure_lab.reporting.core",
    "model_failure_lab.reporting.compare",
    "model_failure_lab.reporting.artifacts",
    "model_failure_lab.reporting.load",
    "model_failure_lab.adapters",
    "model_failure_lab.classifiers",
    "model_failure_lab.index",
    "model_failure_lab.governance",
)


def _modules_loaded_after_production_import() -> list[str]:
    program = (
        "import sys\n"
        + "".join(f"import {name}\n" for name in PRODUCTION_IMPORTS)
        + "forbidden = "
        + repr(list(FORBIDDEN_LEGACY_MODULES))
        + "\n"
        + "print(','.join(m for m in forbidden if m in sys.modules))\n"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(_SRC_DIR), env.get("PYTHONPATH")) if part
    )
    result = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    loaded = result.stdout.strip()
    return [name for name in loaded.split(",") if name]


def test_production_cli_does_not_import_legacy_ml_stack() -> None:
    leaked = _modules_loaded_after_production_import()
    assert leaked == [], (
        "Production import path pulled in legacy ML dependencies: "
        f"{leaked}. The run -> report -> compare workflow must stay free of the "
        "[legacy] extra. Move the offending import inside the legacy code path "
        "or behind a lazy import."
    )
