"""Derived local query index helpers for cross-run artifact analysis."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model_failure_lab.clusters import (
        ClusterEvidenceRef,
        FailureClusterDetail,
        FailureClusterOccurrence,
        FailureClusterSummary,
    )

from .builder import (
    QUERY_INDEX_DIRNAME,
    QUERY_INDEX_FILENAME,
    QUERY_INDEX_SCHEMA_VERSION,
    QueryIndexSummary,
    ensure_query_index,
    query_index_dir,
    query_index_path,
    rebuild_query_index,
)
from .query import (
    QueryFilters,
    aggregate_case_query,
    aggregate_delta_query,
    artifact_overview_summary,
    count_case_query,
    count_delta_query,
    list_comparison_inventory,
    list_query_facets,
    list_run_inventory,
    query_case_deltas,
    query_cases,
    query_comparison_signals,
)

__all__ = [
    "QUERY_INDEX_DIRNAME",
    "QUERY_INDEX_FILENAME",
    "QUERY_INDEX_SCHEMA_VERSION",
    "ClusterEvidenceRef",
    "FailureClusterDetail",
    "FailureClusterOccurrence",
    "FailureClusterSummary",
    "QueryFilters",
    "QueryIndexSummary",
    "aggregate_case_query",
    "aggregate_delta_query",
    "artifact_overview_summary",
    "count_case_query",
    "count_delta_query",
    "ensure_query_index",
    "get_failure_cluster_detail",
    "list_comparison_inventory",
    "list_clusters_for_comparison",
    "list_failure_clusters",
    "list_query_facets",
    "list_run_inventory",
    "query_case_deltas",
    "query_cases",
    "query_comparison_signals",
    "query_index_dir",
    "query_index_path",
    "rebuild_query_index",
]


def __getattr__(name: str):
    if name in {
        "ClusterEvidenceRef",
        "FailureClusterDetail",
        "FailureClusterOccurrence",
        "FailureClusterSummary",
        "get_failure_cluster_detail",
        "list_clusters_for_comparison",
        "list_failure_clusters",
    }:
        from model_failure_lab import clusters as _clusters

        return getattr(_clusters, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
