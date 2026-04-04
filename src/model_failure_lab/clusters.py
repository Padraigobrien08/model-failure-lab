"""Deterministic recurring-failure clusters over the derived local query index."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from model_failure_lab.index.builder import ensure_query_index, query_index_path
from model_failure_lab.index.query import QueryFilters
from model_failure_lab.schemas import JsonValue

DEFAULT_CLUSTER_LIMIT = 20
DEFAULT_CLUSTER_OCCURRENCE_LIMIT = 50
RECURRING_SCOPE_THRESHOLD = 2


@dataclass(slots=True, frozen=True)
class ClusterEvidenceRef:
    kind: str
    label: str
    run_id: str | None
    report_id: str | None
    case_id: str | None
    prompt_id: str | None
    section: str | None
    transition_type: str | None

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
class FailureClusterOccurrence:
    cluster_id: str
    cluster_kind: str
    created_at: str
    dataset_scope: str | None
    dataset: str | None
    run_id: str | None
    model: str | None
    report_id: str | None
    case_id: str
    prompt_id: str
    prompt: str
    tags: tuple[str, ...]
    failure_type: str | None
    expectation_verdict: str | None
    error_stage: str | None
    delta_kind: str | None
    transition_type: str | None
    baseline_run_id: str | None
    candidate_run_id: str | None
    baseline_model: str | None
    candidate_model: str | None
    baseline_failure_type: str | None
    candidate_failure_type: str | None
    baseline_expectation_verdict: str | None
    candidate_expectation_verdict: str | None
    signal_verdict: str | None
    severity: float | None

    @property
    def artifact_scope_id(self) -> str:
        if self.cluster_kind == "comparison_delta":
            return self.report_id or self.case_id
        return self.run_id or self.case_id

    @property
    def evidence_ref(self) -> ClusterEvidenceRef:
        if self.cluster_kind == "comparison_delta":
            return ClusterEvidenceRef(
                kind="comparison_case",
                label=f"{self.report_id}:{self.case_id}",
                run_id=None,
                report_id=self.report_id,
                case_id=self.case_id,
                prompt_id=self.prompt_id,
                section="transitions",
                transition_type=self.transition_type,
            )
        return ClusterEvidenceRef(
            kind="run_case",
            label=f"{self.run_id}:{self.case_id}",
            run_id=self.run_id,
            report_id=None,
            case_id=self.case_id,
            prompt_id=self.prompt_id,
            section="evidence",
            transition_type=None,
        )

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "cluster_id": self.cluster_id,
            "cluster_kind": self.cluster_kind,
            "created_at": self.created_at,
            "dataset_scope": self.dataset_scope,
            "dataset": self.dataset,
            "run_id": self.run_id,
            "model": self.model,
            "report_id": self.report_id,
            "case_id": self.case_id,
            "prompt_id": self.prompt_id,
            "prompt": self.prompt,
            "tags": list(self.tags),
            "failure_type": self.failure_type,
            "expectation_verdict": self.expectation_verdict,
            "error_stage": self.error_stage,
            "delta_kind": self.delta_kind,
            "transition_type": self.transition_type,
            "baseline_run_id": self.baseline_run_id,
            "candidate_run_id": self.candidate_run_id,
            "baseline_model": self.baseline_model,
            "candidate_model": self.candidate_model,
            "baseline_failure_type": self.baseline_failure_type,
            "candidate_failure_type": self.candidate_failure_type,
            "baseline_expectation_verdict": self.baseline_expectation_verdict,
            "candidate_expectation_verdict": self.candidate_expectation_verdict,
            "signal_verdict": self.signal_verdict,
            "severity": _rounded_or_none(self.severity),
            "evidence_ref": self.evidence_ref.to_payload(),
        }


@dataclass(slots=True, frozen=True)
class FailureClusterSummary:
    cluster_id: str
    cluster_kind: str
    label: str
    summary: str
    occurrence_count: int
    scope_count: int
    first_seen_at: str
    last_seen_at: str
    datasets: tuple[str, ...]
    models: tuple[str, ...]
    failure_types: tuple[str, ...]
    transition_types: tuple[str, ...]
    recent_severity: float | None
    representative_evidence: tuple[ClusterEvidenceRef, ...]

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "cluster_id": self.cluster_id,
            "cluster_kind": self.cluster_kind,
            "label": self.label,
            "summary": self.summary,
            "occurrence_count": self.occurrence_count,
            "scope_count": self.scope_count,
            "first_seen_at": self.first_seen_at,
            "last_seen_at": self.last_seen_at,
            "datasets": list(self.datasets),
            "models": list(self.models),
            "failure_types": list(self.failure_types),
            "transition_types": list(self.transition_types),
            "recent_severity": _rounded_or_none(self.recent_severity),
            "representative_evidence": [
                evidence.to_payload() for evidence in self.representative_evidence
            ],
        }


@dataclass(slots=True, frozen=True)
class FailureClusterDetail:
    summary: FailureClusterSummary
    occurrences: tuple[FailureClusterOccurrence, ...]

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "summary": self.summary.to_payload(),
            "occurrences": [row.to_payload() for row in self.occurrences],
        }


def list_failure_clusters(
    filters: QueryFilters | None = None,
    *,
    cluster_kind: str | None = None,
    recurring_only: bool = True,
    limit: int | None = None,
    root: str | Path | None = None,
) -> tuple[FailureClusterSummary, ...]:
    active_filters = filters or QueryFilters()
    ensure_query_index(root=root)
    with _connection(root=root) as connection:
        occurrences = _load_cluster_occurrences(
            connection,
            filters=active_filters,
            cluster_kind=cluster_kind,
        )
    summaries = _summarize_cluster_occurrences(occurrences)
    if recurring_only:
        summaries = [summary for summary in summaries if summary.scope_count >= RECURRING_SCOPE_THRESHOLD]
    summary_limit = max(limit or active_filters.limit or DEFAULT_CLUSTER_LIMIT, 1)
    return tuple(
        sorted(
            summaries,
            key=lambda summary: (
                -summary.scope_count,
                -summary.occurrence_count,
                summary.cluster_kind,
                summary.last_seen_at,
                summary.cluster_id,
            ),
        )[:summary_limit]
    )


def get_failure_cluster_detail(
    cluster_id: str,
    *,
    root: str | Path | None = None,
    limit: int = DEFAULT_CLUSTER_OCCURRENCE_LIMIT,
) -> FailureClusterDetail:
    ensure_query_index(root=root)
    with _connection(root=root) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM cluster_occurrences
            WHERE cluster_id = ?
            ORDER BY created_at DESC, occurrence_id DESC
            LIMIT ?
            """,
            (cluster_id, max(limit, 1)),
        ).fetchall()
    occurrences = tuple(_hydrate_cluster_occurrence(row) for row in rows)
    if not occurrences:
        raise ValueError(f"cluster not found in query index: {cluster_id}")
    summary = _summarize_cluster_occurrences(list(occurrences))[0]
    return FailureClusterDetail(summary=summary, occurrences=occurrences)


