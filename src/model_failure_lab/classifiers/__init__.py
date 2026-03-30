"""Classifier contracts, registries, and built-in heuristics."""

from .contracts import (
    Classifier,
    ClassifierExpectations,
    ClassifierInput,
    ClassifierResult,
)
from .registry import (
    UnknownClassifierError,
    available_classifiers,
    register_classifier,
    resolve_classifier,
)

__all__ = [
    "Classifier",
    "ClassifierExpectations",
    "ClassifierInput",
    "ClassifierResult",
    "UnknownClassifierError",
    "available_classifiers",
    "register_classifier",
    "resolve_classifier",
]
