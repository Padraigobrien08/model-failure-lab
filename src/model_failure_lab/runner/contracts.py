"""Per-case execution contracts for runner-emitted artifacts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from model_failure_lab.adapters.contracts import ModelResult, ModelUsage
from model_failure_lab.classifiers.contracts import ClassifierExpectations, ClassifierResult
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


def _require_int(payload: Mapping[str, object], key: str) -> int:
    value = payload.get(key)
    if type(value) is not int:
        raise PayloadValidationError(f"{key} must be an integer")
    return value


def _optional_number(payload: Mapping[str, object], key: str) -> float | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PayloadValidationError(f"{key} must be a number or null")
    return float(value)


@dataclass(slots=True, frozen=True)
class PromptSnapshot:
    """Standalone prompt context stored with one case result."""

    id: str
    prompt: str
    expected_failure: str | None = None
    expectations: ClassifierExpectations | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "id": self.id,
            "prompt": self.prompt,
        }
        if self.expected_failure is not None:
            payload["expected_failure"] = self.expected_failure
        if self.expectations is not None:
            payload["expectations"] = self.expectations.to_payload()
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "PromptSnapshot":
        data = _require_mapping(payload)
        expectations = data.get("expectations")
        return cls(
            id=_require_string(data, "id"),
            prompt=_require_string(data, "prompt"),
            expected_failure=_optional_string(data, "expected_failure"),
            expectations=(
                ClassifierExpectations.from_payload(expectations)
                if expectations is not None
                else None
            ),
        )

    @classmethod
    def from_prompt_case(cls, prompt_case: PromptCase) -> "PromptSnapshot":
        metadata = dict(prompt_case.metadata)
        expectation_payload: dict[str, object] = {}
        if isinstance(metadata.get("reference_answer"), str):
            expectation_payload["reference_answer"] = metadata["reference_answer"]
        if isinstance(metadata.get("rubric"), (str, list)):
            expectation_payload["rubric"] = metadata["rubric"]
        if isinstance(metadata.get("constraints"), list):
            expectation_payload["constraints"] = metadata["constraints"]

        expectations = (
            ClassifierExpectations.from_payload(expectation_payload)
            if expectation_payload
            else None
        )
        return cls(
            id=prompt_case.id,
            prompt=prompt_case.prompt,
            expected_failure=prompt_case.expected_failure,
            expectations=expectations,
        )


@dataclass(slots=True, frozen=True)
class ExecutionMetadata:
    """Compact execution metadata stored with one case result."""

    adapter_id: str
    model: str
    classifier_id: str
    run_seed: int
    case_seed: int
    latency_ms: float | None = None
    usage: ModelUsage | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "adapter_id": self.adapter_id,
            "model": self.model,
            "classifier_id": self.classifier_id,
            "run_seed": self.run_seed,
            "case_seed": self.case_seed,
        }
        if self.latency_ms is not None:
            payload["latency_ms"] = self.latency_ms
        if self.usage is not None:
            payload["usage"] = self.usage.to_payload()
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "ExecutionMetadata":
        data = _require_mapping(payload)
        usage = data.get("usage")
        return cls(
            adapter_id=_require_string(data, "adapter_id"),
            model=_require_string(data, "model"),
            classifier_id=_require_string(data, "classifier_id"),
            run_seed=_require_int(data, "run_seed"),
            case_seed=_require_int(data, "case_seed"),
            latency_ms=_optional_number(data, "latency_ms"),
            usage=ModelUsage.from_payload(usage) if usage is not None else None,
        )

    @classmethod
    def from_model_result(
        cls,
        *,
        adapter_id: str,
        classifier_id: str,
        run_seed: int,
        case_seed: int,
        result: ModelResult,
    ) -> "ExecutionMetadata":
        metadata = result.metadata
        return cls(
            adapter_id=adapter_id,
            model=metadata.model if metadata is not None else "unknown",
            classifier_id=classifier_id,
            run_seed=run_seed,
            case_seed=case_seed,
            latency_ms=metadata.latency_ms if metadata is not None else None,
            usage=metadata.usage if metadata is not None else None,
        )


@dataclass(slots=True, frozen=True)
class CaseOutput:
    """Model output snapshot stored with one case result."""

    text: str

    def to_payload(self) -> dict[str, JsonValue]:
        return {"text": self.text}

    @classmethod
    def from_payload(cls, payload: object) -> "CaseOutput":
        data = _require_mapping(payload)
        return cls(text=_require_string(data, "text"))

    @classmethod
    def from_model_result(cls, result: ModelResult) -> "CaseOutput":
        return cls(text=result.text)


@dataclass(slots=True, frozen=True)
class CaseClassification:
    """Normalized classification stored with one case result."""

    failure_type: str
    confidence: float | None = None
    explanation: str | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {"failure_type": self.failure_type}
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        if self.explanation is not None:
            payload["explanation"] = self.explanation
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "CaseClassification":
        data = _require_mapping(payload)
        return cls(
            failure_type=_require_string(data, "failure_type"),
            confidence=_optional_number(data, "confidence"),
            explanation=_optional_string(data, "explanation"),
        )

    @classmethod
    def from_classifier_result(cls, result: ClassifierResult) -> "CaseClassification":
        return cls(
            failure_type=result.failure_type,
            confidence=result.confidence,
            explanation=result.explanation,
        )


@dataclass(slots=True, frozen=True)
class CaseError:
    """Structured per-case error payload recorded by the runner."""

    stage: str
    type: str
    message: str

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "stage": self.stage,
            "type": self.type,
            "message": self.message,
        }

    @classmethod
    def from_payload(cls, payload: object) -> "CaseError":
        data = _require_mapping(payload)
        return cls(
            stage=_require_string(data, "stage"),
            type=_require_string(data, "type"),
            message=_require_string(data, "message"),
        )

    @classmethod
    def from_exception(cls, *, stage: str, exc: Exception) -> "CaseError":
        return cls(stage=stage, type=exc.__class__.__name__, message=str(exc))


@dataclass(slots=True, frozen=True)
class CaseExecution:
    """Standalone-inspectable per-case result record."""

    case_id: str
    prompt: PromptSnapshot
    execution: ExecutionMetadata
    output: CaseOutput | None = None
    classification: CaseClassification | None = None
    error: CaseError | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "case_id": self.case_id,
            "prompt": self.prompt.to_payload(),
            "execution": self.execution.to_payload(),
            "error": self.error.to_payload() if self.error is not None else None,
        }
        payload["output"] = self.output.to_payload() if self.output is not None else None
        payload["classification"] = (
            self.classification.to_payload() if self.classification is not None else None
        )
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "CaseExecution":
        data = _require_mapping(payload)
        output = data.get("output")
        classification = data.get("classification")
        error = data.get("error")
        return cls(
            case_id=_require_string(data, "case_id"),
            prompt=PromptSnapshot.from_payload(data.get("prompt")),
            execution=ExecutionMetadata.from_payload(data.get("execution")),
            output=CaseOutput.from_payload(output) if output is not None else None,
            classification=(
                CaseClassification.from_payload(classification)
                if classification is not None
                else None
            ),
            error=CaseError.from_payload(error) if error is not None else None,
        )
