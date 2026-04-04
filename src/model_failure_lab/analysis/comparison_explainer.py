"""Grounded CLI-facing insight builders over heuristic and LLM modes."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any, Literal

from model_failure_lab.adapters import ModelRequest, resolve_model
from model_failure_lab.index import QueryFilters, query_case_deltas, query_cases
from model_failure_lab.schemas import JsonValue

from .contracts import InsightPattern, InsightReport
from .prompt_builder import (
    DEFAULT_ANALYSIS_SYSTEM_PROMPT,
    build_comparison_context_payload,
    build_insight_enrichment_prompt,
    build_query_context_payload,
)
from .summarizer import DEFAULT_INSIGHT_SAMPLE_LIMIT, summarize_delta_query, summarize_query_results

IDENTIFIER_PATTERN = re.compile(
    r"\b(?:run_[A-Za-z0-9._:-]+|compare_[A-Za-z0-9._:-]+|case[-_][A-Za-z0-9._:-]+)\b"
)


def build_query_insight_report(
    *,
    mode: Literal["cases", "deltas", "aggregates"],
    filters: QueryFilters,
    aggregate_by: Literal["failure_type", "model", "dataset", "prompt_id"] = "failure_type",
    root: str | Path | None = None,
    analysis_mode: Literal["heuristic", "llm"] = "heuristic",
    analysis_adapter_id: str | None = None,
    analysis_model: str | None = None,
    analysis_system_prompt: str | None = None,
    analysis_options: Mapping[str, JsonValue] | None = None,
    sample_limit: int = DEFAULT_INSIGHT_SAMPLE_LIMIT,
) -> InsightReport:
    base_report = summarize_query_results(
        mode=mode,
        filters=filters,
        aggregate_by=aggregate_by,
        root=root,
        sample_limit=sample_limit,
    )
    if analysis_mode == "heuristic":
        return base_report

    representative_rows = _representative_query_rows(
        mode=mode,
        filters=filters,
        root=root,
    )
    context_payload = build_query_context_payload(
        mode=mode,
        base_report=base_report,
        filters_payload=_filters_payload(filters, aggregate_by=aggregate_by if mode == "aggregates" else None),
        representative_rows=representative_rows,
    )
    objective = (
        "Summarize the dominant patterns, notable outliers, and distributional signals in this "
        "query result set while preserving the existing grounded groups."
    )
    return _enrich_report_with_llm(
        base_report=base_report,
        objective=objective,
        context_payload=context_payload,
        analysis_adapter_id=analysis_adapter_id,
        analysis_model=analysis_model,
        analysis_system_prompt=analysis_system_prompt,
        analysis_options=analysis_options,
    )


def explain_comparison_report(
    *,
    report_id: str,
    root: str | Path | None = None,
    analysis_mode: Literal["heuristic", "llm"] = "heuristic",
    analysis_adapter_id: str | None = None,
    analysis_model: str | None = None,
    analysis_system_prompt: str | None = None,
    analysis_options: Mapping[str, JsonValue] | None = None,
    sample_limit: int = DEFAULT_INSIGHT_SAMPLE_LIMIT,
) -> InsightReport:
    filters = QueryFilters(report_id=report_id, limit=sample_limit)
    base_delta_report = summarize_delta_query(
        filters=filters,
        root=root,
        sample_limit=sample_limit,
    )
    base_report = replace(
        base_delta_report,
        source_kind="comparison",
        title="Comparison insight report",
        summary=_comparison_summary(report_id, base_delta_report),
    )
    if analysis_mode == "heuristic":
        return base_report

    representative_rows = query_case_deltas(filters, root=root)
    context_payload = build_comparison_context_payload(
        report_id=report_id,
        base_report=base_report,
        representative_rows=representative_rows,
    )
    objective = (
        "Explain what improved, what regressed, and which transition patterns drive this saved "
        "comparison without inventing new evidence groups."
    )
    return _enrich_report_with_llm(
        base_report=base_report,
        objective=objective,
        context_payload=context_payload,
        analysis_adapter_id=analysis_adapter_id,
        analysis_model=analysis_model,
        analysis_system_prompt=analysis_system_prompt,
        analysis_options=analysis_options,
    )


def _enrich_report_with_llm(
    *,
    base_report: InsightReport,
    objective: str,
    context_payload: Mapping[str, Any],
    analysis_adapter_id: str | None,
    analysis_model: str | None,
    analysis_system_prompt: str | None,
    analysis_options: Mapping[str, JsonValue] | None,
) -> InsightReport:
    if analysis_adapter_id is None or analysis_model is None:
        raise ValueError("LLM analysis requires an explicit analysis model")
    if not base_report.patterns and not base_report.anomalies and not base_report.evidence_links:
        return base_report

    prompt = build_insight_enrichment_prompt(
        base_report=base_report,
        objective=objective,
        context_payload=context_payload,
    )
    adapter = resolve_model(analysis_adapter_id)
    result = adapter.generate(
        ModelRequest(
            model=analysis_model,
            prompt=prompt,
            system_prompt=analysis_system_prompt or DEFAULT_ANALYSIS_SYSTEM_PROMPT,
            options=dict(analysis_options or {}),
        )
    )
    parsed = _parse_llm_payload(result.text)
    summary = parsed.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise RuntimeError("LLM analysis output did not include a non-empty summary")
    _validate_grounded_text(
        summary,
        allowed_identifiers=_allowed_evidence_identifiers(base_report),
        field="summary",
    )

    pattern_updates = _parse_updates(
        parsed.get("patterns"),
        allowed_groups={(item.kind, item.group_key) for item in base_report.patterns},
        allowed_identifiers=_allowed_evidence_identifiers_for_patterns(base_report.patterns),
        field="patterns",
    )
    anomaly_updates = _parse_updates(
        parsed.get("anomalies"),
        allowed_groups={(item.kind, item.group_key) for item in base_report.anomalies},
        allowed_identifiers=_allowed_evidence_identifiers_for_patterns(base_report.anomalies),
        field="anomalies",
    )
    return replace(
        base_report,
        analysis_mode="llm",
        generated_by="llm_enriched_v1",
        summary=summary.strip(),
        patterns=_apply_updates(base_report.patterns, pattern_updates),
        anomalies=_apply_updates(base_report.anomalies, anomaly_updates),
    )


def _parse_llm_payload(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("LLM analysis output was not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("LLM analysis output must be a JSON object")
    return parsed


def _parse_updates(
    payload: object,
    *,
    allowed_groups: set[tuple[str, str | None]],
    allowed_identifiers: set[str],
    field: str,
) -> dict[tuple[str, str | None], str]:
    if payload is None:
        return {}
    if not isinstance(payload, list):
        raise RuntimeError(f"LLM analysis output {field} must be a list")
    updates: dict[tuple[str, str | None], str] = {}
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise RuntimeError(f"LLM analysis output {field}[{index}] must be an object")
        kind = item.get("kind")
        group_key = item.get("group_key")
        summary = item.get("summary")
        if not isinstance(kind, str):
            raise RuntimeError(f"LLM analysis output {field}[{index}].kind must be a string")
        if group_key is not None and not isinstance(group_key, str):
            raise RuntimeError(
                f"LLM analysis output {field}[{index}].group_key must be a string or null"
            )
        if not isinstance(summary, str) or not summary.strip():
            raise RuntimeError(f"LLM analysis output {field}[{index}].summary must be a string")
        group = (kind, group_key)
        if group not in allowed_groups:
            raise RuntimeError(
                f"LLM analysis output referenced unsupported insight group {kind}:{group_key}"
            )
        if group in updates:
            raise RuntimeError(
                f"LLM analysis output referenced duplicate insight group {kind}:{group_key}"
            )
        _validate_grounded_text(
            summary,
            allowed_identifiers=allowed_identifiers,
            field=f"{field}[{index}].summary",
        )
        updates[group] = summary.strip()
    return updates


def _allowed_evidence_identifiers(report: InsightReport) -> set[str]:
    return _collect_evidence_identifiers(
        [
            *report.evidence_links,
            *(ref for item in report.patterns for ref in item.evidence_refs),
            *(ref for item in report.anomalies for ref in item.evidence_refs),
        ]
    )


def _allowed_evidence_identifiers_for_patterns(items: Sequence[InsightPattern]) -> set[str]:
    return _collect_evidence_identifiers(
        [ref for item in items for ref in item.evidence_refs]
    )


def _collect_evidence_identifiers(
    refs: Sequence[Any],
) -> set[str]:
    identifiers: set[str] = set()
    for ref in refs:
        for value in (
            getattr(ref, "label", None),
            getattr(ref, "run_id", None),
            getattr(ref, "report_id", None),
            getattr(ref, "case_id", None),
            getattr(ref, "prompt_id", None),
        ):
            if isinstance(value, str) and value.strip():
                identifiers.add(value.strip())
    return identifiers


def _validate_grounded_text(
    text: str,
    *,
    allowed_identifiers: set[str],
    field: str,
) -> None:
    for identifier in IDENTIFIER_PATTERN.findall(text):
        if identifier not in allowed_identifiers:
            raise RuntimeError(
                f"LLM analysis output referenced unsupported evidence identifier in {field}: "
                f"{identifier}"
            )


def _apply_updates(
    items: Sequence[InsightPattern],
    updates: dict[tuple[str, str | None], str],
) -> tuple[InsightPattern, ...]:
    updated: list[InsightPattern] = []
    for item in items:
        summary = updates.get((item.kind, item.group_key), item.summary)
        updated.append(replace(item, summary=summary))
    return tuple(updated)


def _representative_query_rows(
    *,
    mode: Literal["cases", "deltas", "aggregates"],
    filters: QueryFilters,
    root: str | Path | None,
) -> list[dict[str, Any]]:
    if mode == "deltas":
        return query_case_deltas(replace(filters, limit=6), root=root)
    return query_cases(replace(filters, limit=6), root=root)


def _comparison_summary(report_id: str, base_report: InsightReport) -> str:
    return f"Comparison {report_id}. {base_report.summary}"


def _filters_payload(
    filters: QueryFilters,
    *,
    aggregate_by: str | None = None,
) -> dict[str, Any]:
    return {
        "failure_type": filters.failure_type,
        "model": filters.model,
        "dataset": filters.dataset,
        "run_id": filters.run_id,
        "prompt_id": filters.prompt_id,
        "report_id": filters.report_id,
        "baseline_run_id": filters.baseline_run_id,
        "candidate_run_id": filters.candidate_run_id,
        "delta": filters.delta,
        "aggregate_by": aggregate_by,
        "last_n": filters.last_n,
        "since": filters.since,
        "until": filters.until,
        "limit": filters.limit,
    }
