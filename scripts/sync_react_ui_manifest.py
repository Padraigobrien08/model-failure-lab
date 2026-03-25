# ruff: noqa: E402

from __future__ import annotations

import argparse
import filecmp
import shutil
import json
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


def _source_root_for_manifest(source_path: Path, version: str) -> Path:
    expected_suffix = ("artifacts", "contracts", "artifact_index", version, "index.json")
    if source_path.parts[-5:] == expected_suffix:
        return source_path.parents[4]
    return repository_root()


def _collect_sync_paths(payload: object) -> set[str]:
    collected: set[str] = set()

    def visit(value: object) -> None:
        if isinstance(value, dict):
            metadata_path = value.get("metadata_path")
            if isinstance(metadata_path, str):
                collected.add(metadata_path)

            for ref_group_name in ("artifact_refs", "payload_refs"):
                ref_group = value.get(ref_group_name)
                if isinstance(ref_group, dict):
                    for ref in ref_group.values():
                        if isinstance(ref, dict):
                            ref_path = ref.get("path")
                            if isinstance(ref_path, str) and ref.get("exists", True) is not False:
                                collected.add(ref_path)

            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(payload)
    return collected


def _sync_payload_artifacts(source_path: Path, target_root: Path, version: str, check: bool) -> None:
    manifest_payload = json.loads(source_path.read_text(encoding="utf-8"))
    source_root = _source_root_for_manifest(source_path, version)

    for relative_path in sorted(_collect_sync_paths(manifest_payload)):
        source_artifact = source_root / relative_path
        if not source_artifact.exists() or source_artifact.is_dir():
            continue

        target_artifact = target_root / relative_path
        if check:
            if not target_artifact.exists():
                raise FileNotFoundError(f"React UI artifact has not been synced yet: {target_artifact}")
            if not filecmp.cmp(source_artifact, target_artifact, shallow=False):
                raise ValueError(
                    f"React UI artifact is out of date for {relative_path}. "
                    "Re-run scripts/sync_react_ui_manifest.py."
                )
            continue

        target_artifact.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_artifact, target_artifact)


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
        _sync_payload_artifacts(source_path, target_root, args.version, check=True)
        return DispatchResult(
            status="completed",
            message=f"React UI manifest is in sync at {target_path}",
            run_dir=target_path.parent,
            metadata_path=target_path,
            metrics_path=source_path,
        )

    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)
    _sync_payload_artifacts(source_path, target_root, args.version, check=False)

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
