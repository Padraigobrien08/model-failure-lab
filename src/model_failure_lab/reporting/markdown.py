"""Markdown report rendering for Phase 5 findings packages."""

from __future__ import annotations

from typing import Any


def _render_compared_runs(compared_runs: list[dict[str, Any]]) -> str:
    lines = []
    for candidate in compared_runs:
        lines.append(
            f"- `{candidate['label']}` (`eval_id={candidate['eval_id']}`, "
            f"`source_run_id={candidate['source_run_id']}`)"
        )
    return "\n".join(lines)


def _render_headline_findings(findings: list[str]) -> str:
    return "\n".join(f"- {finding}" for finding in findings[:5])


def _render_mitigation_findings(findings: list[str]) -> str:
    return "\n".join(f"- {finding}" for finding in findings[:5])


def _render_seeded_mitigation_summary(report_summary: dict[str, Any]) -> str:
    verdict_counts = report_summary.get("mitigation_verdict_counts")
    seeded_interpretation = report_summary.get("seeded_interpretation")
    if not isinstance(verdict_counts, dict) or not seeded_interpretation:
        return ""

    return "\n".join(
        [
            f"- Seeded interpretation: `{seeded_interpretation}`",
            (
                "- Verdict counts: "
                f"`win={int(verdict_counts.get('win', 0))}`, "
                f"`tradeoff={int(verdict_counts.get('tradeoff', 0))}`, "
                f"`failure={int(verdict_counts.get('failure', 0))}`"
            ),
        ]
    )


def _render_method_aware_seeded_mitigation_summary(report_summary: dict[str, Any]) -> str:
    method_summaries = report_summary.get("mitigation_method_summaries")
    if not isinstance(method_summaries, dict) or len(method_summaries) <= 1:
        return ""

    lines: list[str] = []
    for method_name, summary in method_summaries.items():
        if not isinstance(summary, dict):
            continue
        verdict_counts = summary.get("verdict_counts", {})
        if not isinstance(verdict_counts, dict):
            verdict_counts = {}
        seeded_interpretation = summary.get("seeded_interpretation", "unsupported")
        comparison_count = int(summary.get("comparison_count", 0))
        lines.append(
            f"- `{method_name}`: interpretation `{seeded_interpretation}` across "
            f"`n={comparison_count}` seeded comparisons."
        )
        lines.append(
            (
                f"- `{method_name}` verdict counts: "
                f"`win={int(verdict_counts.get('win', 0))}`, "
                f"`tradeoff={int(verdict_counts.get('tradeoff', 0))}`, "
                f"`failure={int(verdict_counts.get('failure', 0))}`"
            )
        )
    return "\n".join(lines)


def render_report_markdown(
    *,
    report_title: str,
    report_summary: dict[str, Any],
    figure_paths: dict[str, str],
    table_paths: dict[str, str],
) -> str:
    """Render the canonical Phase 5 Markdown findings report."""
    compared_runs = report_summary.get("compared_runs", [])
    headline_findings = list(report_summary.get("headline_findings", []))[:5]
    mitigation_findings = list(report_summary.get("mitigation_findings", []))[:5]
    seeded_mitigation_summary = _render_seeded_mitigation_summary(report_summary)
    method_aware_seeded_mitigation_summary = _render_method_aware_seeded_mitigation_summary(
        report_summary
    )
    key_takeaway = str(report_summary.get("key_takeaway", "No key takeaway available."))
    next_experiment = str(
        report_summary.get("next_experiment", "Choose the next comparable evaluation bundle.")
    )

    sections = [
        f"# {report_title}",
        "## Overview",
        (
            "This report summarizes saved evaluation bundles only. "
            "Metrics and visuals are read from persisted Phase 4 artifacts."
        ),
        "## Compared runs",
        _render_compared_runs(compared_runs),
        "## Headline findings",
        _render_headline_findings(headline_findings),
        "## ID vs OOD degradation",
        f"![ID vs OOD primary metric]({figure_paths['id_vs_ood_primary_metric']})",
        f"- Comparison table: `{table_paths['comparison_table']}`",
        "## Worst-group failure",
        f"![Worst-group vs average]({figure_paths['worst_group_vs_average']})",
        f"![Worst subgroups]({figure_paths['worst_subgroups']})",
        f"- Subgroup table: `{table_paths['subgroup_table']}`",
        "## Calibration summary",
        f"![Calibration curve]({figure_paths['calibration_curve']})",
        f"- Calibration table: `{table_paths['calibration_table']}`",
        "## Mitigation comparison" if mitigation_findings else "",
        _render_mitigation_findings(mitigation_findings) if mitigation_findings else "",
        (
            f"- Mitigation comparison table: `{table_paths['mitigation_comparison_table']}`"
            if mitigation_findings
            else ""
        ),
        "## Seeded mitigation summary" if seeded_mitigation_summary else "",
        seeded_mitigation_summary,
        (
            "## Method-aware seeded mitigation summary"
            if method_aware_seeded_mitigation_summary
            else ""
        ),
        method_aware_seeded_mitigation_summary,
        "## Key takeaway",
        key_takeaway,
        "## Next experiment",
        next_experiment,
    ]
    return "\n\n".join(section for section in sections if section.strip()) + "\n"


def render_perturbation_report_markdown(
    *,
    report_title: str,
    report_summary: dict[str, Any],
    figure_paths: dict[str, str],
    table_paths: dict[str, str],
) -> str:
    """Render the canonical Phase 7 Markdown perturbation report."""
    compared_runs = report_summary.get("compared_runs", [])
    headline_findings = list(report_summary.get("headline_findings", []))[:5]
    key_takeaway = str(report_summary.get("key_takeaway", "No key takeaway available."))
    next_experiment = str(
        report_summary.get("next_experiment", "Choose the next perturbation bundle.")
    )

    sections = [
        f"# {report_title}",
        "## Overview",
        (
            "This report summarizes saved synthetic perturbation bundles only. "
            "Clean baselines come from saved validation predictions, and perturbed outputs come "
            "from deterministic synthetic stress suites. These findings are not canonical WILDS "
            "ID/OOD benchmark claims."
        ),
        "## Source run evaluated",
        _render_compared_runs(compared_runs),
        "## Clean vs perturbed summary",
        _render_headline_findings(headline_findings),
        (
            "![Clean vs perturbed primary metric]"
            f"({figure_paths['clean_vs_perturbed_primary_metric']})"
        ),
        f"- Suite summary table: `{table_paths['suite_summary']}`",
        "## Worst perturbation families",
        f"![Perturbation family drop]({figure_paths['perturbation_family_drop']})",
        f"- Family summary table: `{table_paths['family_summary']}`",
        "## Severity sensitivity",
        f"![Severity ladder]({figure_paths['severity_ladder']})",
        f"- Severity summary table: `{table_paths['severity_summary']}`",
        f"- Family-by-severity table: `{table_paths['family_severity_matrix']}`",
        "## Key takeaway",
        key_takeaway,
        "## Next experiment",
        next_experiment,
    ]
    return "\n\n".join(section for section in sections if section.strip()) + "\n"
