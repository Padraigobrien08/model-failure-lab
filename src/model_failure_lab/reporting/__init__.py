"""Saved-evaluation reporting helpers with a lazy package surface."""

from __future__ import annotations

from importlib import import_module

_EXPORTS: dict[str, str] = {
    "BuiltReport": ".core",
    "CaseSummary": ".core",
    "PRIMARY_METRIC": ".figures",
    "PRIMARY_METRIC_LABEL": ".figures",
    "DEFAULT_REOPEN_CONDITIONS": ".closeout",
    "NO_FAILURE_TYPE": ".core",
    "PerturbationReportCandidate": ".discovery",
    "ReportCandidate": ".discovery",
    "SavedRunArtifacts": ".load",
    "build_clean_vs_perturbed_figure": ".figures",
    "build_comparison_report": ".compare",
    "build_comparison_report_id": ".compare",
    "build_perturbation_family_drop_figure": ".figures",
    "build_report_details_payload": ".artifacts",
    "build_perturbation_report_metadata": ".bundle",
    "build_perturbation_report_summary": ".summary",
    "build_perturbation_report_tables": ".perturbation",
    "build_report_payload": ".artifacts",
    "build_robustness_report_metadata": ".bundle",
    "write_robustness_report_bundle": ".bundle",
    "build_report_metadata": ".bundle",
    "build_run_report": ".core",
    "build_run_report_id": ".core",
    "build_stability_report_metadata": ".bundle",
    "write_comparison_report_artifacts": ".artifacts",
    "write_report_bundle": ".bundle",
    "write_report_artifacts": ".artifacts",
    "write_perturbation_report_bundle": ".bundle",
    "write_stability_report_bundle": ".bundle",
    "build_calibration_curve_figure": ".calibration",
    "build_calibration_table": ".calibration",
    "build_baseline_stability_table": ".stability",
    "build_comparison_table": ".tables",
    "build_default_reference_reports": ".stability",
    "build_id_ood_comparison_frame": ".figures",
    "build_id_ood_figure": ".figures",
    "build_mitigation_stability_table": ".stability",
    "build_mitigation_comparison_table": ".mitigation",
    "build_exploratory_mitigation_summary": ".robustness",
    "build_final_gate_payload": ".closeout",
    "build_final_robustness_summary": ".robustness",
    "build_official_mitigation_summary": ".robustness",
    "build_promotion_audit": ".robustness",
    "build_robustness_method_tables": ".robustness",
    "build_robustness_reference_reports": ".robustness",
    "build_robustness_story": ".robustness",
    "build_report_summary": ".summary",
    "build_seeded_baseline_summary": ".robustness",
    "build_stability_summary": ".stability",
    "build_severity_ladder_figure": ".figures",
    "build_subgroup_table": ".tables",
    "build_worst_group_vs_average_figure": ".figures",
    "build_worst_group_vs_average_frame": ".figures",
    "build_worst_subgroups_figure": ".figures",
    "build_worst_subgroups_frame": ".figures",
    "classify_mitigation_verdict": ".mitigation",
    "discover_evaluation_bundles": ".discovery",
    "discover_perturbation_bundles": ".discovery",
    "load_perturbation_candidates": ".discovery",
    "load_perturbation_report_inputs": ".perturbation",
    "load_report_inputs": ".discovery",
    "load_saved_run_artifacts": ".load",
    "load_saved_json": ".closeout",
    "load_saved_report_metadata": ".robustness",
    "load_saved_report_payload": ".robustness",
    "pair_mitigation_candidates_with_parents": ".mitigation",
    "report_label": ".selection",
    "render_perturbation_report_markdown": ".markdown",
    "render_promotion_audit_markdown": ".robustness",
    "render_robustness_report_markdown": ".markdown",
    "render_report_markdown": ".markdown",
    "render_stability_report_markdown": ".markdown",
    "select_report_candidates": ".selection",
    "summarize_case_executions": ".core",
    "validate_perturbation_report_candidates": ".perturbation",
    "validate_report_candidates": ".selection",
    "write_final_gate": ".closeout",
    "BASELINE_STABILITY_COLUMNS": ".stability",
    "MITIGATION_STABILITY_COLUMNS": ".stability",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> object:
    """Resolve exported reporting symbols lazily."""

    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Expose lazy exports to interactive help and autocomplete."""

    return sorted(set(globals()) | set(__all__))
