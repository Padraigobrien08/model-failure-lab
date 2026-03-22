# ruff: noqa: E402

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

try:
    from scripts._bootstrap import bootstrap_repo_paths
except ModuleNotFoundError:
    from _bootstrap import bootstrap_repo_paths

bootstrap_repo_paths()

from model_failure_lab.artifact_index import (
    DEFAULT_ARTIFACT_INDEX_VERSION,
    load_artifact_index,
    validate_artifact_index_payload,
)
from model_failure_lab.runners.contracts import DispatchResult
from model_failure_lab.utils.paths import build_artifact_index_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the generated artifact-index contract.")
    parser.add_argument(
        "--index",
        default=str(build_artifact_index_path(version=DEFAULT_ARTIFACT_INDEX_VERSION)),
    )
    parser.add_argument("--strict", action="store_true")
    return parser


def run_command(argv: Sequence[str] | None = None) -> DispatchResult:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    index_path = Path(args.index)
    payload = load_artifact_index(index_path)
    errors = validate_artifact_index_payload(payload)
    status = "completed" if not errors else "failed" if args.strict else "warnings"
    if errors and args.strict:
        raise ValueError("Artifact index validation failed:\n- " + "\n- ".join(errors))
    message = (
        f"Artifact index validation passed for {index_path}"
        if not errors
        else f"Artifact index validation reported {len(errors)} issue(s) for {index_path}"
    )
    return DispatchResult(
        status=status,
        message=message,
        run_dir=index_path.parent,
        metadata_path=index_path,
        metrics_path=index_path,
        extras={"errors": errors},
    )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        result = run_command(argv)
    except Exception as exc:  # pragma: no cover - CLI error reporting
        print(str(exc), file=sys.stderr)
        return 1

    print(result.message)
    return 1 if result.status == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
