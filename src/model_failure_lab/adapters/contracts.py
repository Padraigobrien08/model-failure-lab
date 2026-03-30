"""Shared contracts for provider-backed model adapters."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Protocol, TypeAlias, runtime_checkable

from model_failure_lab.schemas import JsonValue, PayloadValidationError

ModelFactory: TypeAlias = Callable[[], "ModelAdapter"]


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


def _optional_int(payload: Mapping[str, object], key: str) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    if type(value) is not int:
        raise PayloadValidationError(f"{key} must be an integer or null")
    return value


def _optional_number(payload: Mapping[str, object], key: str) -> float | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PayloadValidationError(f"{key} must be a number or null")
    return float(value)


def _optional_json_mapping(payload: Mapping[str, object], key: str) -> dict[str, JsonValue]:
    value = payload.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise PayloadValidationError(f"{key} must be a JSON object")
    validated: dict[str, JsonValue] = {}
    for field_key, field_value in value.items():
        if not isinstance(field_key, str):
            raise PayloadValidationError(f"{key} keys must be strings")
        validated[field_key] = _validate_json_value(field_value, field=f"{key}.{field_key}")
    return validated


@dataclass(slots=True, frozen=True)
class ModelUsage:
    """Normalized token usage data from a model invocation."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {}
        if self.prompt_tokens is not None:
            payload["prompt_tokens"] = self.prompt_tokens
        if self.completion_tokens is not None:
            payload["completion_tokens"] = self.completion_tokens
        if self.total_tokens is not None:
            payload["total_tokens"] = self.total_tokens
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "ModelUsage":
        data = _require_mapping(payload)
        return cls(
            prompt_tokens=_optional_int(data, "prompt_tokens"),
            completion_tokens=_optional_int(data, "completion_tokens"),
            total_tokens=_optional_int(data, "total_tokens"),
        )


@dataclass(slots=True, frozen=True)
class ModelMetadata:
    """Shared model invocation metadata with provider detail contained in `raw`."""

    model: str
    latency_ms: float
    usage: ModelUsage | None = None
    raw: JsonValue | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "model": self.model,
            "latency_ms": self.latency_ms,
        }
        if self.usage is not None:
            payload["usage"] = self.usage.to_payload()
        if self.raw is not None:
            payload["raw"] = _validate_json_value(self.raw, field="raw")
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "ModelMetadata":
        data = _require_mapping(payload)
        usage_payload = data.get("usage")
        raw_payload = data.get("raw")
        return cls(
            model=_require_string(data, "model"),
            latency_ms=_optional_number(data, "latency_ms") or 0.0,
            usage=ModelUsage.from_payload(usage_payload) if usage_payload is not None else None,
            raw=_validate_json_value(raw_payload, field="raw") if raw_payload is not None else None,
        )


@dataclass(slots=True, frozen=True)
class ModelRequest:
    """Shared invocation request understood by all adapters."""

    model: str
    prompt: str
    seed: int | None = None
    system_prompt: str | None = None
    options: dict[str, JsonValue] = field(default_factory=dict)

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "model": self.model,
            "prompt": self.prompt,
            "options": dict(self.options),
        }
        if self.seed is not None:
            payload["seed"] = self.seed
        if self.system_prompt is not None:
            payload["system_prompt"] = self.system_prompt
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "ModelRequest":
        data = _require_mapping(payload)
        return cls(
            model=_require_string(data, "model"),
            prompt=_require_string(data, "prompt"),
            seed=_optional_int(data, "seed"),
            system_prompt=_optional_string(data, "system_prompt"),
            options=_optional_json_mapping(data, "options"),
        )


@dataclass(slots=True, frozen=True)
class ModelResult:
    """Normalized model response returned by every adapter."""

    text: str
    metadata: ModelMetadata | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {"text": self.text}
        if self.metadata is not None:
            payload["metadata"] = self.metadata.to_payload()
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "ModelResult":
        data = _require_mapping(payload)
        metadata = data.get("metadata")
        return cls(
            text=_require_string(data, "text"),
            metadata=ModelMetadata.from_payload(metadata) if metadata is not None else None,
        )


@runtime_checkable
class ModelAdapter(Protocol):
    """Protocol implemented by all model adapters."""

    def generate(self, request: ModelRequest) -> ModelResult:
        """Return a normalized model result for one prompt."""

