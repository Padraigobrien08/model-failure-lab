"""Canonical failure-analysis entity contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, TypeAlias

from .taxonomy import FailureLabel

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


def _optional_string_tuple(payload: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = payload.get(key)
    if value is None:
        return ()
    if isinstance(value, str):
        if not value.strip():
            raise PayloadValidationError(f"{key} must be non-empty")
        return (value,)
    if not isinstance(value, list):
        raise PayloadValidationError(f"{key} must be a string or list of strings")
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


@dataclass(slots=True, frozen=True)
class PromptContextExpectations:
    """Optional grounding/context expectations authored with a prompt case."""

    context: str | None = None
    evidence_items: tuple[str, ...] = ()
    required_sources: tuple[str, ...] = ()
    grounding_notes: str | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {}
        if self.context is not None:
            payload["context"] = self.context
        if self.evidence_items:
            payload["evidence_items"] = _json_list(self.evidence_items)
        if self.required_sources:
            payload["required_sources"] = _json_list(self.required_sources)
        if self.grounding_notes is not None:
            payload["grounding_notes"] = self.grounding_notes
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "PromptContextExpectations":
        data = _require_mapping(payload)
        return cls(
            context=_optional_string(data, "context"),
            evidence_items=_optional_string_tuple(data, "evidence_items"),
            required_sources=_optional_string_tuple(data, "required_sources"),
            grounding_notes=_optional_string(data, "grounding_notes"),
        )

    def is_empty(self) -> bool:
        return (
            self.context is None
            and not self.evidence_items
            and not self.required_sources
            and self.grounding_notes is None
        )


@dataclass(slots=True, frozen=True)
class PromptExpectations:
    """Canonical authored expectations stored on a prompt case."""

    expected_failure: str | None = None
    expected_failure_subtype: str | None = None
    reference_answer: str | None = None
    rubric: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    context: PromptContextExpectations | None = None

    def __post_init__(self) -> None:
        if self.expected_failure is None:
            if self.expected_failure_subtype is not None:
                raise ValueError(
                    "expected_failure_subtype requires expected_failure to be set"
                )
            return
        label = FailureLabel(
            failure_type=self.expected_failure,
            failure_subtype=self.expected_failure_subtype,
        )
        object.__setattr__(self, "expected_failure", label.failure_type)
        object.__setattr__(self, "expected_failure_subtype", label.failure_subtype)

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {}
        if self.expected_failure is not None:
            payload["expected_failure"] = self.expected_failure
        if self.expected_failure_subtype is not None:
            payload["expected_failure_subtype"] = self.expected_failure_subtype
        if self.reference_answer is not None:
            payload["reference_answer"] = self.reference_answer
        if self.rubric:
            payload["rubric"] = _json_list(self.rubric)
        if self.constraints:
            payload["constraints"] = _json_list(self.constraints)
        if self.context is not None and not self.context.is_empty():
            payload["context"] = self.context.to_payload()
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "PromptExpectations":
        data = _require_mapping(payload)
        context = data.get("context")
        expected_failure = data.get("expected_failure")
        expected_failure_subtype = data.get("expected_failure_subtype")
        if isinstance(expected_failure, Mapping):
            try:
                expected_label = FailureLabel.from_payload(expected_failure)
            except ValueError as exc:
                raise PayloadValidationError(str(exc)) from exc
            expected_failure = expected_label.failure_type
            expected_failure_subtype = expected_label.failure_subtype
        return cls(
            expected_failure=(
                expected_failure
                if isinstance(expected_failure, str)
                else _optional_string(data, "expected_failure")
            ),
            expected_failure_subtype=(
                expected_failure_subtype
                if isinstance(expected_failure_subtype, str) or expected_failure_subtype is None
                else _optional_string(data, "expected_failure_subtype")
            ),
            reference_answer=_optional_string(data, "reference_answer"),
            rubric=_optional_string_tuple(data, "rubric"),
            constraints=_optional_string_tuple(data, "constraints"),
            context=(
                PromptContextExpectations.from_payload(context)
                if context is not None
                else None
            ),
        )

    def to_classifier_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {}
        if self.reference_answer is not None:
            payload["reference_answer"] = self.reference_answer
        if self.rubric:
            payload["rubric"] = _json_list(self.rubric)
        if self.constraints:
            payload["constraints"] = _json_list(self.constraints)
        if self.context is not None and not self.context.is_empty():
            if self.context.context is not None:
                payload["context"] = self.context.context
            if self.context.evidence_items:
                payload["evidence_items"] = _json_list(self.context.evidence_items)
            if self.context.required_sources:
                payload["required_sources"] = _json_list(self.context.required_sources)
            if self.context.grounding_notes is not None:
                payload["grounding_notes"] = self.context.grounding_notes
        return payload

    def is_empty(self) -> bool:
        return (
            self.expected_failure is None
            and self.expected_failure_subtype is None
            and self.reference_answer is None
            and not self.rubric
            and not self.constraints
            and (self.context is None or self.context.is_empty())
        )

    def to_failure_label(self) -> FailureLabel | None:
        if self.expected_failure is None:
            return None
        return FailureLabel(
            failure_type=self.expected_failure,
            failure_subtype=self.expected_failure_subtype,
        )


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
    tags: tuple[str, ...] = ()
    expectations: PromptExpectations | None = None
    metadata: dict[str, JsonValue] = field(default_factory=dict)

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "id": self.id,
            "prompt": self.prompt,
            "tags": _json_list(self.tags),
            "metadata": dict(self.metadata),
        }
        if self.expectations is not None and not self.expectations.is_empty():
            payload["expectations"] = self.expectations.to_payload()
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "PromptCase":
        data = _require_mapping(payload)
        metadata = _optional_json_mapping(data, "metadata")
        expectations = _build_prompt_expectations(data, metadata=metadata)
        return cls(
            id=_require_string(data, "id"),
            prompt=_require_string(data, "prompt"),
            tags=_require_string_tuple(data, "tags"),
            expectations=expectations,
            metadata=metadata,
        )


_LEGACY_EXPECTATION_METADATA_KEYS = {
    "reference_answer",
    "rubric",
    "constraints",
    "context",
    "evidence_items",
    "required_sources",
    "grounding_notes",
}


def _build_prompt_expectations(
    payload: Mapping[str, object],
    *,
    metadata: dict[str, JsonValue],
) -> PromptExpectations | None:
    explicit_expectations = payload.get("expectations")
    if explicit_expectations is not None:
        return PromptExpectations.from_payload(explicit_expectations)

    legacy_context = _legacy_context_payload(metadata)
    legacy_payload: dict[str, object] = {}
    expected_failure = _optional_string(payload, "expected_failure")
    if expected_failure is not None:
        legacy_payload["expected_failure"] = expected_failure
    if isinstance(metadata.get("reference_answer"), str):
        legacy_payload["reference_answer"] = metadata["reference_answer"]
    if "rubric" in metadata:
        legacy_payload["rubric"] = metadata["rubric"]
    if "constraints" in metadata:
        legacy_payload["constraints"] = metadata["constraints"]
    if legacy_context is not None:
        legacy_payload["context"] = legacy_context

    for key in _LEGACY_EXPECTATION_METADATA_KEYS:
        metadata.pop(key, None)

    if not legacy_payload:
        return None
    return PromptExpectations.from_payload(legacy_payload)


def _legacy_context_payload(metadata: Mapping[str, JsonValue]) -> dict[str, JsonValue] | None:
    legacy_payload: dict[str, JsonValue] = {}
    context_value = metadata.get("context")
    if isinstance(context_value, str) and context_value.strip():
        legacy_payload["context"] = context_value
    elif isinstance(context_value, dict):
        if context_value:
            legacy_payload.update(context_value)
    evidence_items = metadata.get("evidence_items")
    if isinstance(evidence_items, list):
        legacy_payload["evidence_items"] = evidence_items
    required_sources = metadata.get("required_sources")
    if isinstance(required_sources, list):
        legacy_payload["required_sources"] = required_sources
    grounding_notes = metadata.get("grounding_notes")
    if isinstance(grounding_notes, str) and grounding_notes.strip():
        legacy_payload["grounding_notes"] = grounding_notes
    return legacy_payload or None


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
    failure_subtype: str | None = None
    score: float | None = None
    confidence: float | None = None
    explanation: str | None = None
    metadata: dict[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        label = FailureLabel(
            failure_type=self.failure_type,
            failure_subtype=self.failure_subtype,
        )
        object.__setattr__(self, "failure_type", label.failure_type)
        object.__setattr__(self, "failure_subtype", label.failure_subtype)

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "prompt_id": self.prompt_id,
            "output": self.output,
            "failure_type": self.failure_type,
            "score": self.score,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "metadata": dict(self.metadata),
        }
        if self.failure_subtype is not None:
            payload["failure_subtype"] = self.failure_subtype
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "Result":
        data = _require_mapping(payload)
        return cls(
            prompt_id=_require_string(data, "prompt_id"),
            output=_require_string(data, "output"),
            failure_type=_require_string(data, "failure_type"),
            failure_subtype=_optional_string(data, "failure_subtype"),
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
