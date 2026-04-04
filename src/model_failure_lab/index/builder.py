"""Build a derived local SQLite index over saved failure artifacts."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import time

from model_failure_lab.reporting.signals import build_comparison_signal, build_incompatible_signal
from model_failure_lab.reporting.load import load_saved_run_artifacts
from model_failure_lab.storage.layout import (
    REPORT_DETAILS_FILENAME,
    REPORT_FILENAME,
    RESULTS_FILENAME,
    RUN_FILENAME,
    project_root,
    reports_root,
    runs_root,
)

QUERY_INDEX_SCHEMA_VERSION = "query_index_v2"
QUERY_INDEX_DIRNAME = ".failure_lab"
QUERY_INDEX_FILENAME = "query_index.sqlite3"

DELTA_KIND_BY_TRANSITION = {
    "failure_to_no_failure": "improvement",
    "no_failure_to_failure": "regression",
    "failure_type_swap": "swap",
    "error_cleared": "error_change",
    "new_error": "error_change",
    "error_stage_changed": "error_change",
}


@dataclass(slots=True, frozen=True)
class QueryIndexSummary:
    path: Path
    run_count: int
    case_count: int
    comparison_count: int
    case_delta_count: int
    rebuilt: bool


def query_index_dir(*, root: str | Path | None = None, create: bool = False) -> Path:
    index_dir = project_root(root) / QUERY_INDEX_DIRNAME
    if create:
        index_dir.mkdir(parents=True, exist_ok=True)
    return index_dir


def query_index_path(*, root: str | Path | None = None) -> Path:
    return query_index_dir(root=root, create=False) / QUERY_INDEX_FILENAME


def rebuild_query_index(*, root: str | Path | None = None) -> QueryIndexSummary:
    artifact_root = project_root(root)
    index_dir = query_index_dir(root=artifact_root, create=True)
    final_path = query_index_path(root=artifact_root)

    run_rows: list[dict[str, object]] = []
    case_rows: list[dict[str, object]] = []
    run_lookup: dict[str, dict[str, object]] = {}

    for run_dir in _artifact_directories(runs_root(root=artifact_root, create=False)):
        run_path = run_dir / RUN_FILENAME
        results_path = run_dir / RESULTS_FILENAME
        if not run_path.exists() or not results_path.exists():
            raise ValueError(f"run artifact is incomplete: {run_dir.name}")

        saved_run = load_saved_run_artifacts(run_dir.name, root=artifact_root)
        run_row = {
            "run_id": saved_run.run.run_id,
            "dataset": saved_run.run.dataset,
            "model": saved_run.run.model,
            "created_at": saved_run.run.created_at,
            "status": saved_run.status,
            "adapter_id": saved_run.adapter_id,
            "classifier_id": saved_run.classifier_id,
            "run_seed": saved_run.run.metadata.get("run_seed"),
        }
        run_lookup[saved_run.run.run_id] = run_row
        run_rows.append(run_row)

        for case in saved_run.case_results:
            classification = case.classification
            expectation = case.expectation
            error = case.error
            case_rows.append(
                {
                    "run_id": saved_run.run.run_id,
                    "dataset": saved_run.run.dataset,
                    "model": saved_run.run.model,
                    "created_at": saved_run.run.created_at,
                    "case_id": case.case_id,
                    "prompt_id": case.prompt.id,
                    "prompt": case.prompt.prompt,
                    "tags_json": json.dumps(list(case.prompt.tags)),
                    "failure_type": classification.failure_type if classification is not None else None,
                    "expectation_verdict": (
                        expectation.expectation_verdict if expectation is not None else None
                    ),
                    "explanation": classification.explanation if classification is not None else None,
                    "confidence": classification.confidence if classification is not None else None,
                    "error_stage": error.stage if error is not None else None,
                }
            )

    comparison_rows: list[dict[str, object]] = []
    delta_rows: list[dict[str, object]] = []
    signal_driver_rows: list[dict[str, object]] = []
    for report_dir in _artifact_directories(reports_root(root=artifact_root, create=False)):
        report_path = report_dir / REPORT_FILENAME
        details_path = report_dir / REPORT_DETAILS_FILENAME
        if not report_path.exists() or not details_path.exists():
            raise ValueError(f"report artifact is incomplete: {report_dir.name}")

        report_payload = _read_json_object(report_path, f"{report_dir.name}/{REPORT_FILENAME}")
        details_payload = _read_json_object(
            details_path, f"{report_dir.name}/{REPORT_DETAILS_FILENAME}"
        )
        metadata = report_payload.get("metadata")
        report_kind = metadata.get("report_kind") if isinstance(metadata, dict) else None
        if report_kind != "comparison":
            continue

        comparison = _require_mapping(report_payload.get("comparison"), "comparison")
        report_id = _require_string(report_payload.get("report_id"), f"{report_dir.name}.report_id")
        baseline_run_id = _require_string(
            comparison.get("baseline_run_id"), f"{report_id}.comparison.baseline_run_id"
        )
        candidate_run_id = _require_string(
            comparison.get("candidate_run_id"), f"{report_id}.comparison.candidate_run_id"
        )
        baseline_row = run_lookup.get(baseline_run_id)
        candidate_row = run_lookup.get(candidate_run_id)
        signal = _read_comparison_signal(report_payload, details_payload, report_id=report_id)
        comparison_rows.append(
            {
                "report_id": report_id,
                "created_at": _require_string(
                    report_payload.get("created_at"), f"{report_id}.created_at"
                ),
                "dataset": _optional_string(comparison.get("dataset_id")),
                "baseline_run_id": baseline_run_id,
                "candidate_run_id": candidate_run_id,
                "baseline_model": baseline_row["model"] if baseline_row else None,
                "candidate_model": candidate_row["model"] if candidate_row else None,
                "status": _read_report_status(report_payload),
                "compatible": _require_bool(
                    comparison.get("compatible"), f"{report_id}.comparison.compatible"
                ),
                "signal_verdict": _require_string(
                    signal.get("verdict"), f"{report_id}.signal.verdict"
                ),
                "regression_score": _require_number(
                    signal.get("regression_score"), f"{report_id}.signal.regression_score"
                ),
                "improvement_score": _require_number(
                    signal.get("improvement_score"), f"{report_id}.signal.improvement_score"
                ),
                "net_score": _require_number(
                    signal.get("net_score"), f"{report_id}.signal.net_score"
                ),
                "severity": _require_number(
                    signal.get("severity"), f"{report_id}.signal.severity"
                ),
            }
        )
        signal_driver_rows.extend(_signal_driver_rows(report_id=report_id, signal=signal))

        case_deltas = details_payload.get("case_deltas")
        if case_deltas is None:
            raise ValueError(f"{report_id} comparison details are missing case_deltas")
        if not isinstance(case_deltas, list):
            raise ValueError(f"{report_id} comparison details case_deltas must be a list")
        for row in case_deltas:
            payload = _require_mapping(row, f"{report_id}.case_delta")
            transition_type = _require_string(
                payload.get("transition_type"), f"{report_id}.case_delta.transition_type"
            )
            delta_rows.append(
                {
                    "report_id": report_id,
                    "created_at": _require_string(
                        report_payload.get("created_at"), f"{report_id}.created_at"
                    ),
                    "dataset": _optional_string(comparison.get("dataset_id")),
                    "case_id": _require_string(
                        payload.get("case_id"), f"{report_id}.case_delta.case_id"
                    ),
                    "prompt_id": _require_string(
                        payload.get("prompt_id"), f"{report_id}.case_delta.prompt_id"
                    ),
                    "prompt": _require_string(
                        payload.get("prompt"), f"{report_id}.case_delta.prompt"
                    ),
                    "tags_json": json.dumps(_require_string_list(payload.get("tags"), "tags")),
                    "transition_type": transition_type,
                    "transition_label": _require_string(
                        payload.get("transition_label"),
                        f"{report_id}.case_delta.transition_label",
                    ),
                    "delta_kind": DELTA_KIND_BY_TRANSITION.get(transition_type, transition_type),
                    "baseline_run_id": baseline_run_id,
                    "candidate_run_id": candidate_run_id,
                    "baseline_model": baseline_row["model"] if baseline_row else None,
                    "candidate_model": candidate_row["model"] if candidate_row else None,
                    "baseline_failure_type": _optional_string(payload.get("baseline_failure_type")),
                    "candidate_failure_type": _optional_string(payload.get("candidate_failure_type")),
                    "baseline_expectation_verdict": _optional_string(
                        payload.get("baseline_expectation_verdict")
                    ),
                    "candidate_expectation_verdict": _optional_string(
                        payload.get("candidate_expectation_verdict")
                    ),
                    "baseline_explanation": _optional_string(payload.get("baseline_explanation")),
                    "candidate_explanation": _optional_string(payload.get("candidate_explanation")),
                }
            )

    with NamedTemporaryFile(dir=index_dir, suffix=".sqlite3", delete=False) as handle:
        temp_path = Path(handle.name)

    try:
        with sqlite3.connect(temp_path) as connection:
            _create_schema(connection)
            indexed_at = time()
            connection.execute(
                "INSERT INTO metadata(key, value) VALUES(?, ?)",
                ("schema_version", QUERY_INDEX_SCHEMA_VERSION),
            )
            connection.execute(
                "INSERT INTO metadata(key, value) VALUES(?, ?)",
                ("indexed_at", str(indexed_at)),
            )
            connection.executemany(
                """
                INSERT INTO runs(
                    run_id, dataset, model, created_at, status, adapter_id, classifier_id, run_seed
                ) VALUES(
                    :run_id, :dataset, :model, :created_at, :status, :adapter_id, :classifier_id, :run_seed
                )
                """,
                run_rows,
            )
            connection.executemany(
                """
                INSERT INTO cases(
                    run_id, dataset, model, created_at, case_id, prompt_id, prompt, tags_json,
                    failure_type, expectation_verdict, explanation, confidence, error_stage
                ) VALUES(
                    :run_id, :dataset, :model, :created_at, :case_id, :prompt_id, :prompt, :tags_json,
                    :failure_type, :expectation_verdict, :explanation, :confidence, :error_stage
                )
                """,
                case_rows,
            )
            connection.executemany(
                """
                INSERT INTO comparisons(
                    report_id, created_at, dataset, baseline_run_id, candidate_run_id,
                    baseline_model, candidate_model, status, compatible, signal_verdict,
                    regression_score, improvement_score, net_score, severity
                ) VALUES(
                    :report_id, :created_at, :dataset, :baseline_run_id, :candidate_run_id,
                    :baseline_model, :candidate_model, :status, :compatible, :signal_verdict,
                    :regression_score, :improvement_score, :net_score, :severity
                )
                """,
                comparison_rows,
            )
            connection.executemany(
                """
                INSERT INTO case_deltas(
                    report_id, created_at, dataset, case_id, prompt_id, prompt, tags_json,
                    transition_type, transition_label, delta_kind, baseline_run_id, candidate_run_id,
                    baseline_model, candidate_model, baseline_failure_type, candidate_failure_type,
                    baseline_expectation_verdict, candidate_expectation_verdict,
                    baseline_explanation, candidate_explanation
                ) VALUES(
                    :report_id, :created_at, :dataset, :case_id, :prompt_id, :prompt, :tags_json,
                    :transition_type, :transition_label, :delta_kind, :baseline_run_id, :candidate_run_id,
                    :baseline_model, :candidate_model, :baseline_failure_type, :candidate_failure_type,
                    :baseline_expectation_verdict, :candidate_expectation_verdict,
                    :baseline_explanation, :candidate_explanation
                )
                """,
                delta_rows,
            )
            connection.executemany(
                """
                INSERT INTO signal_drivers(
                    report_id, driver_rank, failure_type, delta, direction, case_ids_json
                ) VALUES(
                    :report_id, :driver_rank, :failure_type, :delta, :direction, :case_ids_json
                )
                """,
                signal_driver_rows,
            )
            connection.commit()
        temp_path.replace(final_path)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)

    return QueryIndexSummary(
        path=final_path,
        run_count=len(run_rows),
        case_count=len(case_rows),
        comparison_count=len(comparison_rows),
        case_delta_count=len(delta_rows),
        rebuilt=True,
    )


def ensure_query_index(*, root: str | Path | None = None) -> QueryIndexSummary:
    artifact_root = project_root(root)
    index_path = query_index_path(root=artifact_root)
    if not index_path.exists():
        return rebuild_query_index(root=artifact_root)

    latest_artifact_mtime = _latest_artifact_mtime(artifact_root)
    if latest_artifact_mtime is not None and index_path.stat().st_mtime < latest_artifact_mtime:
        return rebuild_query_index(root=artifact_root)

    with sqlite3.connect(index_path) as connection:
        schema_version = connection.execute(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        ).fetchone()
        if not schema_version or schema_version[0] != QUERY_INDEX_SCHEMA_VERSION:
            return rebuild_query_index(root=artifact_root)

        run_count = _count_rows(connection, "runs")
        case_count = _count_rows(connection, "cases")
        comparison_count = _count_rows(connection, "comparisons")
        case_delta_count = _count_rows(connection, "case_deltas")
    return QueryIndexSummary(
        path=index_path,
        run_count=run_count,
        case_count=case_count,
        comparison_count=comparison_count,
        case_delta_count=case_delta_count,
        rebuilt=False,
    )


def _artifact_directories(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        [entry for entry in root.iterdir() if entry.is_dir()],
        key=lambda entry: entry.name,
    )


def _latest_artifact_mtime(root: Path) -> float | None:
    latest: float | None = None
    for artifact_root in (runs_root(root=root, create=False), reports_root(root=root, create=False)):
        if not artifact_root.exists():
            continue
        for path in artifact_root.rglob("*"):
            if not path.is_file():
                continue
            current = path.stat().st_mtime
            latest = current if latest is None else max(latest, current)
    return latest


def _count_rows(connection: sqlite3.Connection, table: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0]) if row else 0


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE runs (
            run_id TEXT PRIMARY KEY,
            dataset TEXT NOT NULL,
            model TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL,
            adapter_id TEXT,
            classifier_id TEXT,
            run_seed INTEGER
        );

        CREATE TABLE cases (
            run_id TEXT NOT NULL,
            dataset TEXT NOT NULL,
            model TEXT NOT NULL,
            created_at TEXT NOT NULL,
            case_id TEXT NOT NULL,
            prompt_id TEXT NOT NULL,
            prompt TEXT NOT NULL,
            tags_json TEXT NOT NULL,
            failure_type TEXT,
            expectation_verdict TEXT,
            explanation TEXT,
            confidence REAL,
            error_stage TEXT,
            PRIMARY KEY (run_id, case_id)
        );

        CREATE TABLE comparisons (
            report_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            dataset TEXT,
            baseline_run_id TEXT NOT NULL,
            candidate_run_id TEXT NOT NULL,
            baseline_model TEXT,
            candidate_model TEXT,
            status TEXT NOT NULL,
            compatible INTEGER NOT NULL,
            signal_verdict TEXT NOT NULL,
            regression_score REAL NOT NULL,
            improvement_score REAL NOT NULL,
            net_score REAL NOT NULL,
            severity REAL NOT NULL
        );

        CREATE TABLE case_deltas (
            report_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            dataset TEXT,
            case_id TEXT NOT NULL,
            prompt_id TEXT NOT NULL,
            prompt TEXT NOT NULL,
            tags_json TEXT NOT NULL,
            transition_type TEXT NOT NULL,
            transition_label TEXT NOT NULL,
            delta_kind TEXT NOT NULL,
            baseline_run_id TEXT NOT NULL,
            candidate_run_id TEXT NOT NULL,
            baseline_model TEXT,
            candidate_model TEXT,
            baseline_failure_type TEXT,
            candidate_failure_type TEXT,
            baseline_expectation_verdict TEXT,
            candidate_expectation_verdict TEXT,
            baseline_explanation TEXT,
            candidate_explanation TEXT,
            PRIMARY KEY (report_id, case_id, transition_type)
        );

        CREATE TABLE signal_drivers (
            report_id TEXT NOT NULL,
            driver_rank INTEGER NOT NULL,
            failure_type TEXT NOT NULL,
            delta REAL NOT NULL,
            direction TEXT NOT NULL,
            case_ids_json TEXT NOT NULL,
            PRIMARY KEY (report_id, driver_rank)
        );

        CREATE INDEX idx_cases_failure_type ON cases(failure_type);
        CREATE INDEX idx_cases_created_at ON cases(created_at DESC);
        CREATE INDEX idx_cases_model_dataset ON cases(model, dataset);
        CREATE INDEX idx_comparisons_created_at ON comparisons(created_at DESC);
        CREATE INDEX idx_comparisons_signal_verdict ON comparisons(signal_verdict);
        CREATE INDEX idx_comparisons_severity ON comparisons(severity DESC);
        CREATE INDEX idx_case_deltas_delta_kind ON case_deltas(delta_kind);
        CREATE INDEX idx_case_deltas_transition_type ON case_deltas(transition_type);
        CREATE INDEX idx_signal_drivers_failure_type ON signal_drivers(failure_type);
        """
    )


