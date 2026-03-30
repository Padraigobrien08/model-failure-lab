from __future__ import annotations

import pytest

from model_failure_lab.adapters import (
    ModelMetadata,
    ModelRequest,
    ModelResult,
    ModelUsage,
    UnknownModelAdapterError,
    register_model,
    resolve_model,
)


class StubAdapter:
    def generate(self, request: ModelRequest) -> ModelResult:
        return ModelResult(
            text=f"stub:{request.prompt}",
            metadata=ModelMetadata(
                model=request.model,
                latency_ms=1.5,
                usage=ModelUsage(prompt_tokens=3, completion_tokens=4, total_tokens=7),
            ),
        )


def test_model_result_round_trips_with_optional_metadata() -> None:
    result = ModelResult(
        text="Answer",
        metadata=ModelMetadata(
            model="demo-model",
            latency_ms=2.0,
            usage=ModelUsage(prompt_tokens=1, completion_tokens=2, total_tokens=3),
            raw={"id": "resp_123"},
        ),
    )

    assert ModelResult.from_payload(result.to_payload()) == result


def test_model_result_round_trips_without_metadata() -> None:
    result = ModelResult(text="Answer")

    assert result.to_payload() == {"text": "Answer"}
    assert ModelResult.from_payload(result.to_payload()) == result


def test_register_model_resolves_named_adapter() -> None:
    register_model("unit-test-stub-adapter", StubAdapter)

    adapter = resolve_model("unit-test-stub-adapter")
    result = adapter.generate(ModelRequest(model="demo-model", prompt="Solve this"))

    assert result.text == "stub:Solve this"
    assert result.metadata is not None
    assert result.metadata.usage is not None
    assert result.metadata.usage.total_tokens == 7


def test_resolve_model_rejects_unknown_adapter() -> None:
    with pytest.raises(UnknownModelAdapterError, match="unknown model adapter"):
        resolve_model("missing-adapter")
