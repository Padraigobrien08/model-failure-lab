"""Plain JSON read/write helpers for local failure-analysis artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from model_failure_lab.schemas import JsonValue


def _validate_json_value(value: object) -> JsonValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_validate_json_value(item) for item in value]
    if isinstance(value, dict):
        validated: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
            validated[key] = _validate_json_value(item)
        return validated
    raise ValueError("payload must be JSON-serializable")


def write_json(path: str | Path, payload: dict[str, JsonValue]) -> Path:
    """Write a plain JSON artifact with deterministic formatting."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def read_json(path: str | Path) -> dict[str, JsonValue]:
    """Read a JSON artifact and validate that it is a plain object payload."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("artifact payload must be a JSON object")
    return {
        key: _validate_json_value(value)
        for key, value in payload.items()
        if isinstance(key, str)
    }
