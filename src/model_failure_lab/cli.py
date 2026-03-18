"""Thin umbrella CLI that reuses the script entrypoints."""

from __future__ import annotations

import sys
from typing import Sequence

from scripts.build_report import main as build_report_main
from scripts.download_data import main as download_data_main
from scripts.run_baseline import main as run_baseline_main
from scripts.run_mitigation import main as run_mitigation_main
from scripts.run_shift_eval import main as run_shift_eval_main

COMMANDS = {
    "build-report": build_report_main,
    "download-data": download_data_main,
    "run-baseline": run_baseline_main,
    "run-mitigation": run_mitigation_main,
    "run-shift-eval": run_shift_eval_main,
}


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    if not args:
        available = ", ".join(sorted(COMMANDS))
        print(f"Usage: python -m model_failure_lab.cli <command> [args]\nCommands: {available}")
        return 1

    command, *remaining = args
    if command not in COMMANDS:
        available = ", ".join(sorted(COMMANDS))
        print(f"Unknown command: {command}\nCommands: {available}")
        return 1
    return COMMANDS[command](remaining)


if __name__ == "__main__":
    raise SystemExit(main())