def list_clusters_for_comparison(
    comparison_id: str,
    *,
    recurring_only: bool = True,
    limit: int = 3,
    root: str | Path | None = None,
) -> tuple[FailureClusterSummary, ...]:
    ensure_query_index(root=root)
    with _connection(root=root) as connection:
        cluster_rows = connection.execute(
            """
            SELECT DISTINCT cluster_id
            FROM cluster_occurrences
            WHERE cluster_kind = 'comparison_delta' AND report_id = ?
            """,
            (comparison_id,),
        ).fetchall()
        cluster_ids = [str(row["cluster_id"]) for row in cluster_rows]
        if not cluster_ids:
            return ()
        rows = connection.execute(
            f"""
            SELECT *
            FROM cluster_occurrences
            WHERE cluster_id IN ({",".join("?" for _ in cluster_ids)})
            ORDER BY created_at DESC, occurrence_id DESC
            """,
            cluster_ids,
        ).fetchall()
    summaries = _summarize_cluster_occurrences(
        [_hydrate_cluster_occurrence(row) for row in rows]
    )
    if recurring_only:
        summaries = [summary for summary in summaries if summary.scope_count >= RECURRING_SCOPE_THRESHOLD]
    return tuple(
        sorted(
            summaries,
            key=lambda summary: (
                -summary.scope_count,
                -summary.occurrence_count,
                -abs(summary.recent_severity or 0.0),
                summary.cluster_id,
            ),
        )[: max(limit, 1)]
    )


