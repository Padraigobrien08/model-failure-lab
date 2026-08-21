"""Adapter for any OpenAI-compatible chat-completions server.

Targets the de-facto standard `POST <base_url>/chat/completions` API exposed by
vLLM, llama.cpp server, LM Studio, Ollama's OpenAI endpoint, Together, Groq,
OpenRouter, and similar runtimes — without requiring the `openai` extra.

Usage: `--model openai-compat:<model> --option base_url='"http://localhost:8000/v1"'`.
If the server requires a bearer token, export it as `OPENAI_COMPAT_API_KEY`;
it is read from the environment only and never persisted into run artifacts.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from time import perf_counter
from typing import Any
from urllib import error, request

from model_failure_lab.schemas import JsonValue

from .contracts import ModelMetadata, ModelRequest, ModelResult, ModelUsage

_API_KEY_ENV = "OPENAI_COMPAT_API_KEY"
_RESERVED_OPTION_KEYS = frozenset({"base_url", "timeout_seconds"})


class OpenAICompatAdapter:
    """Invoke an OpenAI-compatible HTTP API behind the shared adapter contract."""

    def __init__(
        self,
        *,
        post_json: Callable[[str, dict[str, JsonValue], float | None], Mapping[str, object]]
        | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._post_json = post_json or _post_json
        self._clock = clock or perf_counter

    def generate(self, request: ModelRequest) -> ModelResult:
        base_url = _base_url_from_options(request.options)
        timeout_seconds = _timeout_from_options(request.options)
        payload = _build_payload(request)

        start = self._clock()
        try:
            response = self._post_json(base_url, payload, timeout_seconds)
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(f"OpenAI-compatible request to {base_url} failed: {exc}") from exc
        latency_ms = (self._clock() - start) * 1000.0

        return ModelResult(
            text=_extract_response_text(response, base_url),
            metadata=ModelMetadata(
                model=_response_model(response, fallback=request.model),
                latency_ms=latency_ms,
                usage=_extract_usage(response),
                raw=_trim_raw_payload(response),
            ),
        )


def _build_payload(request: ModelRequest) -> dict[str, JsonValue]:
    extra_options = {
        key: value for key, value in request.options.items() if key not in _RESERVED_OPTION_KEYS
    }

    messages: list[JsonValue] = []
    if request.system_prompt:
        messages.append({"role": "system", "content": request.system_prompt})
    messages.append({"role": "user", "content": request.prompt})

    payload: dict[str, JsonValue] = {
        "model": request.model,
        "messages": messages,
    }
    if request.seed is not None:
        payload.setdefault("seed", request.seed)
    payload.update(extra_options)
    return payload


def _base_url_from_options(options: Mapping[str, JsonValue]) -> str:
    raw_value = options.get("base_url")
    if raw_value is None:
        raise RuntimeError(
            "openai-compat requires a `base_url` model option, for example "
            "--option base_url='\"http://localhost:8000/v1\"'"
        )
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise RuntimeError("openai-compat base_url must be a non-empty string")
    return raw_value.strip().rstrip("/")


def _timeout_from_options(options: Mapping[str, JsonValue]) -> float | None:
    raw_value = options.get("timeout_seconds")
    if raw_value is None:
        return None
    if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
        raise RuntimeError("openai-compat timeout_seconds must be a positive number")
    timeout = float(raw_value)
    if timeout <= 0:
        raise RuntimeError("openai-compat timeout_seconds must be a positive number")
    return timeout


def _post_json(
    base_url: str,
    payload: dict[str, JsonValue],
    timeout_seconds: float | None,
) -> Mapping[str, object]:
    endpoint = f"{base_url}/chat/completions"
    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get(_API_KEY_ENV)
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    http_request = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=timeout_seconds) as http_response:
            response_body = http_response.read().decode("utf-8")
    except error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="replace").strip()
        message = f"OpenAI-compatible request to {base_url} failed with HTTP {exc.code}"
        if response_body:
            message = f"{message}: {response_body}"
        raise RuntimeError(message) from exc
    except error.URLError as exc:
        reason = exc.reason if getattr(exc, "reason", None) is not None else exc
        raise RuntimeError(f"OpenAI-compatible request to {base_url} failed: {reason}") from exc

    if not response_body.strip():
        raise RuntimeError(f"OpenAI-compatible response from {base_url} was empty")

    try:
        parsed = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"OpenAI-compatible response from {base_url} was not valid JSON"
        ) from exc
    if not isinstance(parsed, Mapping):
        raise RuntimeError(f"OpenAI-compatible response from {base_url} was not a JSON object")
    return parsed


def _extract_response_text(response: Mapping[str, object], base_url: str) -> str:
    choices = response.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, Mapping):
            message = first.get("message")
            if isinstance(message, Mapping):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content
    raise RuntimeError(
        f"OpenAI-compatible response from {base_url} missing non-empty "
        "`choices[0].message.content`"
    )


def _response_model(response: Mapping[str, object], *, fallback: str) -> str:
    model_name = response.get("model")
    if isinstance(model_name, str) and model_name.strip():
        return model_name
    return fallback


def _extract_usage(response: Mapping[str, object]) -> ModelUsage | None:
    usage = response.get("usage")
    if not isinstance(usage, Mapping):
        return None
    prompt_tokens = _optional_int(usage.get("prompt_tokens"))
    completion_tokens = _optional_int(usage.get("completion_tokens"))
    total_tokens = _optional_int(usage.get("total_tokens"))
    if prompt_tokens is None and completion_tokens is None and total_tokens is None:
        return None
    if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
        total_tokens = prompt_tokens + completion_tokens
    return ModelUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )


def _optional_int(value: object) -> int | None:
    if type(value) is int:
        return value
    return None


def _trim_raw_payload(response: Mapping[str, object]) -> dict[str, Any]:
    trimmed: dict[str, Any] = {}
    for key in ("id", "model", "created", "system_fingerprint"):
        value = response.get(key)
        if value is not None:
            trimmed[key] = value
    finish_reason = _finish_reason(response)
    if finish_reason is not None:
        trimmed["finish_reason"] = finish_reason
    return trimmed


def _finish_reason(response: Mapping[str, object]) -> str | None:
    choices = response.get("choices")
    if isinstance(choices, list) and choices and isinstance(choices[0], Mapping):
        reason = choices[0].get("finish_reason")
        if isinstance(reason, str):
            return reason
    return None
