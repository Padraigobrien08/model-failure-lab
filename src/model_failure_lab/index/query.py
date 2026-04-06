"""Reusable structured query helpers over the derived local query index."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .builder import ensure_query_index, query_index_path

AggregateKey = Literal["failure_type", "model", "dataset", "prompt_id"]
DeltaAggregateKey = Literal[
    "delta_kind",
    "transition_type",
    "baseline_failure_type",
    "candidate_failure_type",
]
SignalDirection = Literal["regression", "improvement", "neutral", "incompatible"]


@dataclass(slots=True, frozen=True)
class QueryFilters:
    failure_type: str | None = None
    model: str | None = None
    dataset: str | None = None
    run_id: str | None = None
    prompt_id: str | None = None
    report_id: str | None = None
    baseline_run_id: str | None = None
    candidate_run_id: str | None = None
    delta: str | None = None
    last_n: int | None = None
    since: str | None = None
    until: str | None = None
    limit: int = 20


def artifact_overview_summary(*, root: str | Path | None = None) -> dict[str, int]:
    ensure_query_index(root=root)
    with _connection(root=root) as connection:
        run_count = _scalar_int(connection, "SELECT COUNT(*) FROM runs")
        comparison_count = _scalar_int(connection, "SELECT COUNT(*) FROM comparisons")
        case_count = _scalar_int(
            connection,
            "SELECT COUNT(*) FROM cases WHERE failure_type IS NOT NULL AND failure_type != 'no_failure'",
        )
        delta_count = _scalar_int(connection, "SELECT COUNT(*) FROM case_deltas")
    return {
        "run_count": run_count,
        "comparison_count": comparison_count,
        "case_count": case_count,
        "delta_count": delta_count,
    }


def list_run_inventory(*, root: str | Path | None = None) -> list[dict[str, Any]]:
    ensure_query_index(root=root)
    with _connection(root=root) as connection:
        rows = connection.execute(
            """
            SELECT run_id, dataset, model, created_at, status
            FROM runs
            ORDER BY created_at DESC, run_id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def list_comparison_inventory(*, root: str | Path | None = None) -> list[dict[str, Any]]:
    ensure_query_index(root=root)
    with _connection(root=root) as connection:
        rows = connection.execute(
            """
            SELECT report_id, baseline_run_id, candidate_run_id, dataset, created_at, status,
                   compatible, signal_verdict, regression_score, improvement_score, net_score,
                   severity
            FROM comparisons
            ORDER BY severity DESC, created_at DESC, report_id DESC
            """
        ).fetchall()
    hydrated = [_normalize_comparison_row(dict(row)) for row in rows]
    _attach_signal_drivers(connection=None, rows=hydrated, root=root)
    return hydrated


def query_comparison_signals(
    filters: QueryFilters | None = None,
    *,
    verdict: SignalDirection | None = "regression",
    root: str | Path | None = None,
) -> list[dict[str, Any]]:
    filters = filters or QueryFilters()
    ensure_query_index(root=root)
    with _connection(root=root) as connection:
        selected_report_ids = _selected_report_ids(connection, filters)
        query = [
            """
            SELECT report_id, created_at, dataset, baseline_run_id, candidate_run_id,
                   baseline_model, candidate_model, status, compatible, signal_verdict,
                   regression_score, improvement_score, net_score, severity
            FROM comparisons
            WHERE 1 = 1
            """
        ]
        params: list[Any] = []
        if verdict is not None:
            query.append("AND signal_verdict = ?")
            params.append(verdict)
        if filters.dataset is not None:
            query.append("AND dataset = ?")
            params.append(filters.dataset)
        if filters.report_id is not None:
            query.append("AND report_id = ?")
            params.append(filters.report_id)
        if filters.baseline_run_id is not None:
            query.append("AND baseline_run_id = ?")
            params.append(filters.baseline_run_id)
        if filters.candidate_run_id is not None:
            query.append("AND candidate_run_id = ?")
            params.append(filters.candidate_run_id)
        if filters.model is not None:
            query.append("AND (baseline_model = ? OR candidate_model = ?)")
            params.extend([filters.model, filters.model])
        if filters.since is not None:
            query.append("AND created_at >= ?")
            params.append(filters.since)
        if filters.until is not None:
            query.append("AND created_at <= ?")
            params.append(filters.until)
        if filters.failure_type is not None:
            query.append(
                """
                AND EXISTS (
                    SELECT 1
                    FROM signal_drivers
                    WHERE signal_drivers.report_id = comparisons.report_id
                      AND signal_drivers.failure_type = ?
                )
                """
            )
            params.append(filters.failure_type)
        if selected_report_ids is not None:
            query.append(f"AND report_id IN ({','.join('?' for _ in selected_report_ids)})")
            params.extend(selected_report_ids)
        query.append("ORDER BY severity DESC, created_at DESC, report_id DESC")
        query.append("LIMIT ?")
        params.append(max(filters.limit, 1))
        rows = [
            _normalize_comparison_row(dict(row))
            for row in connection.execute(" ".join(query), params).fetchall()
        ]
        _attach_signal_drivers(connection=connection, rows=rows, root=root)
    return rows


