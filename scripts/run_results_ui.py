# ruff: noqa: E402

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, Sequence

try:
    from scripts._bootstrap import bootstrap_repo_paths
except ModuleNotFoundError:
    from _bootstrap import bootstrap_repo_paths

bootstrap_repo_paths()

from model_failure_lab.results_ui.load import default_results_ui_index_path
from model_failure_lab.runners.contracts import DispatchResult
from model_failure_lab.utils.paths import repository_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch the read-only results explorer UI.")
    parser.add_argument("--index", type=Path, default=default_results_ui_index_path())
    parser.add_argument("--port", type=int, default=8501)
    parser.add_argument("--include-exploratory", action="store_true")
    return parser


def _default_runner(app_path: Path, app_args: list[str], server_args: list[str]) -> int:
    try:
        from streamlit.web import cli as stcli
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised through user runtime
        raise RuntimeError(
            "streamlit is not installed. Install the optional UI dependency with "
            "`python3 -m pip install -e .[ui]`."
        ) from exc

    previous_argv = list(sys.argv)
    try:
        sys.argv = ["streamlit", "run", str(app_path), *server_args, "--", *app_args]
        return int(stcli.main() or 0)
    finally:
        sys.argv = previous_argv


def run_command(
    argv: Sequence[str] | None = None,
    *,
    runner: Callable[[Path, list[str], list[str]], int] | None = None,
) -> DispatchResult:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    index_path = args.index.resolve()
    if not index_path.exists():
        raise FileNotFoundError(f"Artifact index not found: {index_path}")

    app_path = repository_root() / "src" / "model_failure_lab" / "results_ui" / "app.py"
    app_args = ["--index", str(index_path)]
    if args.include_exploratory:
        app_args.append("--include-exploratory")
    server_args = ["--server.port", str(args.port)]

    launch_runner = runner or _default_runner
    exit_code = launch_runner(app_path, app_args, server_args)
    status = "completed" if exit_code == 0 else "failed"
    return DispatchResult(
        status=status,
        message=f"Results UI launched from {index_path}",
        run_dir=repository_root(),
        metadata_path=index_path,
        metrics_path=index_path,
        extras={
            "app_path": str(app_path),
            "server_args": server_args,
            "app_args": app_args,
        },
    )


def main(argv: Sequence[str] | None = None) -> int:
    result = run_command(argv)
    print(result.message)
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
