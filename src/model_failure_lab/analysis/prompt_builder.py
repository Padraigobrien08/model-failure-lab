"""Prompt construction helpers for grounded insight enrichment."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from .contracts import InsightReport

DEFAULT_ANALYSIS_SYSTEM_PROMPT = (
    "You are a grounded LLM failure-analysis assistant. Rewrite only the provided summaries, keep "
    "every claim tied to the supplied groups, and never invent new evidence IDs or categories."
)


def build_insight_enrichment_prompt(
    *,
    base_report: InsightReport,
    objective: str,
    context_payload: Mapping[str, Any],
) -> str:
    base_json = json.dumps(base_report.to_payload(), indent=2, sort_keys=True)
    context_json = json.dumps(dict(context_payload), indent=2, sort_keys=True)
    return "\n".join(
        [
            "You are enriching a grounded failure-analysis report.",
            f"Task: {objective}",
            "",
            "Return JSON only with this shape:",
            "{",
            '  "summary": "string",',
            '  "patterns": [{"kind": "string", "group_key": "string|null", "summary": "string"}],',
            '  "anomalies": [{"kind": "string", "group_key": "string|null", "summary": "string"}]',
            "}",
            "",
            "Rules:",
            "- Do not invent new evidence refs, IDs, group kinds, or group keys.",
            "- Only rewrite summaries for groups that already exist in the base report.",
            "- If the evidence is weak or mixed, say that explicitly in the summary text.",
            "- Keep the tone factual and concise.",
            "",
            "Base report:",
            base_json,
            "",
            "Representative evidence context:",
            context_json,
        ]
    )


def build_query_context_payload(
    *,
    mode: str,
    base_report: InsightReport,
    filters_payload: Mapping[str, Any],
    representative_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "mode": mode,
        "filters": dict(filters_payload),
        "sampling": base_report.sampling.to_payload(),
        "representative_rows": [dict(row) for row in representative_rows],
    }


def build_comparison_context_payload(
    *,
    report_id: str,
    base_report: InsightReport,
    representative_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "report_id": report_id,
        "sampling": base_report.sampling.to_payload(),
        "representative_rows": [dict(row) for row in representative_rows],
    }
