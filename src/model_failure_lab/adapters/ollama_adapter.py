"""Provider-contained Ollama adapter implementation."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from time import perf_counter
from typing import Any
from urllib import error, request

from model_failure_lab.schemas import JsonValue

from .contracts import ModelMetadata, ModelRequest, ModelResult, ModelUsage

_DEFAULT_BASE_URL = "http://localhost:11434"
_RESERVED_OPTION_KEYS = frozenset({"base_url", "timeout_seconds", "keep_alive"})


class OllamaAdapter:
    """Invoke Ollama's local HTTP API behind the shared adapter contract."""

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
            raise RuntimeError(f"Ollama request to {base_url} failed: {exc}") from exc
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
    options = {
        key: value for key, value in request.options.items() if key not in _RESERVED_OPTION_KEYS
    }
    if request.seed is not None:
        options.setdefault("seed", request.seed)

    payload: dict[str, JsonValue] = {
        "model": request.model,
        "prompt": request.prompt,
        "stream": False,
    }
    if request.system_prompt:
        payload["system"] = request.system_prompt

    keep_alive = request.options.get("keep_alive")
    if keep_alive is not None:
        payload["keep_alive"] = keep_alive

    if options:
        payload["options"] = options

    return payload


def _base_url_from_options(options: Mapping[str, JsonValue]) -> str:
    raw_value = options.get("base_url")
    if raw_value is None:
        return _DEFAULT_BASE_URL
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise RuntimeError("Ollama base URL must be a non-empty string")
    normalized = raw_value.strip().rstrip("/")
    if normalized.endswith("/api"):
        normalized = normalized[: -len("/api")]
    return normalized


def _timeout_from_options(options: Mapping[str, JsonValue]) -> float | None:
    raw_value = options.get("timeout_seconds")
    if raw_value is None:
        return None
    if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
        raise RuntimeError("Ollama timeout_seconds must be a positive number")
    timeout = float(raw_value)
    if timeout <= 0:
        raise RuntimeError("Ollama timeout_seconds must be a positive number")
    return timeout


def _post_json(
    base_url: str,
    payload: dict[str, JsonValue],
    timeout_seconds: float | None,
) -> Mapping[str, object]:
    endpoint = f"{base_url}/api/generate"
    request_body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        endpoint,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=timeout_seconds) as http_response:
            response_body = http_response.read().decode("utf-8")
    except error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="replace").strip()
        message = f"Ollama request to {base_url} failed with HTTP {exc.code}"
        if response_body:
            message = f"{message}: {response_body}"
        raise RuntimeError(message) from exc
    except error.URLError as exc:
        reason = exc.reason if getattr(exc, "reason", None) is not None else exc
        raise RuntimeError(f"Ollama request to {base_url} failed: {reason}") from exc

    if not response_body.strip():
        raise RuntimeError(f"Ollama response from {base_url} was empty")

    try:
        parsed = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Ollama response from {base_url} was not valid JSON") from exc
    if not isinstance(parsed, Mapping):
        raise RuntimeError(f"Ollama response from {base_url} was not a JSON object")
    return parsed


def _extract_response_text(response: Mapping[str, object], base_url: str) -> str:
    text = response.get("response")
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError(f"Ollama response from {base_url} missing non-empty `response`")
    return text


def _response_model(response: Mapping[str, object], *, fallback: str) -> str:
    model_name = response.get("model")
    if isinstance(model_name, str) and model_name.strip():
        return model_name
    return fallback


def _extract_usage(response: Mapping[str, object]) -> ModelUsage | None:
    prompt_tokens = _optional_int(response.get("prompt_eval_count"))
    completion_tokens = _optional_int(response.get("eval_count"))
    if prompt_tokens is None and completion_tokens is None:
        return None
    total_tokens = None
    if prompt_tokens is not None and completion_tokens is not None:
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
    for key in (
        "model",
        "created_at",
        "done",
        "done_reason",
        "total_duration",
        "load_duration",
        "prompt_eval_count",
        "prompt_eval_duration",
        "eval_count",
        "eval_duration",
    ):
        value = response.get(key)
        if value is not None:
            trimmed[key] = value
    return trimmed
