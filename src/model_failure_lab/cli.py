"""Thin umbrella CLI that reuses the script entrypoints."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Sequence

COMMAND_MODULES = {
    "build-perturbation-report": "scripts.build_perturbation_report",
    "build-report": "scripts.build_report",
    "check-environment": "scripts.check_environment",
    "download-data": "scripts.download_data",
    "run-baseline": "scripts.run_baseline",
    "run-mitigation": "scripts.run_mitigation",
    "run-perturbation-eval": "scripts.run_perturbation_eval",
    "run-shift-eval": "scripts.run_shift_eval",
}


def _ensure_scripts_package() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


def _resolve_command(command: str):
    _ensure_scripts_package()
    module = importlib.import_module(COMMAND_MODULES[command])
    return module.main


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    if not args:
        available = ", ".join(sorted(COMMAND_MODULES))
        print(f"Usage: python -m model_failure_lab.cli <command> [args]\nCommands: {available}")
        return 1

    command, *remaining = args
    if command not in COMMAND_MODULES:
        available = ", ".join(sorted(COMMAND_MODULES))
        print(f"Unknown command: {command}\nCommands: {available}")
        return 1
    return _resolve_command(command)(remaining)


if __name__ == "__main__":
    raise SystemExit(main())
