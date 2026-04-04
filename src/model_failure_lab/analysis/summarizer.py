"""Deterministic heuristic insight reports over query-backed artifacts."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Literal, cast

from model_failure_lab.index import (
    QueryFilters,
    aggregate_case_query,
    aggregate_delta_query,
    count_case_query,
    count_delta_query,
    query_case_deltas,
    query_cases,
)

from .contracts import InsightEvidenceRef, InsightPattern, InsightReport, InsightSampling

DEFAULT_INSIGHT_SAMPLE_LIMIT = 12
MAX_PATTERNS = 3
MAX_ANOMALIES = 3
MAX_EVIDENCE_REFS = 2
DOMINANT_SHARE_THRESHOLD = 0.5
RECURRING_CLUSTER_THRESHOLD = 2


def summarize_query_results(
    *,
    mode: Literal["cases", "deltas", "aggregates"],
    filters: QueryFilters | None = None,
    aggregate_by: Literal["failure_type", "model", "dataset", "prompt_id"] = "failure_type",
    root: str | Path | None = None,
    sample_limit: int = DEFAULT_INSIGHT_SAMPLE_LIMIT,
) -> InsightReport:
    active_filters = filters or QueryFilters()
    if mode == "cases":
        return summarize_case_query(
            filters=active_filters,
            root=root,
            sample_limit=sample_limit,
        )
    if mode == "deltas":
        return summarize_delta_query(
            filters=active_filters,
            root=root,
            sample_limit=sample_limit,
        )
    return summarize_aggregate_query(
        group_by=aggregate_by,
        filters=active_filters,
        root=root,
        sample_limit=sample_limit,
    )


def summarize_case_query(
    *,
    filters: QueryFilters,
    root: str | Path | None = None,
    sample_limit: int = DEFAULT_INSIGHT_SAMPLE_LIMIT,
) -> InsightReport:
    total_matches = count_case_query(filters, root=root)
    sampled_rows = query_cases(_with_limit(filters, sample_limit), root=root)
    sampling = _build_sampling(
        total_matches=total_matches,
        sampled_matches=len(sampled_rows),
        sample_limit=sample_limit,
    )
    if total_matches == 0:
        return InsightReport(
            analysis_mode="heuristic",
            source_kind="cases",
            title="Case insight report",
            summary="No matching failure cases were found for the current query.",
            generated_by="heuristic_v1",
            sampling=sampling,
            patterns=(),
            anomalies=(),
            evidence_links=(),
        )

    dominant_failures = aggregate_case_query(
        "failure_type",
        _with_limit(filters, MAX_PATTERNS),
        root=root,
    )
    prompt_clusters = aggregate_case_query(
        "prompt_id",
        _with_limit(filters, sample_limit),
        root=root,
    )
    model_distribution = (
        aggregate_case_query("model", _with_limit(filters, MAX_PATTERNS), root=root)
        if filters.model is None
        else []
    )
    dataset_distribution = (
        aggregate_case_query("dataset", _with_limit(filters, MAX_PATTERNS), root=root)
        if filters.dataset is None
        else []
    )

    patterns: list[InsightPattern] = []
    for group in dominant_failures[:2]:
        group_key = cast(str, group["group_key"])
        evidence = _build_run_case_refs(
            query_cases(
                _with_limit(replace(filters, failure_type=group_key), MAX_EVIDENCE_REFS),
                root=root,
            )
        )
        count = int(group["case_count"])
        share = _share(count, total_matches)
        patterns.append(
            InsightPattern(
                kind="failure_type",
                label=str(group["group_label"]),
                summary=_failure_pattern_summary(str(group["group_label"]), count, share),
                group_key=group_key,
                count=count,
                share=share,
                evidence_refs=evidence,
            )
        )

    for group in prompt_clusters:
        count = int(group["case_count"])
        if count < RECURRING_CLUSTER_THRESHOLD:
            continue
        group_key = cast(str, group["group_key"])
        evidence = _build_run_case_refs(
            query_cases(
                _with_limit(replace(filters, prompt_id=group_key), MAX_EVIDENCE_REFS),
                root=root,
            )
        )
        patterns.append(
            InsightPattern(
                kind="prompt_cluster",
                label=str(group["group_label"]),
                summary=(
                    f"Prompt {group['group_label']} recurs across {count} matched failure cases."
                ),
                group_key=group_key,
                count=count,
                share=_share(count, total_matches),
                evidence_refs=evidence,
            )
        )
        break

    distribution_patterns = _distribution_patterns(
        total_matches=total_matches,
        model_distribution=model_distribution,
        dataset_distribution=dataset_distribution,
        filters=filters,
        root=root,
    )
    patterns.extend(distribution_patterns)
    patterns = _dedupe_patterns(patterns)[:MAX_PATTERNS]

    anomalies = _case_anomalies(sampled_rows, patterns, total_matches)
    evidence_links = _collect_unique_evidence(patterns, anomalies)

    return InsightReport(
        analysis_mode="heuristic",
        source_kind="cases",
        title="Case insight report",
        summary=_build_case_summary(total_matches, patterns, anomalies, sampling),
        generated_by="heuristic_v1",
        sampling=sampling,
        patterns=tuple(patterns),
        anomalies=tuple(anomalies),
        evidence_links=evidence_links,
    )


def summarize_delta_query(
    *,
    filters: QueryFilters,
    root: str | Path | None = None,
    sample_limit: int = DEFAULT_INSIGHT_SAMPLE_LIMIT,
) -> InsightReport:
    total_matches = count_delta_query(filters, root=root)
    sampled_rows = query_case_deltas(_with_limit(filters, sample_limit), root=root)
    sampling = _build_sampling(
        total_matches=total_matches,
        sampled_matches=len(sampled_rows),
        sample_limit=sample_limit,
    )
    if total_matches == 0:
        return InsightReport(
            analysis_mode="heuristic",
            source_kind="deltas",
            title="Delta insight report",
            summary="No matching comparison deltas were found for the current query.",
            generated_by="heuristic_v1",
            sampling=sampling,
            patterns=(),
            anomalies=(),
            evidence_links=(),
        )

    delta_kind_groups = aggregate_delta_query(
        "delta_kind",
        _with_limit(filters, MAX_PATTERNS),
        root=root,
    )
    transition_groups = aggregate_delta_query(
        "transition_type",
        _with_limit(filters, MAX_PATTERNS),
        root=root,
    )

    patterns: list[InsightPattern] = []
    for group in delta_kind_groups[:2]:
        group_key = cast(str, group["group_key"])
        evidence = _build_comparison_case_refs(
            query_case_deltas(
                _with_limit(replace(filters, delta=group_key), MAX_EVIDENCE_REFS),
                root=root,
            )
        )
        count = int(group["case_count"])
        share = _share(count, total_matches)
        patterns.append(
            InsightPattern(
                kind="delta_kind",
                label=str(group["group_label"]),
                summary=_delta_pattern_summary(str(group["group_label"]), count, share),
                group_key=group_key,
                count=count,
                share=share,
                evidence_refs=evidence,
            )
        )

    for group in transition_groups:
        group_key = cast(str, group["group_key"])
        if any(pattern.group_key == group_key for pattern in patterns):
            continue
        evidence = _build_comparison_case_refs(
            query_case_deltas(
                _with_limit(replace(filters, delta=group_key), MAX_EVIDENCE_REFS),
                root=root,
            )
        )
        count = int(group["case_count"])
        patterns.append(
            InsightPattern(
                kind="transition_type",
                label=str(group["group_label"]),
                summary=(
                    f"Transition {group['group_label']} appears in {count} matched deltas."
                ),
                group_key=group_key,
                count=count,
                share=_share(count, total_matches),
                evidence_refs=evidence,
            )
        )
        break

    patterns = _dedupe_patterns(patterns)[:MAX_PATTERNS]
    anomalies = _delta_anomalies(sampled_rows, patterns, total_matches)
    evidence_links = _collect_unique_evidence(patterns, anomalies)

    return InsightReport(
        analysis_mode="heuristic",
        source_kind="deltas",
        title="Delta insight report",
        summary=_build_delta_summary(total_matches, patterns, anomalies, sampling),
        generated_by="heuristic_v1",
        sampling=sampling,
        patterns=tuple(patterns),
        anomalies=tuple(anomalies),
        evidence_links=evidence_links,
    )


def summarize_aggregate_query(
    *,
    group_by: Literal["failure_type", "model", "dataset", "prompt_id"],
    filters: QueryFilters,
    root: str | Path | None = None,
    sample_limit: int = DEFAULT_INSIGHT_SAMPLE_LIMIT,
) -> InsightReport:
    total_matches = count_case_query(filters, root=root)
    aggregate_rows = aggregate_case_query(
        group_by,
        _with_limit(filters, sample_limit),
        root=root,
    )
    sampling = _build_sampling(
        total_matches=total_matches,
        sampled_matches=min(total_matches, sample_limit),
        sample_limit=sample_limit,
    )
    if total_matches == 0 or not aggregate_rows:
        return InsightReport(
            analysis_mode="heuristic",
            source_kind="aggregates",
            title="Aggregate insight report",
            summary="No matching aggregate rows were found for the current query.",
            generated_by="heuristic_v1",
            sampling=sampling,
            patterns=(),
            anomalies=(),
            evidence_links=(),
        )

    patterns: list[InsightPattern] = []
    for group in aggregate_rows[:MAX_PATTERNS]:
        group_key = cast(str, group["group_key"])
        representative_filters = _case_group_filters(
            group_by=group_by,
            group_key=group_key,
            filters=filters,
        )
        evidence = _build_run_case_refs(
            query_cases(_with_limit(representative_filters, MAX_EVIDENCE_REFS), root=root)
        )
        count = int(group["case_count"])
        share = _share(count, total_matches)
        patterns.append(
            InsightPattern(
                kind="aggregate_group",
                label=str(group["group_label"]),
                summary=(
                    f"{group['group_label']} accounts for {count} matched failure cases "
                    f"within the {group_by} grouping."
                ),
                group_key=group_key,
                count=count,
                share=share,
                evidence_refs=evidence,
            )
        )

    anomalies = tuple(patterns[-1:]) if len(patterns) > 1 else ()
    evidence_links = _collect_unique_evidence(patterns, list(anomalies))
    return InsightReport(
        analysis_mode="heuristic",
        source_kind="aggregates",
        title="Aggregate insight report",
        summary=_build_aggregate_summary(group_by, total_matches, patterns, sampling),
        generated_by="heuristic_v1",
        sampling=sampling,
        patterns=tuple(patterns),
        anomalies=anomalies,
        evidence_links=evidence_links,
    )


def _with_limit(filters: QueryFilters, limit: int) -> QueryFilters:
    return replace(filters, limit=max(1, limit))


def _build_sampling(
    *,
    total_matches: int,
    sampled_matches: int,
    sample_limit: int,
) -> InsightSampling:
    return InsightSampling(
        total_matches=total_matches,
        sampled_matches=sampled_matches,
        sample_limit=max(1, sample_limit),
        truncated=total_matches > sampled_matches,
        strategy="ranked_representative_groups",
    )


def _distribution_patterns(
    *,
    total_matches: int,
    model_distribution: list[dict[str, Any]],
    dataset_distribution: list[dict[str, Any]],
    filters: QueryFilters,
    root: str | Path | None,
) -> list[InsightPattern]:
    patterns: list[InsightPattern] = []
    if model_distribution:
        top_model = model_distribution[0]
        model_count = int(top_model["case_count"])
        model_share = _share(model_count, total_matches)
        if model_share is not None and model_share >= DOMINANT_SHARE_THRESHOLD:
            model_key = cast(str, top_model["group_key"])
            evidence = _build_run_case_refs(
                query_cases(
                    _with_limit(replace(filters, model=model_key), MAX_EVIDENCE_REFS),
                    root=root,
                )
            )
            patterns.append(
                InsightPattern(
                    kind="model_skew",
                    label=str(top_model["group_label"]),
                    summary=(
                        f"Model {top_model['group_label']} carries {model_count} of the matched "
                        "failure cases."
                    ),
                    group_key=model_key,
                    count=model_count,
                    share=model_share,
                    evidence_refs=evidence,
                )
            )
    if dataset_distribution:
        top_dataset = dataset_distribution[0]
        dataset_count = int(top_dataset["case_count"])
        dataset_share = _share(dataset_count, total_matches)
        if dataset_share is not None and dataset_share >= DOMINANT_SHARE_THRESHOLD:
            dataset_key = cast(str, top_dataset["group_key"])
            evidence = _build_run_case_refs(
                query_cases(
                    _with_limit(replace(filters, dataset=dataset_key), MAX_EVIDENCE_REFS),
                    root=root,
                )
            )
            patterns.append(
                InsightPattern(
                    kind="dataset_skew",
                    label=str(top_dataset["group_label"]),
                    summary=(
                        f"Dataset {top_dataset['group_label']} contributes {dataset_count} of the "
                        "matched failure cases."
                    ),
                    group_key=dataset_key,
                    count=dataset_count,
                    share=dataset_share,
                    evidence_refs=evidence,
                )
            )
    return patterns


def _case_anomalies(
    sampled_rows: list[dict[str, Any]],
    patterns: list[InsightPattern],
    total_matches: int,
) -> list[InsightPattern]:
    dominant_groups = {pattern.group_key for pattern in patterns if pattern.kind == "failure_type"}
    candidates = [
        row
        for row in sampled_rows
        if row.get("failure_type") not in dominant_groups or row.get("prompt_id") not in dominant_groups
    ]
    candidates.sort(
        key=lambda row: (
            -(float(row["confidence"]) if row.get("confidence") is not None else 0.0),
            str(row["created_at"]),
            str(row["run_id"]),
            str(row["case_id"]),
        ),
        reverse=True,
    )
    anomalies: list[InsightPattern] = []
    for row in candidates[:MAX_ANOMALIES]:
        anomalies.append(
            InsightPattern(
                kind="outlier_case",
                label=str(row["case_id"]),
                summary=(
                    f"Case {row['case_id']} remains an outlier with "
                    f"{row.get('failure_type') or 'unclassified'} evidence."
                ),
                group_key=str(row["case_id"]),
                count=1,
                share=_share(1, total_matches),
                evidence_refs=_build_run_case_refs([row]),
            )
        )
    return anomalies


def _delta_anomalies(
    sampled_rows: list[dict[str, Any]],
    patterns: list[InsightPattern],
    total_matches: int,
) -> list[InsightPattern]:
    dominant_groups = {pattern.group_key for pattern in patterns if pattern.kind == "delta_kind"}
    candidates = [
        row
        for row in sampled_rows
        if row.get("delta_kind") not in dominant_groups or row.get("transition_type") == "failure_type_swap"
    ]
    anomalies: list[InsightPattern] = []
    for row in candidates[:MAX_ANOMALIES]:
        anomalies.append(
            InsightPattern(
                kind="outlier_delta",
                label=str(row["case_id"]),
                summary=(
                    f"Case {row['case_id']} is a low-frequency delta with "
                    f"{row.get('transition_label') or row.get('delta_kind')}."
                ),
                group_key=str(row["case_id"]),
                count=1,
                share=_share(1, total_matches),
                evidence_refs=_build_comparison_case_refs([row]),
            )
        )
    return anomalies


def _case_group_filters(
    *,
    group_by: Literal["failure_type", "model", "dataset", "prompt_id"],
    group_key: str,
    filters: QueryFilters,
) -> QueryFilters:
    if group_by == "failure_type":
        return replace(filters, failure_type=group_key)
    if group_by == "model":
        return replace(filters, model=group_key)
    if group_by == "dataset":
        return replace(filters, dataset=group_key)
    return replace(filters, prompt_id=group_key)


def _build_run_case_refs(rows: list[dict[str, Any]]) -> tuple[InsightEvidenceRef, ...]:
    refs: list[InsightEvidenceRef] = []
    for row in rows[:MAX_EVIDENCE_REFS]:
        refs.append(
            InsightEvidenceRef(
                kind="run_case",
                label=f"{row['run_id']}:{row['case_id']}",
                run_id=str(row["run_id"]),
                case_id=str(row["case_id"]),
                prompt_id=str(row["prompt_id"]),
                section="evidence",
            )
        )
    return tuple(refs)


def _build_comparison_case_refs(rows: list[dict[str, Any]]) -> tuple[InsightEvidenceRef, ...]:
    refs: list[InsightEvidenceRef] = []
    for row in rows[:MAX_EVIDENCE_REFS]:
        refs.append(
            InsightEvidenceRef(
                kind="comparison_case",
                label=f"{row['report_id']}:{row['case_id']}",
                report_id=str(row["report_id"]),
                case_id=str(row["case_id"]),
                prompt_id=str(row["prompt_id"]),
                section="transitions",
                transition_type=str(row["transition_type"]),
            )
        )
    return tuple(refs)


def _collect_unique_evidence(
    patterns: list[InsightPattern],
    anomalies: list[InsightPattern],
) -> tuple[InsightEvidenceRef, ...]:
    seen: set[tuple[str | None, str | None, str | None]] = set()
    refs: list[InsightEvidenceRef] = []
    for item in [*patterns, *anomalies]:
        for ref in item.evidence_refs:
            key = (ref.kind, ref.run_id or ref.report_id, ref.case_id)
            if key in seen:
                continue
            seen.add(key)
            refs.append(ref)
    return tuple(refs)


def _dedupe_patterns(patterns: list[InsightPattern]) -> list[InsightPattern]:
    seen: set[tuple[str, str | None]] = set()
    deduped: list[InsightPattern] = []
    for pattern in patterns:
        key = (pattern.kind, pattern.group_key)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(pattern)
    return deduped


def _failure_pattern_summary(label: str, count: int, share: float | None) -> str:
    if share is not None and share >= DOMINANT_SHARE_THRESHOLD:
        return f"{label} dominates this result set with {count} matched failure cases."
    return f"{label} appears across {count} matched failure cases."


def _delta_pattern_summary(label: str, count: int, share: float | None) -> str:
    if share is not None and share >= DOMINANT_SHARE_THRESHOLD:
        return f"{label} drives most of the matched comparison deltas ({count} cases)."
    return f"{label} appears in {count} matched comparison deltas."


def _build_case_summary(
    total_matches: int,
    patterns: list[InsightPattern],
    anomalies: list[InsightPattern],
    sampling: InsightSampling,
) -> str:
    lead = patterns[0].summary if patterns else "No dominant failure pattern was identified."
    anomaly_note = (
        f" {len(anomalies)} outlier cases are highlighted for inspection." if anomalies else ""
    )
    sampling_note = (
        f" Representative evidence is bounded to {sampling.sampled_matches} of {total_matches} "
        "matched cases."
        if sampling.truncated
        else f" Representative evidence covers all {total_matches} matched cases."
    )
    return f"{lead}{anomaly_note}{sampling_note}"


def _build_delta_summary(
    total_matches: int,
    patterns: list[InsightPattern],
    anomalies: list[InsightPattern],
    sampling: InsightSampling,
) -> str:
    lead = patterns[0].summary if patterns else "No dominant comparison delta was identified."
    anomaly_note = (
        f" {len(anomalies)} low-frequency deltas are highlighted for follow-up."
        if anomalies
        else ""
    )
    sampling_note = (
        f" Representative evidence is bounded to {sampling.sampled_matches} of {total_matches} "
        "matched deltas."
        if sampling.truncated
        else f" Representative evidence covers all {total_matches} matched deltas."
    )
    return f"{lead}{anomaly_note}{sampling_note}"


def _build_aggregate_summary(
    group_by: str,
    total_matches: int,
    patterns: list[InsightPattern],
    sampling: InsightSampling,
) -> str:
    lead = patterns[0].summary if patterns else "No dominant aggregate group was identified."
    sampling_note = (
        f" Visible groups are bounded to the top {sampling.sampled_matches} {group_by} buckets."
        if sampling.truncated
        else f" Visible groups account for all {total_matches} matched failure cases."
    )
    return f"{lead}{sampling_note}"


def _share(count: int, total: int) -> float | None:
    if total <= 0:
        return None
    return count / total
