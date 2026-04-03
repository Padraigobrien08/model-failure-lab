"""Provider-contained Anthropic adapter implementation."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from time import perf_counter
from typing import Any

from model_failure_lab.schemas import JsonValue

from .contracts import ModelMetadata, ModelRequest, ModelResult, ModelUsage

_DEFAULT_MAX_TOKENS = 1024
_RESERVED_OPTION_KEYS = frozenset({"base_url"})


class AnthropicAdapter:
    """Invoke the Anthropic Python client behind the shared adapter contract."""

    def __init__(
        self,
        *,
        client: Any | None = None,
        client_factory: Callable[[str | None], Any] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._client = client
        self._client_factory = client_factory or _default_client_factory
        self._clock = clock or perf_counter

    def generate(self, request: ModelRequest) -> ModelResult:
        base_url = _base_url_from_options(request.options)
        client = self._client or self._client_factory(base_url)
        start = self._clock()
        try:
            response = _invoke_anthropic(client, request)
        except RuntimeError:
            raise
        except Exception as exc:
            if base_url is not None:
                raise RuntimeError(f"Anthropic request to {base_url} failed: {exc}") from exc
            raise RuntimeError(f"Anthropic request failed: {exc}") from exc
        latency_ms = (self._clock() - start) * 1000.0
        return ModelResult(
            text=_extract_text(response),
            metadata=ModelMetadata(
                model=_response_model(response, fallback=request.model),
                latency_ms=latency_ms,
                usage=_extract_usage(response),
                raw=_trim_raw_payload(response),
            ),
        )


def _default_client_factory(base_url: str | None) -> Any:
    try:
        from anthropic import Anthropic
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised indirectly by runtime users
        raise RuntimeError(
            "Anthropic support is not installed. Install with "
            "`pip install 'model-failure-lab[anthropic]'` or, from a checkout, "
            "`python -m pip install '.[anthropic]'`."
        ) from exc

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        if base_url is None:
            raise RuntimeError(
                "Anthropic API key is not configured. Set `ANTHROPIC_API_KEY` or use "
                "`--anthropic-base-url` against a local compatible stub."
            )
        api_key = "local-test-key"

    client_kwargs: dict[str, object] = {"api_key": api_key}
    if base_url is not None:
        client_kwargs["base_url"] = base_url

    try:
        return Anthropic(**client_kwargs)
    except Exception as exc:  # pragma: no cover - exercised indirectly by runtime users
        raise RuntimeError(f"Anthropic client setup failed: {exc}") from exc


def _invoke_anthropic(client: Any, request: ModelRequest) -> Any:
    messages_api = getattr(client, "messages", None)
    create = getattr(messages_api, "create", None)
    if create is None:
        raise RuntimeError("Anthropic client does not expose messages.create")

    payload: dict[str, object] = {
        "model": request.model,
        "messages": [{"role": "user", "content": request.prompt}],
        "max_tokens": _DEFAULT_MAX_TOKENS,
    }
    if request.system_prompt:
        payload["system"] = request.system_prompt

    for key, value in request.options.items():
        if key not in _RESERVED_OPTION_KEYS:
            payload[key] = value

    return create(**payload)


def _base_url_from_options(options: Mapping[str, JsonValue]) -> str | None:
    raw_value = options.get("base_url")
    if raw_value is None:
        return None
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise RuntimeError("Anthropic base URL must be a non-empty string")
    return raw_value.strip().rstrip("/")


def _extract_text(response: Any) -> str:
    content = _get_value(response, "content")
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            item_type = _get_value(item, "type")
            text = _get_value(item, "text")
            if item_type == "text" and isinstance(text, str):
                parts.append(text)
        normalized = "".join(parts).strip()
        if normalized:
            return normalized
    raise RuntimeError("Anthropic response did not include text content")


def _response_model(response: Any, *, fallback: str) -> str:
    model_name = _get_value(response, "model")
    if isinstance(model_name, str) and model_name.strip():
        return model_name
    return fallback


def _extract_usage(response: Any) -> ModelUsage | None:
    usage = _get_value(response, "usage")
    if usage is None:
        return None
    prompt_tokens = _optional_int(_get_value(usage, "input_tokens"))
    completion_tokens = _optional_int(_get_value(usage, "output_tokens"))
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


def _trim_raw_payload(response: Any) -> dict[str, Any]:
    raw = None
    if hasattr(response, "model_dump"):
        raw = response.model_dump()
    elif isinstance(response, dict):
        raw = response

    if isinstance(raw, dict):
        trimmed: dict[str, Any] = {}
        for key in ("id", "type", "role", "model", "stop_reason", "stop_sequence", "usage"):
            value = raw.get(key)
            if value is not None:
                trimmed[key] = value
        return trimmed

    fallback: dict[str, Any] = {}
    for key in ("id", "type", "role", "model", "stop_reason", "stop_sequence"):
        value = _get_value(response, key)
        if value is not None:
            fallback[key] = value
    usage = _get_value(response, "usage")
    if usage is not None:
        usage_payload: dict[str, Any] = {}
        for key in ("input_tokens", "output_tokens"):
            value = _get_value(usage, key)
            if value is not None:
                usage_payload[key] = value
        if usage_payload:
            fallback["usage"] = usage_payload
    return fallback


def _get_value(obj: Any, name: str) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)