def _read_json_object(path: Path, label: str) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload


def _require_mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("optional string fields must be strings or null")
    return value


def _require_string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list of strings")
    items: list[str] = []
    for index, item in enumerate(value):
        items.append(_require_string(item, f"{label}[{index}]"))
    return items


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be a boolean")
    return value


def _require_number(value: object, label: str) -> float:
    if not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    return float(value)


def _read_report_status(report_payload: dict[str, object]) -> str:
    status = report_payload.get("status")
    if isinstance(status, dict):
        overall = status.get("overall")
        if isinstance(overall, str) and overall.strip():
            return overall
    return "comparison_ready"


def _read_comparison_signal(
    report_payload: dict[str, object],
    details_payload: dict[str, object],
    *,
    report_id: str,
) -> dict[str, JsonValue]:
    comparison = _require_mapping(report_payload.get("comparison"), f"{report_id}.comparison")
    raw_signal = comparison.get("signal")
    if raw_signal is None:
        raw_signal = details_payload.get("signal")
    if isinstance(raw_signal, dict):
        return _normalize_signal_payload(raw_signal, f"{report_id}.signal")

    compatible = _require_bool(comparison.get("compatible"), f"{report_id}.comparison.compatible")
    if not compatible:
        reason = _optional_string(comparison.get("reason")) or "incompatible"
        return build_incompatible_signal(reason=reason)

    case_deltas = details_payload.get("case_deltas")
    if not isinstance(case_deltas, list):
        raise ValueError(f"{report_id} comparison details case_deltas must be a list")
    return build_comparison_signal(
        failure_rate_deltas=_require_float_mapping(
            report_payload.get("failure_rates"), f"{report_id}.failure_rates"
        ),
        case_deltas=[_require_mapping(row, f"{report_id}.case_delta") for row in case_deltas],
    )