def _normalize_comparison_row(row: dict[str, Any]) -> dict[str, Any]:
    compatible = row.get("compatible")
    if compatible is not None:
        row["compatible"] = bool(compatible)
    return row


def list_query_facets(*, root: str | Path | None = None) -> dict[str, list[str]]:
    ensure_query_index(root=root)
    with _connection(root=root) as connection:
        models = _distinct_strings(connection, "SELECT DISTINCT model FROM runs ORDER BY model")
        datasets = _distinct_strings(
            connection,
            "SELECT DISTINCT dataset FROM runs ORDER BY dataset",
        )
        failure_types = _distinct_strings(
            connection,
            """
            SELECT DISTINCT failure_type
            FROM cases
            WHERE failure_type IS NOT NULL AND failure_type != 'no_failure'
            ORDER BY failure_type
            """,
        )
        delta_types = [
            "regression",
            "improvement",
            "swap",
            "error_change",
            "failure_to_no_failure",
            "no_failure_to_failure",
            "failure_type_swap",
            "error_cleared",
            "new_error",
            "error_stage_changed",
        ]
    return {
        "models": models,
        "datasets": datasets,
        "failureTypes": failure_types,
        "deltaTypes": delta_types,
    }


def query_cases(
    filters: QueryFilters | None = None,
    *,
    root: str | Path | None = None,
) -> list[dict[str, Any]]:
    filters = filters or QueryFilters()
    ensure_query_index(root=root)
    with _connection(root=root) as connection:
        selected_run_ids = _selected_run_ids(connection, filters)
        query, params = _build_case_query_parts(
            filters,
            selected_run_ids=selected_run_ids,
            select_sql="""
            SELECT run_id, dataset, model, created_at, case_id, prompt_id, prompt, tags_json,
                   failure_type, expectation_verdict, explanation, confidence, error_stage
            FROM cases
            """,
        )
        query.append("ORDER BY created_at DESC, run_id DESC, case_id ASC")
        query.append("LIMIT ?")
        params.append(max(filters.limit, 1))
        rows = connection.execute(" ".join(query), params).fetchall()
    return [_hydrate_case_row(row) for row in rows]


def query_case_deltas(
    filters: QueryFilters | None = None,
    *,
    root: str | Path | None = None,
) -> list[dict[str, Any]]:
    filters = filters or QueryFilters()
    ensure_query_index(root=root)
    with _connection(root=root) as connection:
        selected_report_ids = _selected_report_ids(connection, filters)
        query, params = _build_delta_query_parts(
            filters,
            selected_report_ids=selected_report_ids,
            select_sql="""
            SELECT report_id, created_at, dataset, case_id, prompt_id, prompt, tags_json,
                   transition_type, transition_label, delta_kind, baseline_run_id,
                   candidate_run_id, baseline_model, candidate_model, baseline_failure_type,
                   candidate_failure_type, baseline_expectation_verdict,
                   candidate_expectation_verdict, baseline_explanation, candidate_explanation
            FROM case_deltas
            """,
        )
        query.append("ORDER BY created_at DESC, report_id DESC, case_id ASC")
        query.append("LIMIT ?")
        params.append(max(filters.limit, 1))
        rows = connection.execute(" ".join(query), params).fetchall()
    return [_hydrate_delta_row(row) for row in rows]


