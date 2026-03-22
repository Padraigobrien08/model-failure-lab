"""Load helpers for the generated artifact-index contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from model_failure_lab.utils.paths import build_artifact_index_path


def load_artifact_index(path: Path | None = None, *, version: str = "v1") -> dict[str, Any]:
    """Load the generated artifact-index payload."""
    index_path = path or build_artifact_index_path(version=version)
    return json.loads(index_path.read_text(encoding="utf-8"))
