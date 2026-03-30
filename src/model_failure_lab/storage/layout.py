"""Deterministic filesystem layout helpers for failure-analysis artifacts."""

from __future__ import annotations

import re
from pathlib import Path

RUN_FILENAME = "run.json"
RESULTS_FILENAME = "results.json"
REPORT_FILENAME = "report.json"

_INVALID_SEGMENT_PATTERN = re.compile(r"[^a-zA-Z0-9._-]+")


def project_root(root: str | Path | None = None) -> Path:
    """Return the repository root or an explicit storage root for tests."""

    if root is not None:
        return Path(root)
    return Path(__file__).resolve().parents[3]


def _normalize_segment(value: str) -> str:
    normalized = _INVALID_SEGMENT_PATTERN.sub("_", value.strip()).strip("._-").lower()
    if not normalized:
        raise ValueError("artifact identifiers must contain at least one alphanumeric character")
    return normalized


def _ensure_dir(path: Path, *, create: bool) -> Path:
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def datasets_root(*, root: str | Path | None = None, create: bool = False) -> Path:
    return _ensure_dir(project_root(root) / "datasets", create=create)


def runs_root(*, root: str | Path | None = None, create: bool = False) -> Path:
    return _ensure_dir(project_root(root) / "runs", create=create)


def reports_root(*, root: str | Path | None = None, create: bool = False) -> Path:
    return _ensure_dir(project_root(root) / "reports", create=create)


def dataset_file(
    dataset_name: str, *, root: str | Path | None = None, create: bool = False
) -> Path:
    source = Path(dataset_name)
    dataset_id = _normalize_segment(source.stem if source.suffix else source.name)
    return datasets_root(root=root, create=create) / f"{dataset_id}.json"


def run_directory(run_id: str, *, root: str | Path | None = None, create: bool = False) -> Path:
    return _ensure_dir(
        runs_root(root=root, create=create) / _normalize_segment(run_id),
        create=create,
    )


def run_file(run_id: str, *, root: str | Path | None = None, create: bool = False) -> Path:
    return run_directory(run_id, root=root, create=create) / RUN_FILENAME


def results_file(run_id: str, *, root: str | Path | None = None, create: bool = False) -> Path:
    return run_directory(run_id, root=root, create=create) / RESULTS_FILENAME


def report_directory(
    report_id: str, *, root: str | Path | None = None, create: bool = False
) -> Path:
    return _ensure_dir(
        reports_root(root=root, create=create) / _normalize_segment(report_id),
        create=create,
    )


def report_file(report_id: str, *, root: str | Path | None = None, create: bool = False) -> Path:
    return report_directory(report_id, root=root, create=create) / REPORT_FILENAME
