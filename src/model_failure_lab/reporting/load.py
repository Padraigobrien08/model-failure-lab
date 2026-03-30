"""Load saved runner artifacts for reporting and comparison."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from model_failure_lab.runner import CaseExecution
from model_failure_lab.schemas import Run
from model_failure_lab.storage import read_json, results_file, run_file


@dataclass(slots=True, frozen=True)
class SavedRunArtifacts:
    """Saved Phase 46 run artifacts normalized for reporting."""

    run: Run
    adapter_id: str
    classifier_id: str
    status: str
    total_cases: int
    error_count: int
    case_results: tuple[CaseExecution, ...]

    @property
    def dataset_id(self) -> str:
        return self.run.dataset

    @property
    def case_ids(self) -> tuple[str, ...]:
        return tuple(case.case_id for case in self.case_results)

    def case_map(self) -> dict[str, CaseExecution]:
        return {case.case_id: case for case in self.case_results}


def load_saved_run_artifacts(run_id: str, *, root: str | Path | None = None) -> SavedRunArtifacts:
    """Load one saved run plus its per-case results from deterministic local storage."""

    run_payload = read_json(run_file(run_id, root=root))
    results_payload = read_json(results_file(run_id, root=root))
    run = Run.from_payload(run_payload)

    payload_run_id = str(results_payload.get("run_id", ""))
    if payload_run_id != run.run_id:
        raise ValueError(
            f"results artifact run_id mismatch: expected {run.run_id!r}, got {payload_run_id!r}"
        )

    cases_payload = results_payload.get("cases")
    if not isinstance(cases_payload, list):
        raise ValueError("results artifact must contain a `cases` list")

    return SavedRunArtifacts(
        run=run,
        adapter_id=_string_field(
            results_payload, "adapter_id", fallback=run.metadata.get("adapter_id")
        ),
        classifier_id=_string_field(
            results_payload,
            "classifier_id",
            fallback=run.metadata.get("classifier_id"),
        ),
        status=_string_field(results_payload, "status", fallback=run.metadata.get("status")),
        total_cases=_int_field(results_payload, "total_cases", fallback=len(cases_payload)),
        error_count=_int_field(results_payload, "error_count", fallback=0),
        case_results=tuple(CaseExecution.from_payload(item) for item in cases_payload),
    )


def _string_field(payload: dict[str, object], key: str, *, fallback: object) -> str:
    value = payload.get(key, fallback)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string in saved run artifacts")
    return value


def _int_field(payload: dict[str, object], key: str, *, fallback: object) -> int:
    value = payload.get(key, fallback)
    if type(value) is not int:
        raise ValueError(f"{key} must be an integer in saved run artifacts")
    return value
