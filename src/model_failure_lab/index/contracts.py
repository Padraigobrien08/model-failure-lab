"""Artifact/query-index contract validation helpers."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from model_failure_lab.datasets.integrity import (
    DatasetIntegrityError,
    audit_dataset_directory,
    load_promotion_ledger,
)
from model_failure_lab.storage.layout import datasets_root, project_root

from .builder import QUERY_INDEX_SCHEMA_VERSION, query_index_path, rebuild_query_index

REQUIRED_INDEX_TABLES = (
    "metadata",
    "runs",
    "cases",
    "dataset_versions",
    "comparisons",
    "case_deltas",
    "signal_drivers",
    "cluster_occurrences",
)


@dataclass(slots=True, frozen=True)
class ArtifactContractValidation:
    schema_version: str
    required_tables_present: bool
    missing_tables: tuple[str, ...]
    run_count: int
    comparison_count: int
    case_count: int
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_payload(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "schema_version": self.schema_version,
            "expected_schema_version": QUERY_INDEX_SCHEMA_VERSION,
            "required_tables_present": self.required_tables_present,
            "missing_tables": list(self.missing_tables),
            "run_count": self.run_count,
            "comparison_count": self.comparison_count,
            "case_count": self.case_count,
            "errors": list(self.errors),
        }


def validate_artifact_contracts(*, root: str | Path | None = None) -> ArtifactContractValidation:
    # Force a strict rebuild so validation actually re-reads every source artifact
    # through the builder's field-level contract checks (`_require_string`, etc.),
    # rather than trusting a possibly-current derived index. A malformed run,
    # report, or comparison artifact raises here and is reported as a contract
    # error instead of silently passing.
    # The integrity sweep runs first and is the single reporter for dataset-integrity
    # problems: it answers "can I still prove the curated packs are the ones that were
    # promoted", which is a different question from the builder's "can I read these
    # artifacts", and it catches the case a load cannot -- a pack whose digest was deleted
    # reads perfectly.
    integrity_errors = [
        finding.message()
        for finding in audit_dataset_directory(
            datasets_root(root=root),
            ledger=load_promotion_ledger(project_root(root)),
        )
    ]

    ingestion_errors: list[str] = []
    try:
        rebuild_query_index(root=root)
    except DatasetIntegrityError as exc:
        # A tampered pack used to escape as an unhandled exception, so `index validate`
        # crashed with exit 1 instead of reporting a contract error with its documented
        # exit 2. Only report it here when the sweep did not already name it -- a pack
        # outside `datasets/` can still fail the load.
        if not integrity_errors:
            ingestion_errors.append(f"dataset integrity: {exc}")
    except (ValueError, KeyError) as exc:
        ingestion_errors.append(f"artifact contract violation: {exc}")
    ingestion_errors = integrity_errors + ingestion_errors

    index_path = query_index_path(root=root)
    if not index_path.exists():
        # The rebuild failed before writing an index; report the ingestion error
        # without attempting to open a non-existent database.
        return ArtifactContractValidation(
            schema_version="missing",
            required_tables_present=False,
            missing_tables=REQUIRED_INDEX_TABLES,
            run_count=0,
            comparison_count=0,
            case_count=0,
            errors=tuple(ingestion_errors or ("query index could not be built",)),
        )
    with sqlite3.connect(index_path) as connection:
        schema_row = connection.execute(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        ).fetchone()
        schema_version = str(schema_row[0]) if schema_row is not None else "missing"
        tables = {
            str(row[0])
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        missing_tables = tuple(
            table_name for table_name in REQUIRED_INDEX_TABLES if table_name not in tables
        )
        run_count = _count_rows(connection, "runs")
        comparison_count = _count_rows(connection, "comparisons")
        case_count = _count_rows(connection, "cases")

    errors: list[str] = list(ingestion_errors)
    if schema_version != QUERY_INDEX_SCHEMA_VERSION:
        errors.append(
            f"schema_version mismatch: expected {QUERY_INDEX_SCHEMA_VERSION}, got {schema_version}"
        )
    if missing_tables:
        errors.append(f"missing index tables: {', '.join(missing_tables)}")
    return ArtifactContractValidation(
        schema_version=schema_version,
        required_tables_present=not missing_tables,
        missing_tables=missing_tables,
        run_count=run_count,
        comparison_count=comparison_count,
        case_count=case_count,
        errors=tuple(errors),
    )


def _count_rows(connection: sqlite3.Connection, table_name: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    return int(row[0]) if row is not None else 0