def count_case_query(
    filters: QueryFilters | None = None,
    *,
    root: str | Path | None = None,
) -> int:
    filters = filters or QueryFilters()
    ensure_query_index(root=root)
    with _connection(root=root) as connection:
        selected_run_ids = _selected_run_ids(connection, filters)
        query, params = _build_case_query_parts(
            filters,
            selected_run_ids=selected_run_ids,
            select_sql="SELECT COUNT(*) FROM cases",
        )
        row = connection.execute(" ".join(query), params).fetchone()
    return int(row[0]) if row else 0


def count_delta_query(
    filters: QueryFilters | None = None,
    *,
    root: str | Path | None = None,
) -> int:
    filters = filters or QueryFilters()
    ensure_query_index(root=root)
    with _connection(root=root) as connection:
        selected_report_ids = _selected_report_ids(connection, filters)
        query, params = _build_delta_query_parts(
            filters,
            selected_report_ids=selected_report_ids,
            select_sql="SELECT COUNT(*) FROM case_deltas",
        )
        row = connection.execute(" ".join(query), params).fetchone()
    return int(row[0]) if row else 0


def aggregate_case_query(
    group_by: AggregateKey,
    filters: QueryFilters | None = None,
    *,
    root: str | Path | None = None,
) -> list[dict[str, Any]]:
    filters = filters or QueryFilters()
    if group_by not in {"failure_type", "model", "dataset", "prompt_id"}:
        raise ValueError(f"unsupported aggregate group: {group_by}")

    ensure_query_index(root=root)
    key_column, label_column = {
        "failure_type": ("failure_type", "failure_type"),
        "model": ("model", "model"),
        "dataset": ("dataset", "dataset"),
        "prompt_id": ("prompt_id", "prompt_id"),
    }[group_by]

    with _connection(root=root) as connection:
        selected_run_ids = _selected_run_ids(connection, filters)
        query, params = _build_case_query_parts(
            filters,
            selected_run_ids=selected_run_ids,
            select_sql=f"""
            SELECT {key_column} AS group_key, {label_column} AS group_label, COUNT(*) AS case_count
            FROM cases
            """,
        )
        query.append(f"GROUP BY {key_column}")
        query.append("ORDER BY case_count DESC, group_key ASC")
        query.append("LIMIT ?")
        params.append(max(filters.limit, 1))
        rows = connection.execute(" ".join(query), params).fetchall()
    return [dict(row) for row in rows]


def aggregate_delta_query(
    group_by: DeltaAggregateKey,
    filters: QueryFilters | None = None,
    *,
    root: str | Path | None = None,
) -> list[dict[str, Any]]:
    filters = filters or QueryFilters()
    if group_by not in {
        "delta_kind",
        "transition_type",
        "baseline_failure_type",
        "candidate_failure_type",
    }:
        raise ValueError(f"unsupported delta aggregate group: {group_by}")

    ensure_query_index(root=root)
    with _connection(root=root) as connection:
        selected_report_ids = _selected_report_ids(connection, filters)
        query, params = _build_delta_query_parts(
            filters,
            selected_report_ids=selected_report_ids,
            select_sql=f"""
            SELECT {group_by} AS group_key, {group_by} AS group_label, COUNT(*) AS case_count
            FROM case_deltas
            """,
        )
        query.append(f"GROUP BY {group_by}")
        query.append("ORDER BY case_count DESC, group_key ASC")
        query.append("LIMIT ?")
        params.append(max(filters.limit, 1))
        rows = connection.execute(" ".join(query), params).fetchall()
    return [dict(row) for row in rows if row["group_key"] is not None]


def _connection(*, root: str | Path | None = None) -> sqlite3.Connection:
    connection = sqlite3.connect(query_index_path(root=root))
    connection.row_factory = sqlite3.Row
    return connection


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


