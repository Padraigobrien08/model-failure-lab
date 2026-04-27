"""Recurring root-cause intelligence summaries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from model_failure_lab.clusters import list_failure_clusters
from model_failure_lab.index import QueryFilters
from model_failure_lab.schemas import JsonValue


@dataclass(slots=True, frozen=True)
class RootCauseSummary:
    failure_type: str
    cluster_count: int
    total_occurrences: int
    max_scope: int
    representative_cluster_ids: tuple[str, ...]

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "failure_type": self.failure_type,
            "cluster_count": self.cluster_count,
            "total_occurrences": self.total_occurrences,
            "max_scope": self.max_scope,
            "representative_cluster_ids": list(self.representative_cluster_ids),
        }


def summarize_recurring_root_causes(
    *,
    filters: QueryFilters | None = None,
    root: str | Path | None = None,
    limit: int = 10,
) -> tuple[RootCauseSummary, ...]:
    active_filters = filters or QueryFilters(limit=200)
    clusters = list_failure_clusters(
        active_filters,
        recurring_only=True,
        root=root,
        limit=max(limit * 5, 20),
    )
    grouped: dict[str, list[object]] = {}
    for cluster in clusters:
        key = cluster.failure_types[0] if cluster.failure_types else "unknown"
        grouped.setdefault(key, []).append(cluster)
    summaries: list[RootCauseSummary] = []
    for failure_type, members in grouped.items():
        ordered = sorted(members, key=lambda row: (-row.scope_count, row.cluster_id))
        summaries.append(
            RootCauseSummary(
                failure_type=failure_type,
                cluster_count=len(members),
                total_occurrences=sum(member.occurrence_count for member in members),
                max_scope=max(member.scope_count for member in members),
                representative_cluster_ids=tuple(member.cluster_id for member in ordered[:3]),
            )
        )
    return tuple(
        sorted(
            summaries,
            key=lambda row: (-row.max_scope, -row.total_occurrences, row.failure_type),
        )[: max(limit, 1)]
    )
