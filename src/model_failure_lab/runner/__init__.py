"""Runner-side execution contracts and helpers for the new engine."""

from .artifacts import build_results_payload, build_run_payload, write_run_artifacts
from .contracts import (
    CaseClassification,
    CaseError,
    CaseExecution,
    CaseOutput,
    ExecutionMetadata,
    PromptSnapshot,
)
from .execute import DatasetRunExecution, execute_dataset_run
from .identity import build_run_id, derive_case_seed

__all__ = [
    "build_results_payload",
    "build_run_payload",
    "write_run_artifacts",
    "CaseClassification",
    "CaseError",
    "CaseExecution",
    "CaseOutput",
    "ExecutionMetadata",
    "PromptSnapshot",
    "DatasetRunExecution",
    "execute_dataset_run",
    "build_run_id",
    "derive_case_seed",
]
