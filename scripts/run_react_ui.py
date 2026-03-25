# ruff: noqa: E402

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence

try:
    from scripts._bootstrap import bootstrap_repo_paths
except ModuleNotFoundError:
    from _bootstrap import bootstrap_repo_paths

bootstrap_repo_paths()

from model_failure_lab.runners.contracts import DispatchResult
from model_failure_lab.utils.paths import repository_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch the React failure debugger UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5173)
    return parser


def _default_runner(command: list[str], cwd: Path, env: dict[str, str]) -> int:
    if shutil.which("npm") is None:  # pragma: no cover - exercised through user runtime
        raise RuntimeError("npm is not installed or not available on PATH.")

    try:
        completed = subprocess.run(command, cwd=cwd, env=env, check=False)
    except FileNotFoundError as exc:  # pragma: no cover - exercised through user runtime
        raise RuntimeError(
            "Failed to launch the React UI because npm is unavailable on PATH."
        ) from exc
    return int(completed.returncode)


def run_command(
    argv: Sequence[str] | None = None,
    *,
    runner: Callable[[list[str], Path, dict[str, str]], int] | None = None,
) -> DispatchResult:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    repo_root = repository_root()
    frontend_package = repo_root / "frontend" / "package.json"
    if not frontend_package.exists():
        raise FileNotFoundError(f"React frontend package not found: {frontend_package}")

    command = [
        "npm",
        "--prefix",
        "frontend",
        "run",
        "dev",
        "--",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    env = os.environ.copy()

    launch_runner = runner or _default_runner
    exit_code = launch_runner(command, repo_root, env)
    status = "completed" if exit_code in {0, 130} else "failed"
    return DispatchResult(
        status=status,
        message=f"React UI launched from {frontend_package}",
        run_dir=repo_root,
        metadata_path=frontend_package,
        metrics_path=frontend_package,
        extras={
            "command": command,
            "cwd": str(repo_root),
            "host": args.host,
            "port": args.port,
        },
    )


def main(argv: Sequence[str] | None = None) -> int:
    result = run_command(argv)
    print(result.message)
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
