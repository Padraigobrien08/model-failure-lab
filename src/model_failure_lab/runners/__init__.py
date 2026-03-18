"""Thin dispatch contracts for script entrypoints."""

from .contracts import DispatchResult
from .dispatch import (
    build_scaffold_metrics,
    dispatch_baseline,
    dispatch_data_download,
    dispatch_mitigation,
    dispatch_report,
    dispatch_shift_eval,
)

__all__ = [
    "DispatchResult",
    "build_scaffold_metrics",
    "dispatch_baseline",
    "dispatch_data_download",
    "dispatch_mitigation",
    "dispatch_report",
    "dispatch_shift_eval",
]
