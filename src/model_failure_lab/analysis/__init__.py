"""Structured grounded analysis over query-backed failure artifacts."""

from .contracts import InsightEvidenceRef, InsightPattern, InsightReport, InsightSampling
from .summarizer import (
    DEFAULT_INSIGHT_SAMPLE_LIMIT,
    summarize_aggregate_query,
    summarize_case_query,
    summarize_delta_query,
    summarize_query_results,
)

__all__ = [
    "DEFAULT_INSIGHT_SAMPLE_LIMIT",
    "InsightEvidenceRef",
    "InsightPattern",
    "InsightReport",
    "InsightSampling",
    "summarize_aggregate_query",
    "summarize_case_query",
    "summarize_delta_query",
    "summarize_query_results",
]
