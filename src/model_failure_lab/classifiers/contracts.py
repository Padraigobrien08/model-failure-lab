"""Shared contracts for deterministic failure classifiers."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TypeAlias

from model_failure_lab.adapters.contracts import ModelResult
from model_failure_lab.schemas import (
    FailureLabel,
    JsonValue,
    PayloadValidationError,
)

Classifier: TypeAlias = Callable[["ClassifierInput"], "ClassifierResult"]


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


def _optional_number(payload: Mapping[str, object], key: str) -> float | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PayloadValidationError(f"{key} must be a number or null")
    return float(value)


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


@dataclass(slots=True, frozen=True)
class ClassifierExpectations:
    """Authored expectations that make heuristic classification more useful."""

    reference_answer: str | None = None
    rubric: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    context: str | None = None
    evidence_items: tuple[str, ...] = ()
    required_sources: tuple[str, ...] = ()
    grounding_notes: str | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {}
        if self.reference_answer is not None:
            payload["reference_answer"] = self.reference_answer
        if self.rubric:
            payload["rubric"] = list(self.rubric)
        if self.constraints:
            payload["constraints"] = list(self.constraints)
        if self.context is not None:
            payload["context"] = self.context
        if self.evidence_items:
            payload["evidence_items"] = list(self.evidence_items)
        if self.required_sources:
            payload["required_sources"] = list(self.required_sources)
        if self.grounding_notes is not None:
            payload["grounding_notes"] = self.grounding_notes
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "ClassifierExpectations":
        data = _require_mapping(payload)
        return cls(
            reference_answer=_optional_string(data, "reference_answer"),
            rubric=_optional_string_tuple(data, "rubric"),
            constraints=_optional_string_tuple(data, "constraints"),
            context=_optional_string(data, "context"),
            evidence_items=_optional_string_tuple(data, "evidence_items"),
            required_sources=_optional_string_tuple(data, "required_sources"),
            grounding_notes=_optional_string(data, "grounding_notes"),
        )


@dataclass(slots=True, frozen=True)
class ClassifierInput:
    """Pure classifier input composed of one model output plus optional expectations."""

    output: ModelResult
    expectations: ClassifierExpectations | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {"output": self.output.to_payload()}
        if self.expectations is not None:
            payload["expectations"] = self.expectations.to_payload()
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "ClassifierInput":
        data = _require_mapping(payload)
        expectations = data.get("expectations")
        return cls(
            output=ModelResult.from_payload(data.get("output")),
            expectations=(
                ClassifierExpectations.from_payload(expectations)
                if expectations is not None
                else None
            ),
        )


@dataclass(slots=True, frozen=True)
class ClassifierResult:
    """Normalized classifier output for one model result."""

    failure_type: str
    failure_subtype: str | None = None
    confidence: float | None = None
    explanation: str | None = None

    def __post_init__(self) -> None:
        try:
            label = FailureLabel(
                failure_type=self.failure_type,
                failure_subtype=self.failure_subtype,
            )
        except ValueError as exc:
            raise PayloadValidationError(str(exc)) from exc
        object.__setattr__(self, "failure_type", label.failure_type)
        object.__setattr__(self, "failure_subtype", label.failure_subtype)

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {"failure_type": self.failure_type}
        if self.failure_subtype is not None:
            payload["failure_subtype"] = self.failure_subtype
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        if self.explanation is not None:
            payload["explanation"] = self.explanation
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "ClassifierResult":
        data = _require_mapping(payload)
        return cls(
            failure_type=_require_string(data, "failure_type"),
            failure_subtype=_optional_string(data, "failure_subtype"),
            confidence=_optional_number(data, "confidence"),
            explanation=_optional_string(data, "explanation"),
        )
