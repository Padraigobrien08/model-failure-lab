"""Saved-evaluation reporting helpers."""

from .discovery import ReportCandidate, discover_evaluation_bundles, load_report_inputs
from .figures import (
    PRIMARY_METRIC,
    PRIMARY_METRIC_LABEL,
    build_id_ood_comparison_frame,
    build_id_ood_figure,
    build_worst_group_vs_average_figure,
    build_worst_group_vs_average_frame,
    build_worst_subgroups_figure,
    build_worst_subgroups_frame,
)
from .selection import report_label, select_report_candidates, validate_report_candidates

__all__ = [
    "PRIMARY_METRIC",
    "PRIMARY_METRIC_LABEL",
    "ReportCandidate",
    "build_id_ood_comparison_frame",
    "build_id_ood_figure",
    "build_worst_group_vs_average_figure",
    "build_worst_group_vs_average_frame",
    "build_worst_subgroups_figure",
    "build_worst_subgroups_frame",
    "discover_evaluation_bundles",
    "load_report_inputs",
    "report_label",
    "select_report_candidates",
    "validate_report_candidates",
]
