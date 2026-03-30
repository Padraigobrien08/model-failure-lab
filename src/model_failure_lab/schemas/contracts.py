"""Canonical failure-analysis entity contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


class PayloadValidationError(ValueError):
    """Raised when a canonical artifact payload is malformed."""


def _json_list(values: tuple[str, ...]) -> list[str]:
    return list(values)


def _validate_json_value(value: object, *, field: str) -> JsonValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_validate_json_value(item, field=field) for item in value]
    if isinstance(value, dict):
        validated: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise PayloadValidationError(f"{field} keys must be strings")
            validated[key] = _validate_json_value(item, field=f"{field}.{key}")
        return validated
    raise PayloadValidationError(f"{field} must be JSON-serializable")


def _require_mapping(payload: object) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise PayloadValidationError("payload must be a mapping")
    return payload


def _require_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PayloadValidationError(f"{key} must be a non-empty string")
    return value


def _optional_string(payload: Mapping[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise PayloadValidationError(f"{key} must be a non-empty string or null")
    return value


def _require_string_tuple(payload: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = payload.get(key)
    if value is None:
        return ()
    if not isinstance(value, list):
        raise PayloadValidationError(f"{key} must be a list of strings")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise PayloadValidationError(f"{key} entries must be non-empty strings")
        items.append(item)
    return tuple(items)


def _optional_json_mapping(payload: Mapping[str, object], key: str) -> dict[str, JsonValue]:
    value = payload.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise PayloadValidationError(f"{key} must be a JSON object")
    return {
        field_key: _validate_json_value(field_value, field=f"{key}.{field_key}")
        for field_key, field_value in value.items()
        if isinstance(field_key, str)
    }


def _optional_number(payload: Mapping[str, object], key: str) -> float | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PayloadValidationError(f"{key} must be a number or null")
    return float(value)


def _require_int(payload: Mapping[str, object], key: str) -> int:
    value = payload.get(key)
    if type(value) is not int:
        raise PayloadValidationError(f"{key} must be an integer")
    return value


def _require_int_mapping(payload: Mapping[str, object], key: str) -> dict[str, int]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise PayloadValidationError(f"{key} must be an object of integer counts")
    validated: dict[str, int] = {}
    for field_key, field_value in value.items():
        if not isinstance(field_key, str) or type(field_value) is not int:
            raise PayloadValidationError(f"{key} must map strings to integers")
        validated[field_key] = field_value
    return validated


def _require_float_mapping(payload: Mapping[str, object], key: str) -> dict[str, float]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise PayloadValidationError(f"{key} must be an object of numeric rates")
    validated: dict[str, float] = {}
    for field_key, field_value in value.items():
        if not isinstance(field_key, str) or isinstance(field_value, bool) or not isinstance(
            field_value, (int, float)
        ):
            raise PayloadValidationError(f"{key} must map strings to numeric rates")
        validated[field_key] = float(field_value)
    return validated


@dataclass(slots=True, frozen=True)
class PromptCase:
    """Tracked prompt input for a failure-analysis run."""

    id: str
    prompt: str
    expected_failure: str | None = None
    tags: tuple[str, ...] = ()
    metadata: dict[str, JsonValue] = field(default_factory=dict)

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "expected_failure": self.expected_failure,
            "tags": _json_list(self.tags),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_payload(cls, payload: object) -> "PromptCase":
        data = _require_mapping(payload)
        return cls(
            id=_require_string(data, "id"),
            prompt=_require_string(data, "prompt"),
            expected_failure=_optional_string(data, "expected_failure"),
            tags=_require_string_tuple(data, "tags"),
            metadata=_optional_json_mapping(data, "metadata"),
        )


@dataclass(slots=True, frozen=True)
class Run:
    """Top-level execution record for one model and dataset combination."""

    run_id: str
    model: str
    dataset: str
    created_at: str
    config: dict[str, JsonValue] = field(default_factory=dict)
    metadata: dict[str, JsonValue] = field(default_factory=dict)

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "run_id": self.run_id,
            "model": self.model,
            "dataset": self.dataset,
            "created_at": self.created_at,
            "config": dict(self.config),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_payload(cls, payload: object) -> "Run":
        data = _require_mapping(payload)
        return cls(
            run_id=_require_string(data, "run_id"),
            model=_require_string(data, "model"),
            dataset=_require_string(data, "dataset"),
            created_at=_require_string(data, "created_at"),
            config=_optional_json_mapping(data, "config"),
            metadata=_optional_json_mapping(data, "metadata"),
        )


@dataclass(slots=True, frozen=True)
class Result:
    """Per-prompt output classification recorded within a run."""

    prompt_id: str
    output: str
    failure_type: str
    score: float | None = None
    confidence: float | None = None
    explanation: str | None = None
    metadata: dict[str, JsonValue] = field(default_factory=dict)

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "prompt_id": self.prompt_id,
            "output": self.output,
            "failure_type": self.failure_type,
            "score": self.score,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_payload(cls, payload: object) -> "Result":
        data = _require_mapping(payload)
        return cls(
            prompt_id=_require_string(data, "prompt_id"),
            output=_require_string(data, "output"),
            failure_type=_require_string(data, "failure_type"),
            score=_optional_number(data, "score"),
            confidence=_optional_number(data, "confidence"),
            explanation=_optional_string(data, "explanation"),
            metadata=_optional_json_mapping(data, "metadata"),
        )


@dataclass(slots=True, frozen=True)
class Report:
    """Aggregate summary for one or more saved runs."""

    report_id: str
    run_ids: tuple[str, ...]
    created_at: str
    total_cases: int
    failure_counts: dict[str, int]
    failure_rates: dict[str, float]
    comparison: dict[str, JsonValue] = field(default_factory=dict)
    metrics: dict[str, JsonValue] = field(default_factory=dict)
    status: dict[str, JsonValue] = field(default_factory=dict)
    metadata: dict[str, JsonValue] = field(default_factory=dict)

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "report_id": self.report_id,
            "run_ids": _json_list(self.run_ids),
            "created_at": self.created_at,
            "total_cases": self.total_cases,
            "failure_counts": dict(self.failure_counts),
            "failure_rates": dict(self.failure_rates),
        }
        if self.comparison:
            payload["comparison"] = dict(self.comparison)
        if self.metrics:
            payload["metrics"] = dict(self.metrics)
        if self.status:
            payload["status"] = dict(self.status)
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "Report":
        data = _require_mapping(payload)
        return cls(
            report_id=_require_string(data, "report_id"),
            run_ids=_require_string_tuple(data, "run_ids"),
            created_at=_require_string(data, "created_at"),
            total_cases=_require_int(data, "total_cases"),
            failure_counts=_require_int_mapping(data, "failure_counts"),
            failure_rates=_require_float_mapping(data, "failure_rates"),
            comparison=_optional_json_mapping(data, "comparison"),
            metrics=_optional_json_mapping(data, "metrics"),
            status=_optional_json_mapping(data, "status"),
            metadata=_optional_json_mapping(data, "metadata"),
        )
