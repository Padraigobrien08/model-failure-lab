"""Derived local query index helpers for cross-run artifact analysis."""

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
    artifact_overview_summary,
    list_comparison_inventory,
    list_query_facets,
    list_run_inventory,
    query_case_deltas,
    query_cases,
)

__all__ = [
    "QUERY_INDEX_DIRNAME",
    "QUERY_INDEX_FILENAME",
    "QUERY_INDEX_SCHEMA_VERSION",
    "QueryFilters",
    "QueryIndexSummary",
    "aggregate_case_query",
    "artifact_overview_summary",
    "ensure_query_index",
    "list_comparison_inventory",
    "list_query_facets",
    "list_run_inventory",
    "query_case_deltas",
    "query_cases",
    "query_index_dir",
    "query_index_path",
    "rebuild_query_index",
]