def _hydrate_case_row(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["tags"] = json.loads(payload.pop("tags_json"))
    return payload


def _hydrate_delta_row(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["tags"] = json.loads(payload.pop("tags_json"))
    return payload


def _attach_signal_drivers(
    *,
    connection: sqlite3.Connection | None,
    rows: list[dict[str, Any]],
    root: str | Path | None = None,
) -> None:
    report_ids = [str(row["report_id"]) for row in rows if row.get("report_id") is not None]
    if not report_ids:
        return
    should_close = connection is None
    conn = connection or _connection(root=root)
    try:
        driver_rows = conn.execute(
            f"""
            SELECT report_id, driver_rank, failure_type, delta, direction, case_ids_json
            FROM signal_drivers
            WHERE report_id IN ({','.join('?' for _ in report_ids)})
            ORDER BY report_id ASC, driver_rank ASC
            """,
            report_ids,
        ).fetchall()
        by_report: dict[str, list[dict[str, Any]]] = {}
        for row in driver_rows:
            payload = dict(row)
            payload["case_ids"] = json.loads(payload.pop("case_ids_json"))
            by_report.setdefault(str(payload.pop("report_id")), []).append(payload)
        for row in rows:
            row["top_drivers"] = by_report.get(str(row["report_id"]), [])
    finally:
        if should_close:
            conn.close()


def _scalar_int(connection: sqlite3.Connection, query: str) -> int:
    row = connection.execute(query).fetchone()
    return int(row[0]) if row else 0


def _distinct_strings(connection: sqlite3.Connection, query: str) -> list[str]:
    rows = connection.execute(query).fetchall()
    return [str(row[0]) for row in rows if row[0] is not None]


def _build_case_query_parts(
    filters: QueryFilters,
    *,
    selected_run_ids: list[str] | None,
    select_sql: str,
) -> tuple[list[str], list[Any]]:
    query = [select_sql, "WHERE 1 = 1"]
    params: list[Any] = []
    if filters.failure_type is not None:
        query.append("AND failure_type = ?")
        params.append(filters.failure_type)
    else:
        query.append("AND failure_type IS NOT NULL AND failure_type != 'no_failure'")
    if filters.model is not None:
        query.append("AND model = ?")
        params.append(filters.model)
    if filters.dataset is not None:
        query.append("AND dataset = ?")
        params.append(filters.dataset)
    if filters.run_id is not None:
        query.append("AND run_id = ?")
        params.append(filters.run_id)
    if filters.prompt_id is not None:
        query.append("AND prompt_id = ?")
        params.append(filters.prompt_id)
    if filters.since is not None:
        query.append("AND created_at >= ?")
        params.append(filters.since)
    if filters.until is not None:
        query.append("AND created_at <= ?")
        params.append(filters.until)
    if selected_run_ids is not None:
        query.append(f"AND run_id IN ({','.join('?' for _ in selected_run_ids)})")
        params.extend(selected_run_ids)
    return query, params


def _build_delta_query_parts(
    filters: QueryFilters,
    *,
    selected_report_ids: list[str] | None,
    select_sql: str,
) -> tuple[list[str], list[Any]]:
    query = [select_sql, "WHERE 1 = 1"]
    params: list[Any] = []
    if filters.delta is not None:
        if filters.delta in {"regression", "improvement", "swap", "error_change"}:
            query.append("AND delta_kind = ?")
            params.append(filters.delta)
        else:
            query.append("AND transition_type = ?")
            params.append(filters.delta)
    if filters.dataset is not None:
        query.append("AND dataset = ?")
        params.append(filters.dataset)
    if filters.report_id is not None:
        query.append("AND report_id = ?")
        params.append(filters.report_id)
    if filters.baseline_run_id is not None:
        query.append("AND baseline_run_id = ?")
        params.append(filters.baseline_run_id)
    if filters.candidate_run_id is not None:
        query.append("AND candidate_run_id = ?")
        params.append(filters.candidate_run_id)
    if filters.model is not None:
        query.append("AND (baseline_model = ? OR candidate_model = ?)")
        params.extend([filters.model, filters.model])
    if filters.prompt_id is not None:
        query.append("AND prompt_id = ?")
        params.append(filters.prompt_id)
    if filters.since is not None:
        query.append("AND created_at >= ?")
        params.append(filters.since)
    if filters.until is not None:
        query.append("AND created_at <= ?")
        params.append(filters.until)
    if selected_report_ids is not None:
        query.append(f"AND report_id IN ({','.join('?' for _ in selected_report_ids)})")
        params.extend(selected_report_ids)
    return query, params
