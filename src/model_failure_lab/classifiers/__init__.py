"""Classifier contracts, registries, and built-in heuristics."""

from .contracts import (
    Classifier,
    ClassifierExpectations,
    ClassifierInput,
    ClassifierResult,
)
from .heuristic import heuristic_classifier
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
    "heuristic_classifier",
    "UnknownClassifierError",
    "available_classifiers",
    "register_classifier",
    "resolve_classifier",
]
