from __future__ import annotations

import pytest

from model_failure_lab.adapters import (
    ModelRequest,
    OpenAICompatAdapter,
    available_models,
    resolve_model,
)

BASE_URL_OPTIONS = {"base_url": "http://localhost:8000/v1"}


class FakeClock:
    def __init__(self, *values: float) -> None:
        self._values = list(values)

    def __call__(self) -> float:
        return self._values.pop(0)


def _response_payload() -> dict[str, object]:
    return {
        "id": "chatcmpl-1",
        "model": "served-model",
        "created": 1,
        "choices": [
            {"message": {"role": "assistant", "content": "served answer"}, "finish_reason": "stop"}
        ],
        "usage": {"prompt_tokens": 11, "completion_tokens": 5, "total_tokens": 16},
    }


def test_openai_compat_is_registered() -> None:
    assert "openai-compat" in available_models()
    assert isinstance(resolve_model("openai-compat"), OpenAICompatAdapter)


def test_generate_posts_chat_completions_payload_and_maps_response() -> None:
    captured: dict[str, object] = {}

    def fake_post(base_url: str, payload: dict[str, object], timeout: float | None):
        captured["base_url"] = base_url
        captured["payload"] = payload
        captured["timeout"] = timeout
        return _response_payload()

    adapter = OpenAICompatAdapter(post_json=fake_post, clock=FakeClock(1.0, 1.25))
    result = adapter.generate(
        ModelRequest(
            model="my-model",
            prompt="What is 2+2?",
            system_prompt="Be terse.",
            seed=7,
            options={**BASE_URL_OPTIONS, "temperature": 0, "timeout_seconds": 30},
        )
    )

    assert captured["base_url"] == "http://localhost:8000/v1"
    assert captured["timeout"] == 30.0
    payload = captured["payload"]
    assert payload["model"] == "my-model"
    assert payload["seed"] == 7
    assert payload["temperature"] == 0
    assert "base_url" not in payload and "timeout_seconds" not in payload
    assert payload["messages"] == [
        {"role": "system", "content": "Be terse."},
        {"role": "user", "content": "What is 2+2?"},
    ]

    assert result.text == "served answer"
    assert result.metadata.model == "served-model"
    assert result.metadata.latency_ms == pytest.approx(250.0)
    assert result.metadata.usage.prompt_tokens == 11
    assert result.metadata.usage.completion_tokens == 5
    assert result.metadata.usage.total_tokens == 16
    assert result.metadata.raw["finish_reason"] == "stop"


def test_generate_requires_base_url_option() -> None:
    adapter = OpenAICompatAdapter(post_json=lambda *args: _response_payload())
    with pytest.raises(RuntimeError, match="base_url"):
        adapter.generate(ModelRequest(model="m", prompt="p"))


def test_generate_rejects_missing_message_content() -> None:
    adapter = OpenAICompatAdapter(post_json=lambda *args: {"choices": []})
    with pytest.raises(RuntimeError, match="choices"):
        adapter.generate(ModelRequest(model="m", prompt="p", options=dict(BASE_URL_OPTIONS)))


def test_generate_wraps_transport_errors() -> None:
    def failing_post(base_url: str, payload: dict[str, object], timeout: float | None):
        raise OSError("connection refused")

    adapter = OpenAICompatAdapter(post_json=failing_post)
    with pytest.raises(RuntimeError, match="connection refused"):
        adapter.generate(ModelRequest(model="m", prompt="p", options=dict(BASE_URL_OPTIONS)))


def test_generate_rejects_invalid_timeout() -> None:
    adapter = OpenAICompatAdapter(post_json=lambda *args: _response_payload())
    with pytest.raises(RuntimeError, match="timeout_seconds"):
        adapter.generate(
            ModelRequest(
                model="m", prompt="p", options={**BASE_URL_OPTIONS, "timeout_seconds": -1}
            )
        )