def _connection(*, root: str | Path | None = None) -> sqlite3.Connection:
    connection = sqlite3.connect(query_index_path(root=root))
    connection.row_factory = sqlite3.Row
    return connection


def _load_cluster_occurrences(
    connection: sqlite3.Connection,
    *,
    filters: QueryFilters,
    cluster_kind: str | None,
) -> list[FailureClusterOccurrence]:
    selected_run_ids = _selected_run_ids(connection, filters)
    selected_report_ids = _selected_report_ids(connection, filters)
    query = ["SELECT * FROM cluster_occurrences WHERE 1 = 1"]
    params: list[Any] = []

    if cluster_kind is not None:
        query.append("AND cluster_kind = ?")
        params.append(cluster_kind)
    if filters.dataset is not None:
        query.append("AND (dataset_scope = ? OR dataset = ?)")
        params.extend([filters.dataset, filters.dataset])
    if filters.model is not None:
        query.append(
            """
            AND (
                model = ?
                OR baseline_model = ?
                OR candidate_model = ?
            )
            """
        )
        params.extend([filters.model, filters.model, filters.model])
    if filters.failure_type is not None:
        query.append(
            """
            AND (
                failure_type = ?
                OR baseline_failure_type = ?
                OR candidate_failure_type = ?
            )
            """
        )
        params.extend([filters.failure_type, filters.failure_type, filters.failure_type])
    if filters.run_id is not None:
        query.append("AND run_id = ?")
        params.append(filters.run_id)
    if filters.report_id is not None:
        query.append("AND report_id = ?")
        params.append(filters.report_id)
    if filters.baseline_run_id is not None:
        query.append("AND baseline_run_id = ?")
        params.append(filters.baseline_run_id)
    if filters.candidate_run_id is not None:
        query.append("AND candidate_run_id = ?")
        params.append(filters.candidate_run_id)
    if filters.prompt_id is not None:
        query.append("AND prompt_id = ?")
        params.append(filters.prompt_id)
    if filters.delta is not None:
        if filters.delta in {"regression", "improvement", "swap", "error_change"}:
            query.append("AND delta_kind = ?")
            params.append(filters.delta)
        else:
            query.append("AND transition_type = ?")
            params.append(filters.delta)
    if filters.since is not None:
        query.append("AND created_at >= ?")
        params.append(filters.since)
    if filters.until is not None:
        query.append("AND created_at <= ?")
        params.append(filters.until)
    if selected_run_ids is not None or selected_report_ids is not None:
        clauses: list[str] = []
        if selected_run_ids:
            clauses.append(
                f"(cluster_kind = 'run_case' AND run_id IN ({','.join('?' for _ in selected_run_ids)}))"
            )
            params.extend(selected_run_ids)
        if selected_report_ids:
            clauses.append(
                f"(cluster_kind = 'comparison_delta' AND report_id IN ({','.join('?' for _ in selected_report_ids)}))"
            )
            params.extend(selected_report_ids)
        if clauses:
            query.append(f"AND ({' OR '.join(clauses)})")

    query.append("ORDER BY created_at DESC, occurrence_id DESC")
    rows = connection.execute(" ".join(query), params).fetchall()
    return [_hydrate_cluster_occurrence(row) for row in rows]