def _normalize_signal_payload(
    payload: dict[str, object],
    label: str,
) -> dict[str, JsonValue]:
    normalized: dict[str, JsonValue] = {
        "verdict": _require_string(payload.get("verdict"), f"{label}.verdict"),
        "regression_score": _require_number(
            payload.get("regression_score"), f"{label}.regression_score"
        ),
        "improvement_score": _require_number(
            payload.get("improvement_score"), f"{label}.improvement_score"
        ),
        "net_score": _require_number(payload.get("net_score"), f"{label}.net_score"),
        "severity": _require_number(payload.get("severity"), f"{label}.severity"),
    }
    reason = payload.get("reason")
    if reason is not None:
        normalized["reason"] = _require_string(reason, f"{label}.reason")

    raw_drivers = payload.get("top_drivers")
    if raw_drivers is None:
        normalized["top_drivers"] = []
        return normalized
    if not isinstance(raw_drivers, list):
        raise ValueError(f"{label}.top_drivers must be a list")
    drivers: list[dict[str, JsonValue]] = []
    for index, raw_driver in enumerate(raw_drivers):
        driver = _require_mapping(raw_driver, f"{label}.top_drivers[{index}]")
        drivers.append(
            {
                "failure_type": _require_string(
                    driver.get("failure_type"), f"{label}.top_drivers[{index}].failure_type"
                ),
                "delta": _require_number(driver.get("delta"), f"{label}.top_drivers[{index}].delta"),
                "direction": _require_string(
                    driver.get("direction"), f"{label}.top_drivers[{index}].direction"
                ),
                "case_ids": _require_string_list(
                    driver.get("case_ids"), f"{label}.top_drivers[{index}].case_ids"
                ),
            }
        )
    normalized["top_drivers"] = drivers
    return normalized


