"""Machine-readable report summary builders."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .discovery import PerturbationReportCandidate, ReportCandidate
from .selection import report_label

MAX_HEADLINE_FINDINGS = 5
MITIGATION_VERDICTS = ("win", "tradeoff", "failure")
PREFERRED_MITIGATION_METHOD_ORDER = {
    "temperature_scaling": 0,
    "reweighting": 1,
}


def _format_score(value: object) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):.3f}"


def _build_headline_findings(
    comparison_table: pd.DataFrame,
    subgroup_table: pd.DataFrame,
    calibration_table: pd.DataFrame,
    mitigation_comparison_table: pd.DataFrame,
) -> list[str]:
    findings: list[str] = []

    if not comparison_table.empty:
        strongest_ood = comparison_table.sort_values(by="ood_score", ascending=False).iloc[0]
        findings.append(
            f"{strongest_ood['label']} has the strongest OOD Macro F1 at "
            f"{_format_score(strongest_ood['ood_score'])}."
        )

        largest_gap = comparison_table.sort_values(by="robustness_gap", ascending=False).iloc[0]
        findings.append(
            f"{largest_gap['label']} shows the largest ID-to-OOD Macro F1 drop at "
            f"{_format_score(largest_gap['robustness_gap'])}."
        )

    if not subgroup_table.empty:
        weakest_group = subgroup_table.sort_values(by="macro_f1", ascending=True).iloc[0]
        findings.append(
            f"The weakest reported subgroup is {weakest_group['group_name']} for "
            f"{weakest_group['label']} at Macro F1 {_format_score(weakest_group['macro_f1'])}."
        )

    if not calibration_table.empty:
        overall_rows = calibration_table.loc[calibration_table["slice_name"] == "overall"]
        if not overall_rows.empty:
            best_ece = overall_rows.sort_values(by="ece", ascending=True).iloc[0]
            findings.append(
                f"{best_ece['label']} has the best overall calibration with ECE "
                f"{_format_score(best_ece['ece'])}."
            )

    if not mitigation_comparison_table.empty:
        best_verdict = mitigation_comparison_table.iloc[0]
        findings.append(
            f"{best_verdict['mitigation_label']} is classified as "
            f"{best_verdict['verdict']} versus {best_verdict['parent_label']}."
        )

    return findings[:MAX_HEADLINE_FINDINGS]


def _build_mitigation_findings(mitigation_comparison_table: pd.DataFrame) -> list[str]:
    if mitigation_comparison_table.empty:
        return []

    findings: list[str] = []
    for _, row in mitigation_comparison_table.iterrows():
        findings.append(
            f"{row['mitigation_label']} vs {row['parent_label']}: verdict "
            f"{row['verdict']} (OOD Macro F1 delta {_format_score(row['ood_macro_f1_delta'])}, "
            f"worst-group F1 delta {_format_score(row['worst_group_f1_delta'])}, "
            f"ECE delta {_format_score(row['ece_delta'])})."
        )
    return findings[:MAX_HEADLINE_FINDINGS]


def _has_seeded_parent_coverage(mitigation_comparison_table: pd.DataFrame) -> bool:
    if mitigation_comparison_table.empty:
        return False
    parent_eval_ids = mitigation_comparison_table.get("parent_eval_id")
    if parent_eval_ids is None:
        return False
    return int(parent_eval_ids.nunique(dropna=True)) > 1


def _verdict_counts_for_table(mitigation_comparison_table: pd.DataFrame) -> dict[str, int]:
    verdict_series = mitigation_comparison_table.get("verdict")
    return {
        verdict: int((verdict_series == verdict).sum()) if verdict_series is not None else 0
        for verdict in MITIGATION_VERDICTS
    }


def _build_mitigation_verdict_counts(
    mitigation_comparison_table: pd.DataFrame,
) -> dict[str, int] | None:
    if (
        mitigation_comparison_table.empty
        or len(mitigation_comparison_table.index) <= 1
        or not _has_seeded_parent_coverage(mitigation_comparison_table)
    ):
        return None

    verdict_series = mitigation_comparison_table.get("verdict")
    if verdict_series is None:
        return None

    return _verdict_counts_for_table(mitigation_comparison_table)


def _build_seeded_interpretation(
    mitigation_verdict_counts: dict[str, int] | None,
) -> str | None:
    if mitigation_verdict_counts is None:
        return None

    wins = int(mitigation_verdict_counts["win"])
    tradeoffs = int(mitigation_verdict_counts["tradeoff"])
    failures = int(mitigation_verdict_counts["failure"])

    if wins >= 2 and failures == 0:
        return "stable"
    if wins >= 1 and (tradeoffs >= 1 or failures >= 1):
        return "mixed"
    if wins == 0 or failures > max(wins, tradeoffs):
        return "unsupported"
    return "unsupported"


def _method_sort_key(method_name: str) -> tuple[int, str]:
    return (
        PREFERRED_MITIGATION_METHOD_ORDER.get(method_name, len(PREFERRED_MITIGATION_METHOD_ORDER)),
        method_name,
    )


def _build_mitigation_method_summaries(
    mitigation_comparison_table: pd.DataFrame,
) -> dict[str, dict[str, Any]] | None:
    if (
        mitigation_comparison_table.empty
        or "mitigation_method" not in mitigation_comparison_table.columns
        or not _has_seeded_parent_coverage(mitigation_comparison_table)
    ):
        return None

    sanitized = mitigation_comparison_table.copy()
    sanitized["mitigation_method"] = sanitized["mitigation_method"].fillna("unknown").astype(str)
    method_names = sorted(sanitized["mitigation_method"].unique().tolist(), key=_method_sort_key)
    if len(method_names) <= 1:
        return None

    method_summaries: dict[str, dict[str, Any]] = {}
    for method_name in method_names:
        method_rows = sanitized.loc[sanitized["mitigation_method"] == method_name]
        verdict_counts = _verdict_counts_for_table(method_rows)
        method_summaries[method_name] = {
            "comparison_count": int(len(method_rows.index)),
            "verdict_counts": verdict_counts,
            "seeded_interpretation": _build_seeded_interpretation(verdict_counts),
        }

    return method_summaries


def build_report_summary(
    candidates: list[ReportCandidate],
    *,
    comparison_table: pd.DataFrame,
    subgroup_table: pd.DataFrame,
    calibration_table: pd.DataFrame,
    mitigation_comparison_table: pd.DataFrame | None = None,
    report_title: str,
) -> dict[str, Any]:
    """Build the optional machine-readable summary payload for a report."""
    resolved_mitigation_table = (
        mitigation_comparison_table
        if mitigation_comparison_table is not None
        else pd.DataFrame()
    )
    headline_findings = _build_headline_findings(
        comparison_table,
        subgroup_table,
        calibration_table,
        resolved_mitigation_table,
    )
    mitigation_findings = _build_mitigation_findings(resolved_mitigation_table)
    mitigation_verdict_counts = _build_mitigation_verdict_counts(
        resolved_mitigation_table
    )
    seeded_interpretation = _build_seeded_interpretation(mitigation_verdict_counts)
    mitigation_method_summaries = _build_mitigation_method_summaries(
        resolved_mitigation_table
    )
    compared_runs = [
        {
            "eval_id": candidate.eval_id,
            "label": report_label(candidate),
            "model_name": candidate.metadata.get("model_name"),
            "source_run_id": candidate.metadata.get("source_run_id"),
        }
        for candidate in candidates
    ]
    key_takeaway = headline_findings[0] if headline_findings else "No report findings available."
    next_experiment = "Run mitigation comparisons against the strongest OOD baseline."
    return {
        "report_title": report_title,
        "headline_findings": headline_findings,
        "mitigation_findings": mitigation_findings,
        "compared_runs": compared_runs,
        "key_takeaway": key_takeaway,
        "next_experiment": next_experiment,
        "mitigation_verdict_counts": mitigation_verdict_counts,
        "seeded_interpretation": seeded_interpretation,
        "mitigation_method_summaries": mitigation_method_summaries,
    }


def build_perturbation_report_summary(
    candidates: list[PerturbationReportCandidate],
    *,
    suite_summary: pd.DataFrame,
    family_summary: pd.DataFrame,
    severity_summary: pd.DataFrame,
    report_title: str,
) -> dict[str, Any]:
    """Build the machine-readable summary payload for a perturbation report."""
    findings: list[str] = []

    if not suite_summary.empty:
        largest_drop = suite_summary.sort_values(by="macro_f1_drop", ascending=False).iloc[0]
        findings.append(
            f"{largest_drop['label']} drops by {_format_score(largest_drop['macro_f1_drop'])} "
            "Macro F1 on average under the perturbation suite."
        )

    if not family_summary.empty:
        worst_family = family_summary.sort_values(by="macro_f1_drop", ascending=False).iloc[0]
        findings.append(
            f"The worst perturbation family is {worst_family['perturbation_family']} for "
            f"{worst_family['label']} with Macro F1 drop "
            f"{_format_score(worst_family['macro_f1_drop'])}."
        )

    if not severity_summary.empty:
        steepest_severity = severity_summary.sort_values(
            by="macro_f1_drop",
            ascending=False,
        ).iloc[0]
        findings.append(
            f"Severity {steepest_severity['severity']} is the harshest setting for "
            f"{steepest_severity['label']} with Macro F1 drop "
            f"{_format_score(steepest_severity['macro_f1_drop'])}."
        )

    compared_runs = [
        {
            "eval_id": candidate.eval_id,
            "label": report_label(candidate),
            "model_name": candidate.metadata.get("model_name"),
            "source_run_id": candidate.metadata.get("source_run_id"),
        }
        for candidate in candidates
    ]
    key_takeaway = findings[0] if findings else "No perturbation findings available."
    return {
        "report_title": report_title,
        "headline_findings": findings[:MAX_HEADLINE_FINDINGS],
        "compared_runs": compared_runs,
        "key_takeaway": key_takeaway,
        "next_experiment": "Compare mitigation runs on the same perturbation suite.",
    }
