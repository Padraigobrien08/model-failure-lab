"""Explicit in-memory registry for model adapters."""

from __future__ import annotations

from .contracts import ModelAdapter, ModelFactory

_MODEL_FACTORIES: dict[str, ModelFactory] = {}
_BUILTINS_REGISTERED = False


class UnknownModelAdapterError(LookupError):
    """Raised when an adapter ID has not been registered."""


def _register_model(model_id: str, factory: ModelFactory) -> None:
    _MODEL_FACTORIES[model_id] = factory


def _validate_model_id(model_id: str) -> str:
    normalized = model_id.strip()
    if not normalized:
        raise ValueError("model_id must be a non-empty string")
    return normalized


def ensure_builtin_models() -> None:
    """Register built-in adapters in deterministic order once."""

    global _BUILTINS_REGISTERED

    if _BUILTINS_REGISTERED:
        return

    try:
        from .demo import DemoAdapter
    except ModuleNotFoundError:
        DemoAdapter = None

    if DemoAdapter is not None:
        _register_model("demo", DemoAdapter)

    try:
        from .openai_adapter import OpenAIAdapter
    except ModuleNotFoundError:
        OpenAIAdapter = None

    if OpenAIAdapter is not None:
        _register_model("openai", OpenAIAdapter)

    _BUILTINS_REGISTERED = True


def register_model(model_id: str, factory: ModelFactory) -> None:
    """Register a custom model adapter factory by ID."""

    ensure_builtin_models()
    normalized = _validate_model_id(model_id)
    if normalized in _MODEL_FACTORIES:
        raise ValueError(f"model adapter '{normalized}' is already registered")
    _register_model(normalized, factory)


def available_models() -> tuple[str, ...]:
    """Return registered adapter IDs in deterministic order."""

    ensure_builtin_models()
    return tuple(_MODEL_FACTORIES)


def resolve_model(model_id: str) -> ModelAdapter:
    """Instantiate one adapter by its registered ID."""

    ensure_builtin_models()
    normalized = _validate_model_id(model_id)
    try:
        factory = _MODEL_FACTORIES[normalized]
    except KeyError as exc:
        raise UnknownModelAdapterError(f"unknown model adapter: {normalized}") from exc
    return factory()
