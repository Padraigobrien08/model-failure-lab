"""Runner-side execution contracts and helpers for the new engine."""

from .contracts import (
    CaseClassification,
    CaseError,
    CaseExecution,
    CaseOutput,
    ExecutionMetadata,
    PromptSnapshot,
)
from .identity import build_run_id, derive_case_seed

__all__ = [
    "CaseClassification",
    "CaseError",
    "CaseExecution",
    "CaseOutput",
    "ExecutionMetadata",
    "PromptSnapshot",
    "build_run_id",
    "derive_case_seed",
]
