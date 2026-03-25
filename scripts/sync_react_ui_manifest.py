# ruff: noqa: E402

from __future__ import annotations

import argparse
import filecmp
import shutil
from pathlib import Path
from typing import Sequence

try:
    from scripts._bootstrap import bootstrap_repo_paths
except ModuleNotFoundError:
    from _bootstrap import bootstrap_repo_paths

bootstrap_repo_paths()

from model_failure_lab.artifact_index.schema import (
    ARTIFACT_INDEX_SCHEMA_VERSION,
    DEFAULT_ARTIFACT_INDEX_VERSION,
)
from model_failure_lab.runners.contracts import DispatchResult
from model_failure_lab.utils.paths import build_artifact_index_path, repository_root


def _default_target_root() -> Path:
    return repository_root() / "frontend" / "public"


def _target_manifest_path(target_root: Path, version: str) -> Path:
    return target_root / "artifacts" / "contracts" / "artifact_index" / version / "index.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sync the artifact-index contract into the React UI static path."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=build_artifact_index_path(version=DEFAULT_ARTIFACT_INDEX_VERSION),
    )
    parser.add_argument(
        "--target-root",
        type=Path,
        default=_default_target_root(),
    )
    parser.add_argument(
        "--version",
        default=DEFAULT_ARTIFACT_INDEX_VERSION,
    )
    parser.add_argument("--check", action="store_true")
    return parser


def _validate_source_manifest(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Artifact index not found: {path}")

    payload = path.read_text(encoding="utf-8")
    if ARTIFACT_INDEX_SCHEMA_VERSION not in payload:
        raise ValueError(
            "Source manifest does not appear to use the expected artifact index schema."
        )


def run_command(argv: Sequence[str] | None = None) -> DispatchResult:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    source_path = args.source.resolve()
    target_root = args.target_root.resolve()
    target_path = _target_manifest_path(target_root, args.version)

    _validate_source_manifest(source_path)

    if args.check:
        if not target_path.exists():
            raise FileNotFoundError(f"React UI manifest has not been synced yet: {target_path}")
        if not filecmp.cmp(source_path, target_path, shallow=False):
            raise ValueError(
                "React UI manifest is out of date. Re-run scripts/sync_react_ui_manifest.py."
            )
        return DispatchResult(
            status="completed",
            message=f"React UI manifest is in sync at {target_path}",
            run_dir=target_path.parent,
            metadata_path=target_path,
            metrics_path=source_path,
        )

    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)

    return DispatchResult(
        status="completed",
        message=f"React UI manifest synced to {target_path}",
        run_dir=target_path.parent,
        metadata_path=target_path,
        metrics_path=source_path,
    )


def main(argv: Sequence[str] | None = None) -> int:
    result = run_command(argv)
    print(result.message)
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
