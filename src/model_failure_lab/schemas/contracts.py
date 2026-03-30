"""Canonical failure-analysis entity contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


def _json_list(values: tuple[str, ...]) -> list[str]:
    return list(values)


@dataclass(slots=True, frozen=True)
class PromptCase:
    """Tracked prompt input for a failure-analysis run."""

    id: str
    prompt: str
    expected_failure: str | None = None
    tags: tuple[str, ...] = ()
    metadata: dict[str, JsonValue] = field(default_factory=dict)

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "expected_failure": self.expected_failure,
            "tags": _json_list(self.tags),
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class Run:
    """Top-level execution record for one model and dataset combination."""

    run_id: str
    model: str
    dataset: str
    created_at: str
    config: dict[str, JsonValue] = field(default_factory=dict)
    metadata: dict[str, JsonValue] = field(default_factory=dict)

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "run_id": self.run_id,
            "model": self.model,
            "dataset": self.dataset,
            "created_at": self.created_at,
            "config": dict(self.config),
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class Result:
    """Per-prompt output classification recorded within a run."""

    prompt_id: str
    output: str
    failure_type: str
    score: float | None = None
    confidence: float | None = None
    explanation: str | None = None
    metadata: dict[str, JsonValue] = field(default_factory=dict)

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "prompt_id": self.prompt_id,
            "output": self.output,
            "failure_type": self.failure_type,
            "score": self.score,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class Report:
    """Aggregate summary for one or more saved runs."""

    report_id: str
    run_ids: tuple[str, ...]
    created_at: str
    total_cases: int
    failure_counts: dict[str, int]
    failure_rates: dict[str, float]
    metadata: dict[str, JsonValue] = field(default_factory=dict)

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "report_id": self.report_id,
            "run_ids": _json_list(self.run_ids),
            "created_at": self.created_at,
            "total_cases": self.total_cases,
            "failure_counts": dict(self.failure_counts),
            "failure_rates": dict(self.failure_rates),
            "metadata": dict(self.metadata),
        }
