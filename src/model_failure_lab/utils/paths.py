"""Filesystem contracts for configs, artifacts, and reports."""

from __future__ import annotations

import os
import re
from pathlib import Path

ARTIFACT_ROOT_ENV = "MODEL_FAILURE_LAB_ARTIFACT_ROOT"
CONFIG_ROOT_ENV = "MODEL_FAILURE_LAB_CONFIG_ROOT"
_SEGMENT_PATTERN = re.compile(r"[^a-z0-9]+")
_PREDICTION_SPLIT_SUFFIXES = {
    "train": "train",
    "validation": "val",
    "val": "val",
    "test": "test",
    "id_test": "id_test",
    "ood_test": "ood_test",
}


def repository_root() -> Path:
    """Return the repository root for the current source tree."""
    return Path(__file__).resolve().parents[3]


def _normalize_segment(value: str) -> str:
    normalized = _SEGMENT_PATTERN.sub("_", value.strip().lower()).strip("_")
    return normalized or "default"


def _resolve_root(env_var: str, default_relative_path: str) -> Path:
    default_root = repository_root() / default_relative_path
    env_raw = os.environ.get(env_var)
    if env_raw:
        resolved_root = Path(env_raw).expanduser().resolve()
        resolved_root.mkdir(parents=True, exist_ok=True)
        return resolved_root
    default_root.mkdir(parents=True, exist_ok=True)
    return default_root


def artifact_root() -> Path:
    """Return the artifact root, honoring test overrides."""
    return _resolve_root(ARTIFACT_ROOT_ENV, "artifacts")


def config_root() -> Path:
    """Return the config root, honoring test overrides."""
    return _resolve_root(CONFIG_ROOT_ENV, "configs")


def build_baseline_run_dir(model_name: str, run_id: str, create: bool = False) -> Path:
    """Return the canonical baseline run directory."""
    run_dir = (
        artifact_root() / "baselines" / _normalize_segment(model_name) / _normalize_segment(run_id)
    )
    if create:
        run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def build_mitigation_run_dir(
    method_name: str,
    model_name: str,
    run_id: str,
    create: bool = False,
) -> Path:
    """Return the canonical mitigation run directory."""
    run_dir = (
        artifact_root()
        / "mitigations"
        / _normalize_segment(method_name)
        / _normalize_segment(model_name)
        / _normalize_segment(run_id)
    )
    if create:
        run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def build_report_dir(
    experiment_group: str | None = None,
    category: str = "comparisons",
    create: bool = False,
) -> Path:
    """Return the report directory for a comparison or summary group."""
    report_dir = artifact_root() / "reports" / _normalize_segment(category)
    if experiment_group:
        report_dir = report_dir / _normalize_segment(experiment_group)
    if create:
        report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def build_data_dir(create: bool = False) -> Path:
    """Return the root directory for persisted data artifacts."""
    data_dir = artifact_root() / "data"
    if create:
        data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def build_data_manifest_dir(create: bool = False) -> Path:
    """Return the directory for dataset manifest files."""
    manifest_dir = build_data_dir(create=create) / "manifests"
    if create:
        manifest_dir.mkdir(parents=True, exist_ok=True)
    return manifest_dir


def build_data_summary_dir(create: bool = False) -> Path:
    """Return the directory for dataset validation summaries."""
    summary_dir = build_data_dir(create=create) / "summaries"
    if create:
        summary_dir.mkdir(parents=True, exist_ok=True)
    return summary_dir


def build_data_manifest_path(dataset_name: str) -> Path:
    """Return the canonical manifest path for a dataset."""
    manifest_name = f"{_normalize_segment(dataset_name)}_manifest.json"
    return build_data_manifest_dir(create=True) / manifest_name


def build_prediction_artifact_path(run_dir: Path, split: str) -> Path:
    """Return the canonical prediction artifact path for a split."""
    normalized_split = _normalize_segment(split)
    suffix = _PREDICTION_SPLIT_SUFFIXES.get(normalized_split, normalized_split)
    return run_dir / f"predictions_{suffix}.parquet"


def build_prediction_artifact_paths(run_dir: Path, splits: list[str]) -> dict[str, str]:
    """Return canonical prediction artifact paths keyed by split name."""
    return {
        str(split): str(build_prediction_artifact_path(run_dir, str(split)))
        for split in splits
    }
