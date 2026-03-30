"""Artifact emission helpers for executed dataset runs."""

from __future__ import annotations

from pathlib import Path

from model_failure_lab.schemas import JsonValue
from model_failure_lab.storage import results_file, run_file, write_json

from .execute import DatasetRunExecution


def build_run_payload(run_execution: DatasetRunExecution) -> dict[str, JsonValue]:
    """Build the persisted `run.json` payload for one executed dataset run."""

    return run_execution.run.to_payload()


def build_results_payload(run_execution: DatasetRunExecution) -> dict[str, JsonValue]:
    """Build the persisted `results.json` payload for one executed dataset run."""

    return {
        "run_id": run_execution.run.run_id,
        "dataset_id": run_execution.run.dataset,
        "adapter_id": run_execution.adapter_id,
        "classifier_id": run_execution.classifier_id,
        "status": run_execution.status,
        "total_cases": run_execution.total_cases,
        "error_count": run_execution.error_count,
        "cases": [case.to_payload() for case in run_execution.case_results],
    }


def write_run_artifacts(
    run_execution: DatasetRunExecution,
    *,
    root: str | Path | None = None,
) -> tuple[Path, Path]:
    """Persist one executed dataset run through the Phase 44 storage helpers."""

    run_path = run_file(run_execution.run.run_id, root=root, create=True)
    results_path = results_file(run_execution.run.run_id, root=root, create=True)
    write_json(run_path, build_run_payload(run_execution))
    write_json(results_path, build_results_payload(run_execution))
    return run_path, results_path
