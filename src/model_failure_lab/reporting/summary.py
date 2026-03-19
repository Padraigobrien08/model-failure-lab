"""Machine-readable report summary builders."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .discovery import ReportCandidate
from .selection import report_label

MAX_HEADLINE_FINDINGS = 5


def _format_score(value: object) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):.3f}"


def _build_headline_findings(
    comparison_table: pd.DataFrame,
    subgroup_table: pd.DataFrame,
    calibration_table: pd.DataFrame,
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

    return findings[:MAX_HEADLINE_FINDINGS]


def build_report_summary(
    candidates: list[ReportCandidate],
    *,
    comparison_table: pd.DataFrame,
    subgroup_table: pd.DataFrame,
    calibration_table: pd.DataFrame,
    report_title: str,
) -> dict[str, Any]:
    """Build the optional machine-readable summary payload for a report."""
    headline_findings = _build_headline_findings(
        comparison_table,
        subgroup_table,
        calibration_table,
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
        "compared_runs": compared_runs,
        "key_takeaway": key_takeaway,
        "next_experiment": next_experiment,
    }
