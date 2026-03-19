"""Saved-run evaluation helpers."""

from .aggregate import build_split_metrics_rows, compute_aggregate_metrics
from .calibration import build_calibration_bins, compute_calibration_summary
from .diagnostics import build_confidence_summary, build_diagnostics_payload
from .loaders import load_saved_predictions, select_prediction_splits
from .robustness import build_id_ood_comparison, compute_robustness_gaps
from .subgroup import build_worst_group_summary, compute_subgroup_metrics

__all__ = [
    "build_calibration_bins",
    "build_confidence_summary",
    "build_diagnostics_payload",
    "build_id_ood_comparison",
    "build_split_metrics_rows",
    "build_worst_group_summary",
    "compute_calibration_summary",
    "compute_aggregate_metrics",
    "compute_subgroup_metrics",
    "compute_robustness_gaps",
    "load_saved_predictions",
    "select_prediction_splits",
]
