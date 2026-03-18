"""Result contracts returned by thin runner dispatch functions."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DispatchResult:
    """Structured result for scaffolded command entrypoints."""

    status: str
    message: str
    run_dir: Path
    metadata_path: Path
    metrics_path: Path | None = None
    preset_name: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)
