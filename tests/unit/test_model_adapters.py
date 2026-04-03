from __future__ import annotations

from urllib.error import URLError

import pytest

from model_failure_lab.adapters import (
    DemoAdapter,
    ModelMetadata,
    ModelRequest,
    ModelResult,
    ModelUsage,
    OllamaAdapter,
    OpenAIAdapter,
    UnknownModelAdapterError,
    available_models,
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


class FakeClock:
    def __init__(self, *values: float) -> None:
        self._values = list(values)

    def __call__(self) -> float:
        return self._values.pop(0)


class FakeUsage:
    def __init__(self, prompt_tokens: int, completion_tokens: int, total_tokens: int) -> None:
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens


class FakeResponse:
    def __init__(self) -> None:
        self.output_text = "Provider answer"
        self.usage = FakeUsage(prompt_tokens=11, completion_tokens=7, total_tokens=18)
        self.id = "resp_123"
        self.status = "completed"

    def model_dump(self) -> dict[str, object]:
        return {
            "id": self.id,
            "object": "response",
            "status": self.status,
            "output_text": self.output_text,
            "usage": {
                "prompt_tokens": self.usage.prompt_tokens,
                "completion_tokens": self.usage.completion_tokens,
                "total_tokens": self.usage.total_tokens,
            },
            "ignored": "trim me",
        }


class FakeResponsesAPI:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> FakeResponse:
        self.calls.append(kwargs)
        return FakeResponse()


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.responses = FakeResponsesAPI()


class CapturingOllamaTransport:
    def __init__(self, response: dict[str, object]) -> None:
        self._response = response
        self.calls: list[dict[str, object]] = []

    def __call__(
        self,
        base_url: str,
        payload: dict[str, object],
        timeout_seconds: float | None,
    ) -> dict[str, object]:
        self.calls.append(
            {
                "base_url": base_url,
                "payload": payload,
                "timeout_seconds": timeout_seconds,
            }
        )
        return dict(self._response)


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


def test_ollama_adapter_is_registered_by_default() -> None:
    adapter = resolve_model("ollama")

    assert "ollama" in available_models()
    assert isinstance(adapter, OllamaAdapter)


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


def test_openai_adapter_shapes_provider_response_without_network() -> None:
    client = FakeOpenAIClient()
    adapter = OpenAIAdapter(client=client, clock=FakeClock(10.0, 10.25))

    result = adapter.generate(
        ModelRequest(
            model="gpt-4.1-mini",
            prompt="Answer the question.",
            system_prompt="Be concise.",
            seed=7,
            options={"temperature": 0, "max_output_tokens": 64},
        )
    )

    assert client.responses.calls == [
        {
            "model": "gpt-4.1-mini",
            "input": [
                {"role": "system", "content": "Be concise."},
                {"role": "user", "content": "Answer the question."},
            ],
            "temperature": 0,
            "max_output_tokens": 64,
            "seed": 7,
        }
    ]
    assert result.text == "Provider answer"
    assert result.metadata is not None
    assert result.metadata.model == "gpt-4.1-mini"
    assert result.metadata.latency_ms == 250.0
    assert result.metadata.usage == ModelUsage(
        prompt_tokens=11,
        completion_tokens=7,
        total_tokens=18,
    )
    assert result.metadata.raw == {
        "id": "resp_123",
        "object": "response",
        "status": "completed",
        "output_text": "Provider answer",
        "usage": {
            "prompt_tokens": 11,
            "completion_tokens": 7,
            "total_tokens": 18,
        },
    }


def test_ollama_adapter_shapes_non_streaming_request_and_maps_usage() -> None:
    transport = CapturingOllamaTransport(
        {
            "model": "llama3.2",
            "created_at": "2026-04-03T07:20:00Z",
            "response": "Provider answer",
            "done": True,
            "done_reason": "stop",
            "total_duration": 1000,
            "load_duration": 200,
            "prompt_eval_count": 11,
            "prompt_eval_duration": 300,
            "eval_count": 7,
            "eval_duration": 400,
            "ignored": "trim me",
        }
    )
    adapter = OllamaAdapter(post_json=transport, clock=FakeClock(1.0, 1.125))

    result = adapter.generate(
        ModelRequest(
            model="llama3.2",
            prompt="Answer the question.",
            system_prompt="Be concise.",
            seed=7,
            options={
                "temperature": 0,
                "top_p": 0.8,
                "keep_alive": "10m",
                "base_url": "http://ollama.local:11434/api",
                "timeout_seconds": 9.5,
            },
        )
    )

    assert transport.calls == [
        {
            "base_url": "http://ollama.local:11434",
            "payload": {
                "model": "llama3.2",
                "prompt": "Answer the question.",
                "system": "Be concise.",
                "stream": False,
                "keep_alive": "10m",
                "options": {
                    "temperature": 0,
                    "top_p": 0.8,
                    "seed": 7,
                },
            },
            "timeout_seconds": 9.5,
        }
    ]
    assert result.text == "Provider answer"
    assert result.metadata is not None
    assert result.metadata.model == "llama3.2"
    assert result.metadata.latency_ms == 125.0
    assert result.metadata.usage == ModelUsage(
        prompt_tokens=11,
        completion_tokens=7,
        total_tokens=18,
    )
    assert result.metadata.raw == {
        "model": "llama3.2",
        "created_at": "2026-04-03T07:20:00Z",
        "done": True,
        "done_reason": "stop",
        "total_duration": 1000,
        "load_duration": 200,
        "prompt_eval_count": 11,
        "prompt_eval_duration": 300,
        "eval_count": 7,
        "eval_duration": 400,
    }


def test_ollama_adapter_wraps_transport_failures_with_base_url() -> None:
    adapter = OllamaAdapter(
        post_json=lambda base_url, payload, timeout_seconds: (_ for _ in ()).throw(
            URLError("connection refused")
        )
    )

    with pytest.raises(RuntimeError, match="Ollama request to http://localhost:11434 failed"):
        adapter.generate(ModelRequest(model="llama3.2", prompt="Answer the question."))


def test_ollama_adapter_rejects_malformed_payloads() -> None:
    adapter = OllamaAdapter(post_json=lambda base_url, payload, timeout_seconds: {"done": True})

    with pytest.raises(
        RuntimeError,
        match="Ollama response from http://localhost:11434 missing non-empty `response`",
    ):
        adapter.generate(ModelRequest(model="llama3.2", prompt="Answer the question."))


def test_resolve_model_rejects_unknown_adapter() -> None:
    with pytest.raises(UnknownModelAdapterError, match="unknown model adapter"):
        resolve_model("missing-adapter")
