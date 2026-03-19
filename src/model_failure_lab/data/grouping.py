"""CivilComments subgroup normalization helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _coerce_binary_value(field_name: str, value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value >= 0.5)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes"}:
            return 1
        if normalized in {"0", "false", "no", ""}:
            return 0
    raise ValueError(f"Unsupported subgroup value for {field_name}: {value!r}")


def build_group_attributes(record: dict[str, Any], data_config: dict[str, Any]) -> dict[str, int]:
    """Extract identity and auxiliary metadata into one stable subgroup payload."""
    group_attributes: dict[str, int] = {}
    for field_name in data_config["group_fields"]:
        if field_name not in record:
            raise ValueError(f"Missing required subgroup field: {field_name}")
        group_attributes[field_name] = _coerce_binary_value(field_name, record[field_name])
    for field_name in data_config.get("auxiliary_fields", []):
        if field_name in record:
            group_attributes[field_name] = _coerce_binary_value(field_name, record[field_name])
    return group_attributes


def build_group_id(group_attributes: dict[str, int]) -> str:
    """Build a deterministic subgroup identifier from the normalized attributes."""
    serialized = json.dumps(group_attributes, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha1(serialized.encode("utf-8")).hexdigest()[:12]
    return f"group_{digest}"
