"""Explicit in-memory registry for classifier functions."""

from __future__ import annotations

from .contracts import Classifier

_CLASSIFIERS: dict[str, Classifier] = {}
_BUILTINS_REGISTERED = False


class UnknownClassifierError(LookupError):
    """Raised when a classifier ID has not been registered."""


def _register_classifier(classifier_id: str, classifier: Classifier) -> None:
    _CLASSIFIERS[classifier_id] = classifier


def _validate_classifier_id(classifier_id: str) -> str:
    normalized = classifier_id.strip()
    if not normalized:
        raise ValueError("classifier_id must be a non-empty string")
    return normalized


def ensure_builtin_classifiers() -> None:
    """Register built-in classifier functions in deterministic order once."""

    global _BUILTINS_REGISTERED

    if _BUILTINS_REGISTERED:
        return

    try:
        from .heuristic import heuristic_classifier
    except ModuleNotFoundError:
        heuristic_classifier = None

    if heuristic_classifier is not None:
        _register_classifier("heuristic_v1", heuristic_classifier)

    _BUILTINS_REGISTERED = True


def register_classifier(classifier_id: str, classifier: Classifier) -> None:
    """Register a custom classifier by ID."""

    ensure_builtin_classifiers()
    normalized = _validate_classifier_id(classifier_id)
    if normalized in _CLASSIFIERS:
        raise ValueError(f"classifier '{normalized}' is already registered")
    _register_classifier(normalized, classifier)


def available_classifiers() -> tuple[str, ...]:
    """Return registered classifier IDs in deterministic order."""

    ensure_builtin_classifiers()
    return tuple(_CLASSIFIERS)


def resolve_classifier(classifier_id: str) -> Classifier:
    """Resolve one classifier function by its registered ID."""

    ensure_builtin_classifiers()
    normalized = _validate_classifier_id(classifier_id)
    try:
        return _CLASSIFIERS[normalized]
    except KeyError as exc:
        raise UnknownClassifierError(f"unknown classifier: {normalized}") from exc