def _require_float_mapping(value: object, label: str) -> dict[str, float]:
    mapping = _require_mapping(value, label)
    normalized: dict[str, float] = {}
    for key, item in mapping.items():
        normalized[_require_string(key, label)] = _require_number(item, f"{label}.{key}")
    return normalized


def _signal_driver_rows(
    *,
    report_id: str,
    signal: dict[str, JsonValue],
) -> list[dict[str, object]]:
    raw_drivers = signal.get("top_drivers")
    if not isinstance(raw_drivers, list):
        return []
    rows: list[dict[str, object]] = []
    for index, raw_driver in enumerate(raw_drivers):
        if not isinstance(raw_driver, dict):
            continue
        failure_type = raw_driver.get("failure_type")
        delta = raw_driver.get("delta")
        direction = raw_driver.get("direction")
        case_ids = raw_driver.get("case_ids")
        if not isinstance(failure_type, str) or not isinstance(direction, str):
            continue
        if not isinstance(delta, (int, float)):
            continue
        case_ids_json = json.dumps(_require_string_list(case_ids, "signal_driver.case_ids"))
        rows.append(
            {
                "report_id": report_id,
                "driver_rank": index,
                "failure_type": failure_type,
                "delta": float(delta),
                "direction": direction,
                "case_ids_json": case_ids_json,
            }
        )
    return rows
