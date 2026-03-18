"""Run ID generation for local experiment bundles."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import uuid4

_SEGMENT_PATTERN = re.compile(r"[^a-z0-9]+")


def _normalize_segment(value: str) -> str:
    normalized = _SEGMENT_PATTERN.sub("_", value.strip().lower()).strip("_")
    return normalized or "run"


def generate_run_id(
    prefix: str,
    now: datetime | None = None,
    suffix: str | None = None,
) -> str:
    """Format run IDs as timestamp + prefix + short suffix."""
    current_time = now or datetime.now(timezone.utc)
    formatted_time = current_time.strftime("%Y%m%d_%H%M%S")
    normalized_prefix = _normalize_segment(prefix)
    normalized_suffix = _normalize_segment(suffix or uuid4().hex[:4])
    return f"{formatted_time}_{normalized_prefix}_{normalized_suffix}"
