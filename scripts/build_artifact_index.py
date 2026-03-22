# ruff: noqa: E402

from __future__ import annotations

import argparse
from typing import Sequence

try:
    from scripts._bootstrap import bootstrap_repo_paths
except ModuleNotFoundError:
    from _bootstrap import bootstrap_repo_paths

bootstrap_repo_paths()

from model_failure_lab.artifact_index import DEFAULT_ARTIFACT_INDEX_VERSION, write_artifact_index
from model_failure_lab.runners.contracts import DispatchResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the versioned artifact-index contract from saved artifacts."
    )
    parser.add_argument("--version", default=DEFAULT_ARTIFACT_INDEX_VERSION)
    return parser


def run_command(argv: Sequence[str] | None = None) -> DispatchResult:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    index_path = write_artifact_index(version=args.version)
    return DispatchResult(
        status="completed",
        message=f"Artifact index written to {index_path}",
        run_dir=index_path.parent,
        metadata_path=index_path,
        metrics_path=index_path,
    )


def main(argv: Sequence[str] | None = None) -> int:
    result = run_command(argv)
    print(result.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
