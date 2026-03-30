"""Dataset JSON loading with list and envelope compatibility."""

from __future__ import annotations

import json
import re
from pathlib import Path

from model_failure_lab.schemas import PayloadValidationError, PromptCase

from .contracts import FailureDataset

_SEGMENT_PATTERN = re.compile(r"[^a-z0-9]+")


def _normalize_dataset_id(value: str) -> str:
    normalized = _SEGMENT_PATTERN.sub("-", value.strip().lower()).strip("-")
    if not normalized:
        raise PayloadValidationError("dataset_id must contain at least one alphanumeric character")
    return normalized


def load_dataset(path: str | Path) -> FailureDataset:
    """Load one dataset JSON file into the normalized dataset contract."""

    source_path = Path(path)
    raw_payload = json.loads(source_path.read_text(encoding="utf-8"))
    return parse_dataset_payload(raw_payload, fallback_dataset_id=source_path.stem)


def parse_dataset_payload(
    payload: object,
    *,
    fallback_dataset_id: str | None = None,
) -> FailureDataset:
    """Parse either a bare prompt-case list or a canonical dataset envelope."""

    if isinstance(payload, list):
        dataset_id = _normalize_dataset_id(fallback_dataset_id or "dataset")
        dataset_name_source = fallback_dataset_id or dataset_id
        dataset_name = dataset_name_source.replace("_", " ").replace("-", " ").title()
        return FailureDataset(
            dataset_id=dataset_id,
            name=dataset_name,
            cases=tuple(PromptCase.from_payload(item) for item in payload),
        )

    if isinstance(payload, dict):
        if "cases" not in payload:
            raise PayloadValidationError("dataset envelope must contain cases")
        return FailureDataset.from_payload(payload)

    raise PayloadValidationError("dataset payload must be a list or an object with cases")
