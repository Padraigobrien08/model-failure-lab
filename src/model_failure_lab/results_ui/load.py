"""Manifest loading helpers for the read-only results explorer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from model_failure_lab.artifact_index.load import load_artifact_index
from model_failure_lab.artifact_index.schema import (
    ARTIFACT_INDEX_SCHEMA_VERSION,
    DEFAULT_ARTIFACT_INDEX_VERSION,
)
from model_failure_lab.utils.paths import build_artifact_index_path

DEFAULT_RESULTS_UI_INDEX_VERSION = DEFAULT_ARTIFACT_INDEX_VERSION


def default_results_ui_index_path() -> Path:
    """Return the default manifest path used by the read-only UI."""
    return build_artifact_index_path(version=DEFAULT_RESULTS_UI_INDEX_VERSION)


def load_results_ui_index(path: Path | None = None) -> dict[str, Any]:
    """Load and validate the manifest contract used by the UI."""
    index_path = path or default_results_ui_index_path()
    payload = load_artifact_index(path=index_path, version=DEFAULT_RESULTS_UI_INDEX_VERSION)
    schema_version = payload.get("schema_version")
    if schema_version != ARTIFACT_INDEX_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported artifact index schema for results UI: "
            f"expected {ARTIFACT_INDEX_SCHEMA_VERSION}, got {schema_version!r}"
        )
    return payload
