"""Provider-contained OpenAI adapter implementation."""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter
from typing import Any

from .contracts import ModelMetadata, ModelRequest, ModelResult, ModelUsage


class OpenAIAdapter:
    """Invoke the OpenAI Python client behind the shared adapter contract."""

    def __init__(
        self,
        *,
        client: Any | None = None,
        client_factory: Callable[[], Any] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._client = client
        self._client_factory = client_factory or _default_client_factory
        self._clock = clock or perf_counter

    def generate(self, request: ModelRequest) -> ModelResult:
        client = self._client or self._client_factory()
        start = self._clock()
        response = _invoke_openai(client, request)
        latency_ms = (self._clock() - start) * 1000.0
        return ModelResult(
            text=_extract_text(response),
            metadata=ModelMetadata(
                model=request.model,
                latency_ms=latency_ms,
                usage=_extract_usage(response),
                raw=_trim_raw_payload(response),
            ),
        )


def _default_client_factory() -> Any:
    try:
        from openai import OpenAI
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised indirectly by runtime users
        raise RuntimeError(
            "OpenAI support is not installed. Install with "
            "`pip install 'model-failure-lab[openai]'`."
        ) from exc
    return OpenAI()


def _invoke_openai(client: Any, request: ModelRequest) -> Any:
    options = dict(request.options)
    if request.seed is not None:
        options.setdefault("seed", request.seed)

    if hasattr(client, "responses") and hasattr(client.responses, "create"):
        return client.responses.create(
            model=request.model,
            input=_build_input_payload(request),
            **options,
        )

    if hasattr(client, "chat") and hasattr(client.chat, "completions"):
        return client.chat.completions.create(
            model=request.model,
            messages=_build_chat_messages(request),
            **options,
        )

    raise RuntimeError("OpenAI client does not expose responses.create or chat.completions.create")


def _build_input_payload(request: ModelRequest) -> list[dict[str, str]]:
    messages = []
    if request.system_prompt:
        messages.append({"role": "system", "content": request.system_prompt})
    messages.append({"role": "user", "content": request.prompt})
    return messages


def _build_chat_messages(request: ModelRequest) -> list[dict[str, str]]:
    return _build_input_payload(request)


def _extract_text(response: Any) -> str:
    output_text = _get_value(response, "output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    choices = _get_value(response, "choices")
    if isinstance(choices, list) and choices:
        first_choice = choices[0]
        message = _get_value(first_choice, "message")
        content = _get_value(message, "content")
        normalized = _normalize_content(content)
        if normalized:
            return normalized

    raise RuntimeError("OpenAI response did not include output text")


def _normalize_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            text = _get_value(item, "text")
            if isinstance(text, str):
                parts.append(text)
        return "".join(parts)
    return ""


def _extract_usage(response: Any) -> ModelUsage | None:
    usage = _get_value(response, "usage")
    if usage is None:
        return None

    prompt_tokens = _get_value(usage, "prompt_tokens")
    if prompt_tokens is None:
        prompt_tokens = _get_value(usage, "input_tokens")

    completion_tokens = _get_value(usage, "completion_tokens")
    if completion_tokens is None:
        completion_tokens = _get_value(usage, "output_tokens")

    total_tokens = _get_value(usage, "total_tokens")
    if not any(
        value is not None for value in (prompt_tokens, completion_tokens, total_tokens)
    ):
        return None

    return ModelUsage(
        prompt_tokens=int(prompt_tokens) if prompt_tokens is not None else None,
        completion_tokens=int(completion_tokens) if completion_tokens is not None else None,
        total_tokens=int(total_tokens) if total_tokens is not None else None,
    )


def _trim_raw_payload(response: Any) -> dict[str, Any]:
    raw = None
    if hasattr(response, "model_dump"):
        raw = response.model_dump()
    elif isinstance(response, dict):
        raw = response

    if isinstance(raw, dict):
        trimmed: dict[str, Any] = {}
        for key in ("id", "model", "created", "output_text", "usage", "object", "status"):
            value = raw.get(key)
            if value is not None:
                trimmed[key] = value
        return trimmed

    identifier = _get_value(response, "id")
    status = _get_value(response, "status")
    fallback: dict[str, Any] = {}
    if identifier is not None:
        fallback["id"] = identifier
    if status is not None:
        fallback["status"] = status
    return fallback


def _get_value(obj: Any, name: str) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)