def _selected_run_ids(
    connection: sqlite3.Connection,
    filters: QueryFilters,
) -> list[str] | None:
    if filters.last_n is None:
        return None
    query = ["SELECT run_id FROM runs WHERE 1 = 1"]
    params: list[Any] = []
    if filters.model is not None:
        query.append("AND model = ?")
        params.append(filters.model)
    if filters.dataset is not None:
        query.append("AND dataset = ?")
        params.append(filters.dataset)
    if filters.since is not None:
        query.append("AND created_at >= ?")
        params.append(filters.since)
    if filters.until is not None:
        query.append("AND created_at <= ?")
        params.append(filters.until)
    query.append("ORDER BY created_at DESC, run_id DESC LIMIT ?")
    params.append(max(filters.last_n, 1))
    rows = connection.execute(" ".join(query), params).fetchall()
    return [str(row["run_id"]) for row in rows]


def _selected_report_ids(
    connection: sqlite3.Connection,
    filters: QueryFilters,
) -> list[str] | None:
    if filters.last_n is None:
        return None
    query = ["SELECT report_id FROM comparisons WHERE 1 = 1"]
    params: list[Any] = []
    if filters.dataset is not None:
        query.append("AND dataset = ?")
        params.append(filters.dataset)
    if filters.model is not None:
        query.append("AND (baseline_model = ? OR candidate_model = ?)")
        params.extend([filters.model, filters.model])
    if filters.since is not None:
        query.append("AND created_at >= ?")
        params.append(filters.since)
    if filters.until is not None:
        query.append("AND created_at <= ?")
        params.append(filters.until)
    query.append("ORDER BY created_at DESC, report_id DESC LIMIT ?")
    params.append(max(filters.last_n, 1))
    rows = connection.execute(" ".join(query), params).fetchall()
    return [str(row["report_id"]) for row in rows]


def _hydrate_cluster_occurrence(row: sqlite3.Row) -> FailureClusterOccurrence:
    return FailureClusterOccurrence(
        cluster_id=str(row["cluster_id"]),
        cluster_kind=str(row["cluster_kind"]),
        created_at=str(row["created_at"]),
        dataset_scope=_string_or_none(row["dataset_scope"]),
        dataset=_string_or_none(row["dataset"]),
        run_id=_string_or_none(row["run_id"]),
        model=_string_or_none(row["model"]),
        report_id=_string_or_none(row["report_id"]),
        case_id=str(row["case_id"]),
        prompt_id=str(row["prompt_id"]),
        prompt=str(row["prompt"]),
        tags=tuple(json.loads(str(row["tags_json"]))),
        failure_type=_string_or_none(row["failure_type"]),
        expectation_verdict=_string_or_none(row["expectation_verdict"]),
        error_stage=_string_or_none(row["error_stage"]),
        delta_kind=_string_or_none(row["delta_kind"]),
        transition_type=_string_or_none(row["transition_type"]),
        baseline_run_id=_string_or_none(row["baseline_run_id"]),
        candidate_run_id=_string_or_none(row["candidate_run_id"]),
        baseline_model=_string_or_none(row["baseline_model"]),
        candidate_model=_string_or_none(row["candidate_model"]),
        baseline_failure_type=_string_or_none(row["baseline_failure_type"]),
        candidate_failure_type=_string_or_none(row["candidate_failure_type"]),
        baseline_expectation_verdict=_string_or_none(row["baseline_expectation_verdict"]),
        candidate_expectation_verdict=_string_or_none(row["candidate_expectation_verdict"]),
        signal_verdict=_string_or_none(row["signal_verdict"]),
        severity=_float_or_none(row["severity"]),
    )


