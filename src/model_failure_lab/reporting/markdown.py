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
        "## Key takeaway",
        key_takeaway,
        "## Next experiment",
        next_experiment,
    ]
    return "\n\n".join(section for section in sections if section.strip()) + "\n"
