"""Structured grounded analysis over query-backed failure artifacts."""

from .contracts import InsightEvidenceRef, InsightPattern, InsightReport, InsightSampling
from .comparison_explainer import build_query_insight_report, explain_comparison_report
from .prompt_builder import DEFAULT_ANALYSIS_SYSTEM_PROMPT, build_insight_enrichment_prompt
from .summarizer import (
    DEFAULT_INSIGHT_SAMPLE_LIMIT,
    summarize_aggregate_query,
    summarize_case_query,
    summarize_delta_query,
    summarize_query_results,
)

__all__ = [
    "DEFAULT_INSIGHT_SAMPLE_LIMIT",
    "DEFAULT_ANALYSIS_SYSTEM_PROMPT",
    "InsightEvidenceRef",
    "InsightPattern",
    "InsightReport",
    "InsightSampling",
    "build_insight_enrichment_prompt",
    "build_query_insight_report",
    "explain_comparison_report",
    "summarize_aggregate_query",
    "summarize_case_query",
    "summarize_delta_query",
    "summarize_query_results",
]
