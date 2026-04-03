"""Structured contracts for grounded insight reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from model_failure_lab.schemas import JsonValue

InsightMode = Literal["heuristic", "llm"]
InsightSourceKind = Literal["cases", "deltas", "aggregates", "comparison"]
EvidenceKind = Literal["run_case", "comparison_case"]
PatternKind = Literal[
    "failure_type",
    "prompt_cluster",
    "model_skew",
    "dataset_skew",
    "delta_kind",
    "transition_type",
    "aggregate_group",
    "outlier_case",
    "outlier_delta",
]


@dataclass(slots=True, frozen=True)
class InsightSampling:
    total_matches: int
    sampled_matches: int
    sample_limit: int
    truncated: bool
    strategy: str

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "total_matches": self.total_matches,
            "sampled_matches": self.sampled_matches,
            "sample_limit": self.sample_limit,
            "truncated": self.truncated,
            "strategy": self.strategy,
        }


@dataclass(slots=True, frozen=True)
class InsightEvidenceRef:
    kind: EvidenceKind
    label: str
    run_id: str | None = None
    report_id: str | None = None
    case_id: str | None = None
    prompt_id: str | None = None
    section: str | None = None
    transition_type: str | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "kind": self.kind,
            "label": self.label,
            "run_id": self.run_id,
            "report_id": self.report_id,
            "case_id": self.case_id,
            "prompt_id": self.prompt_id,
            "section": self.section,
            "transition_type": self.transition_type,
        }


@dataclass(slots=True, frozen=True)
class InsightPattern:
    kind: PatternKind
    label: str
    summary: str
    group_key: str | None
    count: int
    share: float | None
    evidence_refs: tuple[InsightEvidenceRef, ...]

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "kind": self.kind,
            "label": self.label,
            "summary": self.summary,
            "group_key": self.group_key,
            "count": self.count,
            "share": self.share,
            "evidence_refs": [item.to_payload() for item in self.evidence_refs],
        }


@dataclass(slots=True, frozen=True)
class InsightReport:
    analysis_mode: InsightMode
    source_kind: InsightSourceKind
    title: str
    summary: str
    generated_by: str
    sampling: InsightSampling
    patterns: tuple[InsightPattern, ...]
    anomalies: tuple[InsightPattern, ...]
    evidence_links: tuple[InsightEvidenceRef, ...]

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "analysis_mode": self.analysis_mode,
            "source_kind": self.source_kind,
            "title": self.title,
            "summary": self.summary,
            "generated_by": self.generated_by,
            "sampling": self.sampling.to_payload(),
            "patterns": [item.to_payload() for item in self.patterns],
            "anomalies": [item.to_payload() for item in self.anomalies],
            "evidence_links": [item.to_payload() for item in self.evidence_links],
        }
