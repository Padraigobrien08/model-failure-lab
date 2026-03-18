"""Metadata manifest builders for reproducible run bundles."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

DEFAULT_VERSION_PACKAGES = {
    "torch": "torch",
    "scikit_learn": "scikit-learn",
    "transformers": "transformers",
    "wilds": "wilds",
    "pyyaml": "PyYAML",
    "pandas": "pandas",
    "pyarrow": "pyarrow",
}


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def resolve_git_commit_hash(cwd: Path | None = None) -> str | None:
    """Return the current git commit hash when available."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        check=False,
        cwd=cwd,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def resolve_library_versions() -> dict[str, str | None]:
    """Return the pinned library versions available in the local environment."""
    versions: dict[str, str | None] = {}
    for key, package_name in DEFAULT_VERSION_PACKAGES.items():
        try:
            versions[key] = metadata.version(package_name)
        except metadata.PackageNotFoundError:
            versions[key] = None
    return versions


def build_artifact_paths(run_dir: Path) -> dict[str, str]:
    """Build the standard artifact path map for a run directory."""
    return {
        "checkpoint": str(run_dir / "checkpoint"),
        "predictions": str(run_dir / "predictions.parquet"),
        "metrics_json": str(run_dir / "metrics.json"),
        "plots": str(run_dir / "figures"),
    }


def build_run_metadata(
    *,
    run_id: str,
    experiment_type: str,
    model_name: str,
    dataset_name: str,
    split_details: dict[str, str],
    random_seed: int,
    resolved_config: dict[str, Any],
    command: str,
    run_dir: Path,
    git_commit_hash: str | None = None,
    library_versions: dict[str, str | None] | None = None,
    artifact_paths: dict[str, str] | None = None,
    parent_run_id: str | None = None,
    notes: str = "",
    tags: list[str] | None = None,
    timestamp: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Build the metadata payload for a run."""
    metadata_payload: dict[str, Any] = {
        "run_id": run_id,
        "timestamp": timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "experiment_type": experiment_type,
        "model_name": model_name,
        "dataset_name": dataset_name,
        "split_details": split_details,
        "random_seed": random_seed,
        "resolved_config": resolved_config,
        "command": command,
        "git_commit_hash": git_commit_hash
        if git_commit_hash is not None
        else resolve_git_commit_hash(run_dir),
        "library_versions": library_versions or resolve_library_versions(),
        "artifact_paths": artifact_paths or build_artifact_paths(run_dir),
        "parent_run_id": parent_run_id,
        "notes": notes,
        "tags": tags or [],
    }
    if status is not None:
        metadata_payload["status"] = status
    return metadata_payload


def write_metadata(run_dir: Path, metadata_payload: dict[str, Any]) -> Path:
    """Write metadata.json inside the supplied run directory."""
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "checkpoint").mkdir(parents=True, exist_ok=True)
    (run_dir / "figures").mkdir(parents=True, exist_ok=True)
    return _write_json(run_dir / "metadata.json", metadata_payload)
