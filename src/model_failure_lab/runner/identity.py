"""Deterministic run identity and per-case seed helpers."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

_SEGMENT_PATTERN = re.compile(r"[^a-z0-9]+")
_MAX_CASE_SEED = 2**31


def _normalize_segment(value: str) -> str:
    normalized = _SEGMENT_PATTERN.sub("_", value.strip().lower()).strip("_")
    return normalized or "run"


def derive_case_seed(
    *,
    run_seed: int,
    dataset_id: str,
    case_id: str,
    adapter_id: str,
) -> int:
    """Derive one deterministic, order-independent seed for a prompt case."""

    digest = hashlib.sha256(
        f"{run_seed}:{dataset_id}:{case_id}:{adapter_id}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False) % _MAX_CASE_SEED


def build_run_id(
    *,
    dataset_id: str,
    adapter_id: str,
    classifier_id: str,
    run_seed: int,
    now: datetime | None = None,
) -> str:
    """Build a readable run ID without random suffixes."""

    current_time = now or datetime.now(timezone.utc)
    timestamp = current_time.strftime("%Y%m%d_%H%M%S")
    slug = "_".join(
        [
            _normalize_segment(dataset_id),
            _normalize_segment(adapter_id),
            _normalize_segment(classifier_id),
        ]
    )
    digest = hashlib.sha256(
        f"{dataset_id}:{adapter_id}:{classifier_id}:{run_seed}".encode("utf-8")
    ).hexdigest()[:6]
    return f"{timestamp}_{slug}_seed_{run_seed}_{digest}"
