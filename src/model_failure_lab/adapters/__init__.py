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
    "UnknownModelAdapterError",
    "available_models",
    "register_model",
    "resolve_model",
]
