"""Artifact-index helpers for the UI-facing contract."""

from .load import load_artifact_index
from .schema import ARTIFACT_INDEX_SCHEMA_VERSION, DEFAULT_ARTIFACT_INDEX_VERSION


def build_artifact_index_payload(*args, **kwargs):
    """Lazily import the builder to keep lightweight consumers cheap."""
    from .build import build_artifact_index_payload as _build_artifact_index_payload

    return _build_artifact_index_payload(*args, **kwargs)


def write_artifact_index(*args, **kwargs):
    """Lazily import the writer to keep lightweight consumers cheap."""
    from .build import write_artifact_index as _write_artifact_index

    return _write_artifact_index(*args, **kwargs)


def assert_valid_artifact_index_payload(*args, **kwargs):
    """Lazily import validator helpers to avoid heavy package import costs."""
    from .validation import (
        assert_valid_artifact_index_payload as _assert_valid_artifact_index_payload,
    )

    return _assert_valid_artifact_index_payload(*args, **kwargs)


def validate_artifact_index_payload(*args, **kwargs):
    """Lazily import validator helpers to avoid heavy package import costs."""
    from .validation import validate_artifact_index_payload as _validate_artifact_index_payload

    return _validate_artifact_index_payload(*args, **kwargs)

__all__ = [
    "ARTIFACT_INDEX_SCHEMA_VERSION",
    "DEFAULT_ARTIFACT_INDEX_VERSION",
    "assert_valid_artifact_index_payload",
    "build_artifact_index_payload",
    "load_artifact_index",
    "validate_artifact_index_payload",
    "write_artifact_index",
]
