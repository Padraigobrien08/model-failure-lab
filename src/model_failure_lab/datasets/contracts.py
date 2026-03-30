"""Normalized dataset contracts for prompt-case execution."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from model_failure_lab.schemas import JsonValue, PayloadValidationError, PromptCase


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


def _optional_json_mapping(payload: Mapping[str, object], key: str) -> dict[str, JsonValue]:
    value = payload.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise PayloadValidationError(f"{key} must be a JSON object")
    metadata: dict[str, JsonValue] = {}
    for field_key, field_value in value.items():
        if not isinstance(field_key, str):
            raise PayloadValidationError(f"{key} keys must be strings")
        if value is None or isinstance(field_value, (str, int, float, bool)):
            metadata[field_key] = field_value
        elif isinstance(field_value, list):
            metadata[field_key] = field_value
        elif isinstance(field_value, dict):
            metadata[field_key] = field_value
        else:
            raise PayloadValidationError(f"{key}.{field_key} must be JSON-serializable")
    return metadata


def _require_cases(payload: Mapping[str, object], key: str) -> tuple[PromptCase, ...]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise PayloadValidationError(f"{key} must be a list of prompt cases")
    return tuple(PromptCase.from_payload(item) for item in value)


@dataclass(slots=True, frozen=True)
class FailureDataset:
    """Canonical normalized dataset envelope used by the runner."""

    dataset_id: str
    name: str | None = None
    description: str | None = None
    version: str | None = None
    cases: tuple[PromptCase, ...] = ()
    metadata: dict[str, JsonValue] = field(default_factory=dict)

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "dataset_id": self.dataset_id,
            "cases": [case.to_payload() for case in self.cases],
        }
        if self.name is not None:
            payload["name"] = self.name
        if self.description is not None:
            payload["description"] = self.description
        if self.version is not None:
            payload["version"] = self.version
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "FailureDataset":
        data = _require_mapping(payload)
        return cls(
            dataset_id=_require_string(data, "dataset_id"),
            name=_optional_string(data, "name"),
            description=_optional_string(data, "description"),
            version=_optional_string(data, "version"),
            cases=_require_cases(data, "cases"),
            metadata=_optional_json_mapping(data, "metadata"),
        )
