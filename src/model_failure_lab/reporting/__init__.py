"""Saved-evaluation reporting helpers with a lazy package surface."""

from __future__ import annotations

from importlib import import_module

_EXPORTS: dict[str, str] = {
    "BuiltReport": ".core",
    "CaseSummary": ".core",
    "PRIMARY_METRIC": ".legacy.figures",
    "PRIMARY_METRIC_LABEL": ".legacy.figures",
    "DEFAULT_REOPEN_CONDITIONS": ".legacy.closeout",
    "NO_FAILURE_TYPE": ".core",
    "PerturbationReportCandidate": ".legacy.discovery",
    "ReportCandidate": ".legacy.discovery",
    "SavedRunArtifacts": ".load",
    "build_clean_vs_perturbed_figure": ".legacy.figures",
    "build_comparison_report": ".compare",
    "build_comparison_report_id": ".compare",
    "build_perturbation_family_drop_figure": ".legacy.figures",
    "build_report_details_payload": ".artifacts",
    "build_perturbation_report_metadata": ".legacy.bundle",
    "build_perturbation_report_summary": ".legacy.summary",
    "build_perturbation_report_tables": ".legacy.perturbation",
    "build_report_payload": ".artifacts",
    "build_robustness_report_metadata": ".legacy.bundle",
    "write_robustness_report_bundle": ".legacy.bundle",
    "build_report_metadata": ".legacy.bundle",
    "build_run_report": ".core",
    "build_run_report_id": ".core",
    "build_stability_report_metadata": ".legacy.bundle",
    "write_comparison_report_artifacts": ".artifacts",
    "write_report_bundle": ".legacy.bundle",
    "write_report_artifacts": ".artifacts",
    "write_perturbation_report_bundle": ".legacy.bundle",
    "write_stability_report_bundle": ".legacy.bundle",
    "build_calibration_curve_figure": ".legacy.calibration",
    "build_calibration_table": ".legacy.calibration",
    "build_baseline_stability_table": ".legacy.stability",
    "build_comparison_table": ".legacy.tables",
    "build_default_reference_reports": ".legacy.stability",
    "build_id_ood_comparison_frame": ".legacy.figures",
    "build_id_ood_figure": ".legacy.figures",
    "build_mitigation_stability_table": ".legacy.stability",
    "build_mitigation_comparison_table": ".legacy.mitigation",
    "build_exploratory_mitigation_summary": ".legacy.robustness",
    "build_final_gate_payload": ".legacy.closeout",
    "build_final_robustness_summary": ".legacy.robustness",
    "build_official_mitigation_summary": ".legacy.robustness",
    "build_promotion_audit": ".legacy.robustness",
    "build_robustness_method_tables": ".legacy.robustness",
    "build_robustness_reference_reports": ".legacy.robustness",
    "build_robustness_story": ".legacy.robustness",
    "build_report_summary": ".legacy.summary",
    "build_seeded_baseline_summary": ".legacy.robustness",
    "build_stability_summary": ".legacy.stability",
    "build_severity_ladder_figure": ".legacy.figures",
    "build_subgroup_table": ".legacy.tables",
    "build_worst_group_vs_average_figure": ".legacy.figures",
    "build_worst_group_vs_average_frame": ".legacy.figures",
    "build_worst_subgroups_figure": ".legacy.figures",
    "build_worst_subgroups_frame": ".legacy.figures",
    "classify_mitigation_verdict": ".legacy.mitigation",
    "discover_evaluation_bundles": ".legacy.discovery",
    "discover_perturbation_bundles": ".legacy.discovery",
    "load_perturbation_candidates": ".legacy.discovery",
    "load_perturbation_report_inputs": ".legacy.perturbation",
    "load_report_inputs": ".legacy.discovery",
    "load_saved_run_artifacts": ".load",
    "load_saved_json": ".legacy.closeout",
    "load_saved_report_metadata": ".legacy.robustness",
    "load_saved_report_payload": ".legacy.robustness",
    "pair_mitigation_candidates_with_parents": ".legacy.mitigation",
    "report_label": ".legacy.selection",
    "render_perturbation_report_markdown": ".markdown",
    "render_promotion_audit_markdown": ".legacy.robustness",
    "render_robustness_report_markdown": ".markdown",
    "render_report_markdown": ".markdown",
    "render_stability_report_markdown": ".markdown",
    "select_report_candidates": ".legacy.selection",
    "summarize_case_executions": ".core",
    "validate_perturbation_report_candidates": ".legacy.perturbation",
    "validate_report_candidates": ".legacy.selection",
    "write_final_gate": ".legacy.closeout",
    "BASELINE_STABILITY_COLUMNS": ".legacy.stability",
    "MITIGATION_STABILITY_COLUMNS": ".legacy.stability",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> object:
    """Resolve exported reporting symbols lazily."""

    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    try:
        module = import_module(module_name, __name__)
    except ModuleNotFoundError as exc:
        # `reporting.legacy` is excluded from the wheel (see pyproject), so on an installed
        # package these names resolve to nothing. Say which surface the caller reached for
        # rather than leaving them with a bare module path.
        #
        # Only when the *package* is what is missing. The overwhelmingly common cause of a
        # ModuleNotFoundError here is a third-party import inside the legacy module -- a
        # checkout without the `[legacy]` extra -- and reporting that as "not shipped in
        # the installed package" replaced a correct, actionable error ("No module named
        # 'matplotlib'") with a false one. `exc.name` separates the two exactly.
        missing = exc.name or ""
        legacy_package = f"{__name__}.legacy"
        if module_name.startswith(".legacy") and (
            missing == legacy_package or missing.startswith(f"{legacy_package}.")
        ):
            raise AttributeError(
                f"'{name}' belongs to the legacy benchmark reporting surface, which is not "
                "shipped in the installed package (see docs/legacy.md). Work from a source "
                "checkout with the '[legacy]' extra installed to use it."
            ) from exc
        raise
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Expose lazy exports to interactive help and autocomplete."""

    return sorted(set(globals()) | set(__all__))
