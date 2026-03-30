from __future__ import annotations

import pytest

from model_failure_lab.adapters import (
    DemoAdapter,
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


def test_demo_adapter_is_registered_by_default() -> None:
    adapter = resolve_model("demo")

    assert isinstance(adapter, DemoAdapter)


def test_demo_adapter_returns_deterministic_results_for_repeat_inputs() -> None:
    adapter = resolve_model("demo")
    request = ModelRequest(
        model="demo-model",
        prompt="Explain why the answer is 42.",
        seed=13,
        options={"temperature": 0},
    )

    first = adapter.generate(request)
    second = adapter.generate(request)

    assert first == second
    assert first.metadata is not None
    assert first.metadata.model == "demo-model"
    assert first.metadata.latency_ms == 0.0


def test_demo_adapter_changes_when_request_seed_changes() -> None:
    adapter = resolve_model("demo")

    first = adapter.generate(ModelRequest(model="demo-model", prompt="Explain 42", seed=13))
    second = adapter.generate(ModelRequest(model="demo-model", prompt="Explain 42", seed=42))

    assert first.text != second.text


def test_resolve_model_rejects_unknown_adapter() -> None:
    with pytest.raises(UnknownModelAdapterError, match="unknown model adapter"):
        resolve_model("missing-adapter")
