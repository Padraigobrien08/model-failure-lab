"""Saved-evaluation reporting helpers."""

from .bundle import (
    build_perturbation_report_metadata,
    build_report_metadata,
    write_perturbation_report_bundle,
    write_report_bundle,
)
from .calibration import build_calibration_curve_figure, build_calibration_table
from .discovery import (
    PerturbationReportCandidate,
    ReportCandidate,
    discover_evaluation_bundles,
    discover_perturbation_bundles,
    load_perturbation_candidates,
    load_report_inputs,
)
from .figures import (
    PRIMARY_METRIC,
    PRIMARY_METRIC_LABEL,
    build_clean_vs_perturbed_figure,
    build_id_ood_comparison_frame,
    build_id_ood_figure,
    build_perturbation_family_drop_figure,
    build_severity_ladder_figure,
    build_worst_group_vs_average_figure,
    build_worst_group_vs_average_frame,
    build_worst_subgroups_figure,
    build_worst_subgroups_frame,
)
from .markdown import render_perturbation_report_markdown, render_report_markdown
from .mitigation import (
    build_mitigation_comparison_table,
    classify_mitigation_verdict,
    pair_mitigation_candidates_with_parents,
)
from .perturbation import (
    build_perturbation_report_tables,
    load_perturbation_report_inputs,
    validate_perturbation_report_candidates,
)
from .selection import report_label, select_report_candidates, validate_report_candidates
from .summary import build_perturbation_report_summary, build_report_summary
from .tables import build_comparison_table, build_subgroup_table

__all__ = [
    "PRIMARY_METRIC",
    "PRIMARY_METRIC_LABEL",
    "PerturbationReportCandidate",
    "ReportCandidate",
    "build_clean_vs_perturbed_figure",
    "build_perturbation_family_drop_figure",
    "build_perturbation_report_metadata",
    "build_perturbation_report_summary",
    "build_perturbation_report_tables",
    "build_report_metadata",
    "write_report_bundle",
    "write_perturbation_report_bundle",
    "build_calibration_curve_figure",
    "build_calibration_table",
    "build_comparison_table",
    "build_id_ood_comparison_frame",
    "build_id_ood_figure",
    "build_mitigation_comparison_table",
    "build_report_summary",
    "build_severity_ladder_figure",
    "build_subgroup_table",
    "build_worst_group_vs_average_figure",
    "build_worst_group_vs_average_frame",
    "build_worst_subgroups_figure",
    "build_worst_subgroups_frame",
    "classify_mitigation_verdict",
    "discover_evaluation_bundles",
    "discover_perturbation_bundles",
    "load_perturbation_candidates",
    "load_perturbation_report_inputs",
    "load_report_inputs",
    "pair_mitigation_candidates_with_parents",
    "report_label",
    "render_perturbation_report_markdown",
    "render_report_markdown",
    "select_report_candidates",
    "validate_perturbation_report_candidates",
    "validate_report_candidates",
]
