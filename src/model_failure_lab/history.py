"""Deterministic temporal history, trend, and dataset-health helpers."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from model_failure_lab.index.builder import ensure_query_index, query_index_path
from model_failure_lab.schemas import JsonValue

DEFAULT_HISTORY_LIMIT = 10
DEFAULT_TREND_DELTA_THRESHOLD = 0.05
DEFAULT_LOW_VOLATILITY_THRESHOLD = 0.03
DEFAULT_HIGH_VOLATILITY_THRESHOLD = 0.08


@dataclass(slots=True, frozen=True)
class MetricTrend:
    label: str
    delta: float | None
    sample_count: int
    first_value: float | None
    last_value: float | None
    volatility: float | None
    volatility_label: str

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "label": self.label,
            "delta": _rounded_or_none(self.delta),
            "sample_count": self.sample_count,
            "first_value": _rounded_or_none(self.first_value),
            "last_value": _rounded_or_none(self.last_value),
            "volatility": _rounded_or_none(self.volatility),
            "volatility_label": self.volatility_label,
        }


@dataclass(slots=True, frozen=True)
class RecurringFailurePattern:
    failure_type: str
    occurrences: int
    comparison_ids: tuple[str, ...]
    latest_delta: float | None

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "failure_type": self.failure_type,
            "occurrences": self.occurrences,
            "comparison_ids": list(self.comparison_ids),
            "latest_delta": _rounded_or_none(self.latest_delta),
        }


@dataclass(slots=True, frozen=True)
class RunHistoryRecord:
    run_id: str
    dataset: str
    model: str
    created_at: str
    status: str
    attempted_case_count: int
    classified_case_count: int
    execution_error_count: int
    unclassified_count: int
    successful_model_invocation_count: int
    failure_case_count: int
    failure_rate: float | None
    classification_coverage: float | None
    execution_success_rate: float | None

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "run_id": self.run_id,
            "dataset": self.dataset,
            "model": self.model,
            "created_at": self.created_at,
            "status": self.status,
            "attempted_case_count": self.attempted_case_count,
            "classified_case_count": self.classified_case_count,
            "execution_error_count": self.execution_error_count,
            "unclassified_count": self.unclassified_count,
            "successful_model_invocation_count": self.successful_model_invocation_count,
            "failure_case_count": self.failure_case_count,
            "failure_rate": _rounded_or_none(self.failure_rate),
            "classification_coverage": _rounded_or_none(self.classification_coverage),
            "execution_success_rate": _rounded_or_none(self.execution_success_rate),
        }


@dataclass(slots=True, frozen=True)
class ComparisonHistoryRecord:
    report_id: str
    created_at: str
    dataset: str | None
    baseline_run_id: str
    candidate_run_id: str
    baseline_model: str | None
    candidate_model: str | None
    status: str
    compatible: bool
    signal_verdict: str
    regression_score: float
    improvement_score: float
    net_score: float
    severity: float
    top_drivers: tuple[dict[str, Any], ...]

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "report_id": self.report_id,
            "created_at": self.created_at,
            "dataset": self.dataset,
            "baseline_run_id": self.baseline_run_id,
            "candidate_run_id": self.candidate_run_id,
            "baseline_model": self.baseline_model,
            "candidate_model": self.candidate_model,
            "status": self.status,
            "compatible": self.compatible,
            "signal_verdict": self.signal_verdict,
            "regression_score": round(self.regression_score, 6),
            "improvement_score": round(self.improvement_score, 6),
            "net_score": round(self.net_score, 6),
            "severity": round(self.severity, 6),
            "top_drivers": [
                {
                    "driver_rank": int(driver["driver_rank"]),
                    "failure_type": str(driver["failure_type"]),
                    "delta": round(float(driver["delta"]), 6),
                    "direction": str(driver["direction"]),
                    "case_ids": list(driver["case_ids"]),
                }
                for driver in self.top_drivers
            ],
        }


@dataclass(slots=True, frozen=True)
class DatasetVersionHistoryRecord:
    family_id: str
    dataset_id: str
    version_number: int
    version_tag: str
    created_at: str | None
    case_count: int
    parent_dataset_id: str | None
    source_comparison_id: str | None
    source_dataset_id: str | None
    signal_verdict: str | None
    severity: float | None
    primary_failure_type: str | None
    run_count: int
    average_failure_rate: float | None
    latest_run_at: str | None

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "family_id": self.family_id,
            "dataset_id": self.dataset_id,
            "version_number": self.version_number,
            "version_tag": self.version_tag,
            "case_count": self.case_count,
            "parent_dataset_id": self.parent_dataset_id,
            "source_comparison_id": self.source_comparison_id,
            "source_dataset_id": self.source_dataset_id,
            "signal_verdict": self.signal_verdict,
            "severity": _rounded_or_none(self.severity),
            "primary_failure_type": self.primary_failure_type,
            "run_count": self.run_count,
            "average_failure_rate": _rounded_or_none(self.average_failure_rate),
            "latest_run_at": self.latest_run_at,
        }
        if self.created_at is not None:
            payload["created_at"] = self.created_at
        return payload


@dataclass(slots=True, frozen=True)
class DatasetHealthSummary:
    family_id: str
    health_label: str
    trend: MetricTrend
    version_count: int
    evaluation_run_count: int
    recent_fail_rate: float | None
    previous_fail_rate: float | None
    latest_dataset_id: str | None
    latest_version_tag: str | None
    latest_created_at: str | None
    source_dataset_id: str | None
    primary_failure_type: str | None

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "family_id": self.family_id,
            "health_label": self.health_label,
            "trend": self.trend.to_payload(),
            "version_count": self.version_count,
            "evaluation_run_count": self.evaluation_run_count,
            "recent_fail_rate": _rounded_or_none(self.recent_fail_rate),
            "previous_fail_rate": _rounded_or_none(self.previous_fail_rate),
            "latest_dataset_id": self.latest_dataset_id,
            "latest_version_tag": self.latest_version_tag,
            "latest_created_at": self.latest_created_at,
            "source_dataset_id": self.source_dataset_id,
            "primary_failure_type": self.primary_failure_type,
        }


@dataclass(slots=True, frozen=True)
class SignalHistoryContext:
    scope_kind: str
    scope_value: str
    recent_comparison_count: int
    recent_regression_count: int
    comparison_trend: MetricTrend
    candidate_run_trend: MetricTrend | None
    recurring_failures: tuple[RecurringFailurePattern, ...]
    recent_comparisons: tuple[ComparisonHistoryRecord, ...]
    family_health: DatasetHealthSummary | None

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "scope_kind": self.scope_kind,
            "scope_value": self.scope_value,
            "recent_comparison_count": self.recent_comparison_count,
            "recent_regression_count": self.recent_regression_count,
            "comparison_trend": self.comparison_trend.to_payload(),
            "recurring_failures": [
                pattern.to_payload() for pattern in self.recurring_failures
            ],
            "recent_comparisons": [
                row.to_payload() for row in self.recent_comparisons
            ],
            "family_health": self.family_health.to_payload() if self.family_health else None,
        }
        if self.candidate_run_trend is not None:
            payload["candidate_run_trend"] = self.candidate_run_trend.to_payload()
        return payload


@dataclass(slots=True, frozen=True)
class HistorySnapshot:
    scope_kind: str
    scope_value: str
    run_history: tuple[RunHistoryRecord, ...]
    comparison_history: tuple[ComparisonHistoryRecord, ...]
    run_trend: MetricTrend | None
    comparison_trend: MetricTrend | None
    recurring_failures: tuple[RecurringFailurePattern, ...]
    dataset_versions: tuple[DatasetVersionHistoryRecord, ...]
    dataset_health: DatasetHealthSummary | None

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "scope_kind": self.scope_kind,
            "scope_value": self.scope_value,
            "run_history": [row.to_payload() for row in self.run_history],
            "comparison_history": [row.to_payload() for row in self.comparison_history],
            "run_trend": self.run_trend.to_payload() if self.run_trend else None,
            "comparison_trend": (
                self.comparison_trend.to_payload() if self.comparison_trend else None
            ),
            "recurring_failures": [
                pattern.to_payload() for pattern in self.recurring_failures
            ],
            "dataset_versions": [row.to_payload() for row in self.dataset_versions],
            "dataset_health": self.dataset_health.to_payload() if self.dataset_health else None,
        }


def query_history_snapshot(
    *,
    dataset: str | None = None,
    model: str | None = None,
    family_id: str | None = None,
    limit: int = DEFAULT_HISTORY_LIMIT,
    root: str | Path | None = None,
) -> HistorySnapshot:
    if family_id is None and dataset is None and model is None:
        raise ValueError("history snapshot requires a dataset, model, or family scope")

    ensure_query_index(root=root)
    with _connection(root=root) as connection:
        if family_id is not None:
            versions = _list_family_versions(connection, family_id=family_id)
            run_history = _list_family_runs(connection, family_id=family_id, limit=limit)
            comparison_history: tuple[ComparisonHistoryRecord, ...] = ()
            dataset_health = summarize_dataset_health(versions)
            return HistorySnapshot(
                scope_kind="family",
                scope_value=family_id,
                run_history=run_history,
                comparison_history=comparison_history,
                run_trend=summarize_run_trend(run_history),
                comparison_trend=None,
                recurring_failures=(),
                dataset_versions=versions,
                dataset_health=dataset_health,
            )

        run_history = _list_run_history(
            connection,
            dataset=dataset,
            model=model,
            limit=limit,
        )
        comparison_history = _list_comparison_history(
            connection,
            dataset=dataset,
            model=model,
            limit=limit,
        )
        return HistorySnapshot(
            scope_kind="dataset" if dataset is not None else "model",
            scope_value=dataset or model or "unknown",
            run_history=run_history,
            comparison_history=comparison_history,
            run_trend=summarize_run_trend(run_history),
            comparison_trend=summarize_comparison_trend(comparison_history),
            recurring_failures=summarize_recurring_failures(comparison_history),
            dataset_versions=(),
            dataset_health=None,
        )


def build_signal_history_context(
    comparison_id: str,
    *,
    family_id: str | None = None,
    limit: int = 5,
    root: str | Path | None = None,
) -> SignalHistoryContext:
    ensure_query_index(root=root)
    with _connection(root=root) as connection:
        current = _load_comparison(connection, comparison_id)
        if current is None:
            raise ValueError(f"comparison not found in query index: {comparison_id}")

        scope_kind = "dataset" if current.dataset is not None else "model"
        scope_value = (
            current.dataset
            or current.candidate_model
            or current.baseline_model
            or current.report_id
        )
        recent_comparisons = _list_comparison_history(
            connection,
            dataset=current.dataset,
            model=None if current.dataset is not None else current.candidate_model,
            limit=limit,
        )
        candidate_run_history = _list_run_history(
            connection,
            dataset=current.dataset,
            model=current.candidate_model,
            limit=limit,
        )
        family_health = (
            summarize_dataset_health(_list_family_versions(connection, family_id=family_id))
            if family_id is not None
            else None
        )
        return SignalHistoryContext(
            scope_kind=scope_kind,
            scope_value=scope_value,
            recent_comparison_count=len(recent_comparisons),
            recent_regression_count=sum(
                1 for row in recent_comparisons if row.signal_verdict == "regression"
            ),
            comparison_trend=summarize_comparison_trend(recent_comparisons),
            candidate_run_trend=(
                summarize_run_trend(candidate_run_history)
                if candidate_run_history
                else None
            ),
            recurring_failures=summarize_recurring_failures(recent_comparisons),
            recent_comparisons=recent_comparisons,
            family_health=family_health,
        )


def summarize_run_trend(rows: tuple[RunHistoryRecord, ...]) -> MetricTrend:
    return _summarize_metric_trend([row.failure_rate for row in rows])


def summarize_comparison_trend(rows: tuple[ComparisonHistoryRecord, ...]) -> MetricTrend:
    return _summarize_metric_trend([row.net_score for row in rows])


def summarize_dataset_health(
    versions: tuple[DatasetVersionHistoryRecord, ...],
) -> DatasetHealthSummary | None:
    if not versions:
        return None

    rate_history = [row.average_failure_rate for row in versions]
    trend = _summarize_metric_trend(rate_history)
    recent = versions[-1]
    previous = versions[-2] if len(versions) > 1 else None
    evaluation_run_count = sum(row.run_count for row in versions)
    if evaluation_run_count == 0:
        health_label = "unevaluated"
    elif trend.label == "degrading":
        health_label = "degrading"
    elif trend.volatility_label == "high":
        health_label = "volatile"
    elif trend.label == "improving":
        health_label = "improving"
    else:
        health_label = "stable"

    return DatasetHealthSummary(
        family_id=recent.family_id,
        health_label=health_label,
        trend=trend,
        version_count=len(versions),
        evaluation_run_count=evaluation_run_count,
        recent_fail_rate=recent.average_failure_rate,
        previous_fail_rate=previous.average_failure_rate if previous else None,
        latest_dataset_id=recent.dataset_id,
        latest_version_tag=recent.version_tag,
        latest_created_at=recent.created_at,
        source_dataset_id=recent.source_dataset_id,
        primary_failure_type=recent.primary_failure_type,
    )


def summarize_recurring_failures(
    rows: tuple[ComparisonHistoryRecord, ...],
    *,
    minimum_occurrences: int = 2,
    limit: int = 3,
) -> tuple[RecurringFailurePattern, ...]:
    by_failure_type: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.signal_verdict != "regression":
            continue
        seen_in_row: set[str] = set()
        for driver in row.top_drivers:
            failure_type = str(driver["failure_type"])
            if failure_type in seen_in_row:
                continue
            seen_in_row.add(failure_type)
            entry = by_failure_type.setdefault(
                failure_type,
                {
                    "occurrences": 0,
                    "comparison_ids": [],
                    "latest_delta": None,
                },
            )
            entry["occurrences"] += 1
            entry["comparison_ids"].append(row.report_id)
            delta = float(driver["delta"])
            latest_delta = entry["latest_delta"]
            if latest_delta is None or abs(delta) >= abs(float(latest_delta)):
                entry["latest_delta"] = delta

    patterns = [
        RecurringFailurePattern(
            failure_type=failure_type,
            occurrences=int(entry["occurrences"]),
            comparison_ids=tuple(entry["comparison_ids"]),
            latest_delta=(
                float(entry["latest_delta"])
                if entry["latest_delta"] is not None
                else None
            ),
        )
        for failure_type, entry in by_failure_type.items()
        if int(entry["occurrences"]) >= minimum_occurrences
    ]
    return tuple(
        sorted(
            patterns,
            key=lambda pattern: (-pattern.occurrences, pattern.failure_type),
        )[:limit]
    )


def _connection(*, root: str | Path | None = None) -> sqlite3.Connection:
    connection = sqlite3.connect(query_index_path(root=root))
    connection.row_factory = sqlite3.Row
    return connection


def _list_run_history(
    connection: sqlite3.Connection,
    *,
    dataset: str | None,
    model: str | None,
    limit: int,
) -> tuple[RunHistoryRecord, ...]:
    query = [
        """
        SELECT run_id, dataset, model, created_at, status, attempted_case_count,
               classified_case_count, execution_error_count, unclassified_count,
               successful_model_invocation_count, failure_case_count, failure_rate,
               classification_coverage, execution_success_rate
        FROM runs
        WHERE 1 = 1
        """
    ]
    params: list[Any] = []
    if dataset is not None:
        query.append("AND dataset = ?")
        params.append(dataset)
    if model is not None:
        query.append("AND model = ?")
        params.append(model)
    query.append("ORDER BY created_at DESC, run_id DESC LIMIT ?")
    params.append(max(limit, 1))
    rows = connection.execute(" ".join(query), params).fetchall()
    return tuple(
        RunHistoryRecord(
            run_id=str(row["run_id"]),
            dataset=str(row["dataset"]),
            model=str(row["model"]),
            created_at=str(row["created_at"]),
            status=str(row["status"]),
            attempted_case_count=int(row["attempted_case_count"]),
            classified_case_count=int(row["classified_case_count"]),
            execution_error_count=int(row["execution_error_count"]),
            unclassified_count=int(row["unclassified_count"]),
            successful_model_invocation_count=int(row["successful_model_invocation_count"]),
            failure_case_count=int(row["failure_case_count"]),
            failure_rate=_float_or_none(row["failure_rate"]),
            classification_coverage=_float_or_none(row["classification_coverage"]),
            execution_success_rate=_float_or_none(row["execution_success_rate"]),
        )
        for row in reversed(rows)
    )


def _list_comparison_history(
    connection: sqlite3.Connection,
    *,
    dataset: str | None,
    model: str | None,
    limit: int,
) -> tuple[ComparisonHistoryRecord, ...]:
    query = [
        """
        SELECT report_id, created_at, dataset, baseline_run_id, candidate_run_id, baseline_model,
               candidate_model, status, compatible, signal_verdict, regression_score,
               improvement_score, net_score, severity
        FROM comparisons
        WHERE 1 = 1
        """
    ]
    params: list[Any] = []
    if dataset is not None:
        query.append("AND dataset = ?")
        params.append(dataset)
    if model is not None:
        query.append("AND (baseline_model = ? OR candidate_model = ?)")
        params.extend([model, model])
    query.append("ORDER BY created_at DESC, report_id DESC LIMIT ?")
    params.append(max(limit, 1))
    rows = list(connection.execute(" ".join(query), params).fetchall())
    drivers = _load_signal_drivers(
        connection,
        report_ids=[str(row["report_id"]) for row in rows],
    )
    return tuple(
        ComparisonHistoryRecord(
            report_id=str(row["report_id"]),
            created_at=str(row["created_at"]),
            dataset=_string_or_none(row["dataset"]),
            baseline_run_id=str(row["baseline_run_id"]),
            candidate_run_id=str(row["candidate_run_id"]),
            baseline_model=_string_or_none(row["baseline_model"]),
            candidate_model=_string_or_none(row["candidate_model"]),
            status=str(row["status"]),
            compatible=bool(row["compatible"]),
            signal_verdict=str(row["signal_verdict"]),
            regression_score=float(row["regression_score"]),
            improvement_score=float(row["improvement_score"]),
            net_score=float(row["net_score"]),
            severity=float(row["severity"]),
            top_drivers=tuple(drivers.get(str(row["report_id"]), ())),
        )
        for row in reversed(rows)
    )


def _list_family_runs(
    connection: sqlite3.Connection,
    *,
    family_id: str,
    limit: int,
) -> tuple[RunHistoryRecord, ...]:
    rows = connection.execute(
        """
        SELECT runs.run_id, runs.dataset, runs.model, runs.created_at, runs.status,
               runs.attempted_case_count, runs.classified_case_count, runs.execution_error_count,
               runs.unclassified_count, runs.successful_model_invocation_count,
               runs.failure_case_count, runs.failure_rate, runs.classification_coverage,
               runs.execution_success_rate
        FROM runs
        INNER JOIN dataset_versions ON dataset_versions.dataset_id = runs.dataset
        WHERE dataset_versions.family_id = ?
        ORDER BY runs.created_at DESC, runs.run_id DESC
        LIMIT ?
        """,
        (family_id, max(limit, 1)),
    ).fetchall()
    return tuple(
        RunHistoryRecord(
            run_id=str(row["run_id"]),
            dataset=str(row["dataset"]),
            model=str(row["model"]),
            created_at=str(row["created_at"]),
            status=str(row["status"]),
            attempted_case_count=int(row["attempted_case_count"]),
            classified_case_count=int(row["classified_case_count"]),
            execution_error_count=int(row["execution_error_count"]),
            unclassified_count=int(row["unclassified_count"]),
            successful_model_invocation_count=int(row["successful_model_invocation_count"]),
            failure_case_count=int(row["failure_case_count"]),
            failure_rate=_float_or_none(row["failure_rate"]),
            classification_coverage=_float_or_none(row["classification_coverage"]),
            execution_success_rate=_float_or_none(row["execution_success_rate"]),
        )
        for row in reversed(rows)
    )


def _list_family_versions(
    connection: sqlite3.Connection,
    *,
    family_id: str,
) -> tuple[DatasetVersionHistoryRecord, ...]:
    rows = connection.execute(
        """
        SELECT dataset_versions.family_id, dataset_versions.dataset_id, dataset_versions.version_number,
               dataset_versions.version_tag, dataset_versions.created_at, dataset_versions.case_count,
               dataset_versions.parent_dataset_id, dataset_versions.source_comparison_id,
               dataset_versions.source_dataset_id, dataset_versions.signal_verdict,
               dataset_versions.severity, dataset_versions.primary_failure_type,
               COUNT(runs.run_id) AS run_count,
               AVG(runs.failure_rate) AS average_failure_rate,
               MAX(runs.created_at) AS latest_run_at
        FROM dataset_versions
        LEFT JOIN runs ON runs.dataset = dataset_versions.dataset_id
        WHERE dataset_versions.family_id = ?
        GROUP BY dataset_versions.dataset_id
        ORDER BY dataset_versions.version_number ASC, dataset_versions.dataset_id ASC
        """,
        (family_id,),
    ).fetchall()
    return tuple(
        DatasetVersionHistoryRecord(
            family_id=str(row["family_id"]),
            dataset_id=str(row["dataset_id"]),
            version_number=int(row["version_number"]),
            version_tag=str(row["version_tag"]),
            created_at=_string_or_none(row["created_at"]),
            case_count=int(row["case_count"]),
            parent_dataset_id=_string_or_none(row["parent_dataset_id"]),
            source_comparison_id=_string_or_none(row["source_comparison_id"]),
            source_dataset_id=_string_or_none(row["source_dataset_id"]),
            signal_verdict=_string_or_none(row["signal_verdict"]),
            severity=_float_or_none(row["severity"]),
            primary_failure_type=_string_or_none(row["primary_failure_type"]),
            run_count=int(row["run_count"]),
            average_failure_rate=_float_or_none(row["average_failure_rate"]),
            latest_run_at=_string_or_none(row["latest_run_at"]),
        )
        for row in rows
    )


def _load_comparison(
    connection: sqlite3.Connection,
    comparison_id: str,
) -> ComparisonHistoryRecord | None:
    rows = _list_comparison_history(
        connection,
        dataset=None,
        model=None,
        limit=10_000,
    )
    for row in rows:
        if row.report_id == comparison_id:
            return row
    return None


def _load_signal_drivers(
    connection: sqlite3.Connection,
    *,
    report_ids: list[str],
) -> dict[str, tuple[dict[str, Any], ...]]:
    if not report_ids:
        return {}
    rows = connection.execute(
        f"""
        SELECT report_id, driver_rank, failure_type, delta, direction, case_ids_json
        FROM signal_drivers
        WHERE report_id IN ({",".join("?" for _ in report_ids)})
        ORDER BY report_id ASC, driver_rank ASC
        """,
        report_ids,
    ).fetchall()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["report_id"]), []).append(
            {
                "driver_rank": int(row["driver_rank"]),
                "failure_type": str(row["failure_type"]),
                "delta": float(row["delta"]),
                "direction": str(row["direction"]),
                "case_ids": json.loads(str(row["case_ids_json"])),
            }
        )
    return {report_id: tuple(entries) for report_id, entries in grouped.items()}


def _summarize_metric_trend(values: list[float | None]) -> MetricTrend:
    usable_values = [float(value) for value in values if value is not None]
    if len(usable_values) < 2:
        first_value = usable_values[0] if usable_values else None
        return MetricTrend(
            label="insufficient_history",
            delta=None,
            sample_count=len(usable_values),
            first_value=first_value,
            last_value=first_value,
            volatility=None,
            volatility_label="insufficient_history",
        )

    delta = usable_values[-1] - usable_values[0]
    if delta <= -DEFAULT_TREND_DELTA_THRESHOLD:
        label = "improving"
    elif delta >= DEFAULT_TREND_DELTA_THRESHOLD:
        label = "degrading"
    else:
        label = "stable"

    deltas = [
        abs(current - previous)
        for previous, current in zip(usable_values, usable_values[1:], strict=False)
    ]
    volatility = sum(deltas) / len(deltas) if deltas else 0.0
    if volatility < DEFAULT_LOW_VOLATILITY_THRESHOLD:
        volatility_label = "low"
    elif volatility < DEFAULT_HIGH_VOLATILITY_THRESHOLD:
        volatility_label = "medium"
    else:
        volatility_label = "high"

    return MetricTrend(
        label=label,
        delta=delta,
        sample_count=len(usable_values),
        first_value=usable_values[0],
        last_value=usable_values[-1],
        volatility=volatility,
        volatility_label=volatility_label,
    )


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