def _summarize_cluster_occurrences(
    occurrences: list[FailureClusterOccurrence],
) -> list[FailureClusterSummary]:
    if not occurrences:
        return []

    grouped: dict[str, list[FailureClusterOccurrence]] = {}
    for occurrence in occurrences:
        grouped.setdefault(occurrence.cluster_id, []).append(occurrence)

    summaries: list[FailureClusterSummary] = []
    for cluster_id, rows in grouped.items():
        ordered = sorted(
            rows,
            key=lambda row: (row.created_at, row.artifact_scope_id, row.case_id),
        )
        latest = ordered[-1]
        scope_ids = {row.artifact_scope_id for row in ordered}
        datasets = tuple(
            sorted(
                {
                    value
                    for row in ordered
                    for value in (row.dataset_scope or row.dataset,)
                    if value is not None
                }
            )
        )
        models = tuple(
            sorted(
                {
                    value
                    for row in ordered
                    for value in _model_labels(row)
                    if value is not None
                }
            )
        )
        failure_types = tuple(
            sorted(
                {
                    value
                    for row in ordered
                    for value in (
                        row.failure_type,
                        row.baseline_failure_type,
                        row.candidate_failure_type,
                    )
                    if value is not None and value != "no_failure"
                }
            )
        )
        transition_types = tuple(
            sorted({row.transition_type for row in ordered if row.transition_type is not None})
        )
        representative_evidence = tuple(
            row.evidence_ref
            for row in sorted(
                ordered,
                key=lambda row: (row.created_at, row.artifact_scope_id, row.case_id),
                reverse=True,
            )[:3]
        )
        label = _build_cluster_label(latest, failure_types=failure_types)
        summary = _build_cluster_summary_text(
            latest,
            occurrence_count=len(ordered),
            scope_count=len(scope_ids),
            failure_types=failure_types,
        )
        summaries.append(
            FailureClusterSummary(
                cluster_id=cluster_id,
                cluster_kind=latest.cluster_kind,
                label=label,
                summary=summary,
                occurrence_count=len(ordered),
                scope_count=len(scope_ids),
                first_seen_at=ordered[0].created_at,
                last_seen_at=latest.created_at,
                datasets=datasets,
                models=models,
                failure_types=failure_types,
                transition_types=transition_types,
                recent_severity=latest.severity,
                representative_evidence=representative_evidence,
            )
        )
    return summaries


def _build_cluster_label(
    occurrence: FailureClusterOccurrence,
    *,
    failure_types: tuple[str, ...],
) -> str:
    if occurrence.cluster_kind == "comparison_delta":
        transition_label = (occurrence.transition_type or "comparison_delta").replace("_", " ")
        failure_label = failure_types[0] if failure_types else "mixed failure"
        return f"{failure_label} · {transition_label}"
    failure_label = failure_types[0] if failure_types else (occurrence.error_stage or "failure")
    verdict_label = occurrence.expectation_verdict or "observed"
    return f"{failure_label} · {verdict_label}"


def _build_cluster_summary_text(
    occurrence: FailureClusterOccurrence,
    *,
    occurrence_count: int,
    scope_count: int,
    failure_types: tuple[str, ...],
) -> str:
    dataset_label = occurrence.dataset_scope or occurrence.dataset or "unscoped dataset"
    if occurrence.cluster_kind == "comparison_delta":
        transition_label = (occurrence.transition_type or "comparison_delta").replace("_", " ")
        failure_label = failure_types[0] if failure_types else "mixed failure"
        return (
            f"{failure_label} {transition_label} recurred {occurrence_count} times across "
            f"{scope_count} saved comparisons in {dataset_label}."
        )
    failure_label = failure_types[0] if failure_types else (occurrence.error_stage or "failure")
    return (
        f"{failure_label} recurred {occurrence_count} times across {scope_count} saved runs "
        f"in {dataset_label}."
    )


def _model_labels(row: FailureClusterOccurrence) -> tuple[str | None, ...]:
    if row.cluster_kind == "comparison_delta":
        model_label = None
        if row.baseline_model is not None or row.candidate_model is not None:
            model_label = f"{row.baseline_model or 'unknown'}→{row.candidate_model or 'unknown'}"
        return (model_label,)
    return (row.model,)


def _rounded_or_none(value: float | None) -> float | None:
    return round(value, 6) if value is not None else None


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
