"""Model adapter contracts, registries, and built-in adapters."""

from .contracts import (
    ModelAdapter,
    ModelFactory,
    ModelMetadata,
    ModelRequest,
    ModelResult,
    ModelUsage,
)
from .demo import DemoAdapter
from .ollama_adapter import OllamaAdapter
from .openai_adapter import OpenAIAdapter
from .registry import (
    UnknownModelAdapterError,
    available_models,
    register_model,
    resolve_model,
)

__all__ = [
    "ModelAdapter",
    "ModelFactory",
    "ModelMetadata",
    "ModelRequest",
    "ModelResult",
    "ModelUsage",
    "DemoAdapter",
    "OllamaAdapter",
    "OpenAIAdapter",
    "UnknownModelAdapterError",
    "available_models",
    "register_model",
    "resolve_model",
]
