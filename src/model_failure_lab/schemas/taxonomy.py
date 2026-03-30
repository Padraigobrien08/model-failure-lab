"""Shared failure taxonomy and expectation verdict helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

FAILURE_TYPES: tuple[str, ...] = (
    "no_failure",
    "reasoning",
    "instruction_following",
    "hallucination",
    "retrieval",
    "safety",
    "format",
    "tool_use",
)
NO_FAILURE_TYPE = "no_failure"
LEGACY_FAILURE_TYPE_ALIASES: dict[str, str] = {
    "instruction": "instruction_following",
}
EXPECTATION_VERDICTS: tuple[str, ...] = (
    "matched_expected",
    "unexpected_failure",
    "missed_expected",
    "no_failure_as_expected",
)


def normalize_failure_type(failure_type: str) -> str:
    """Normalize one failure type into the closed canonical taxonomy."""

    normalized = failure_type.strip()
    if not normalized:
        raise ValueError("failure_type must be a non-empty string")
    normalized = LEGACY_FAILURE_TYPE_ALIASES.get(normalized, normalized)
    if normalized not in FAILURE_TYPES:
        raise ValueError(f"unknown failure_type: {normalized}")
    return normalized


def normalize_failure_subtype(failure_subtype: str | None) -> str | None:
    """Normalize an optional failure subtype."""

    if failure_subtype is None:
        return None
    normalized = failure_subtype.strip()
    if not normalized:
        raise ValueError("failure_subtype must be a non-empty string or null")
    return normalized


def normalize_expectation_verdict(expectation_verdict: str) -> str:
    """Normalize one explicit expectation verdict into the closed set."""

    normalized = expectation_verdict.strip()
    if not normalized:
        raise ValueError("expectation_verdict must be a non-empty string")
    if normalized not in EXPECTATION_VERDICTS:
        raise ValueError(f"unknown expectation_verdict: {normalized}")
    return normalized


@dataclass(slots=True, frozen=True)
class FailureLabel:
    """Canonical typed label for one observed or expected failure."""

    failure_type: str
    failure_subtype: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "failure_type", normalize_failure_type(self.failure_type))
        object.__setattr__(
            self,
            "failure_subtype",
            normalize_failure_subtype(self.failure_subtype),
        )

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {"failure_type": self.failure_type}
        if self.failure_subtype is not None:
            payload["failure_subtype"] = self.failure_subtype
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "FailureLabel":
        if isinstance(payload, str):
            return cls(failure_type=payload)
        if not isinstance(payload, Mapping):
            raise ValueError("failure label payload must be a string or mapping")
        failure_type = payload.get("failure_type")
        if not isinstance(failure_type, str):
            raise ValueError("failure_type must be a non-empty string")
        failure_subtype = payload.get("failure_subtype")
        if failure_subtype is not None and not isinstance(failure_subtype, str):
            raise ValueError("failure_subtype must be a non-empty string or null")
        return cls(
            failure_type=failure_type,
            failure_subtype=failure_subtype,
        )
