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


def _render_stability_cohort_summaries(
    stability_summary: dict[str, Any],
) -> str:
    cohort_summaries = stability_summary.get("cohort_summaries", {})
    if not isinstance(cohort_summaries, dict):
        return ""

    ordered_keys = [
        "logistic_baseline",
        "distilbert_baseline",
        "temperature_scaling",
        "reweighting",
    ]
    lines: list[str] = []
    for key in ordered_keys:
        summary = cohort_summaries.get(key)
        if not isinstance(summary, dict):
            continue
        label = str(summary.get("label", "n/a"))
        seed_count = int(summary.get("seed_count", 0))
        lines.append(f"- `{key}`: `{label}` across `n={seed_count}` seed rows.")
        verdict_counts = summary.get("verdict_counts")
        if isinstance(verdict_counts, dict):
            lines.append(
                (
                    f"- `{key}` verdict counts: "
                    f"`win={int(verdict_counts.get('win', 0))}`, "
                    f"`tradeoff={int(verdict_counts.get('tradeoff', 0))}`, "
                    f"`failure={int(verdict_counts.get('failure', 0))}`"
                )
            )
    return "\n".join(lines)


def _render_stability_model_comparison(stability_summary: dict[str, Any]) -> str:
    model_comparison = stability_summary.get("baseline_model_comparison")
    if not isinstance(model_comparison, dict):
        return ""
    label = str(model_comparison.get("label", "n/a"))
    mean_deltas = model_comparison.get("mean_deltas", {})
    ood_delta = mean_deltas.get("ood_macro_f1_delta")
    worst_delta = mean_deltas.get("worst_group_f1_delta")
    ood_text = "n/a" if ood_delta is None else f"{float(ood_delta):.3f}"
    worst_text = "n/a" if worst_delta is None else f"{float(worst_delta):.3f}"
    return "\n".join(
        [
            f"- Logistic vs DistilBERT comparison: `{label}`",
            (
                "- Mean DistilBERT-minus-Logistic deltas: "
                f"`ood_macro_f1={ood_text}`, `worst_group_f1={worst_text}`"
            ),
        ]
    )


def _render_stability_references(stability_summary: dict[str, Any]) -> str:
    references = stability_summary.get("reference_reports", {})
    if not isinstance(references, dict):
        return ""
    lines: list[str] = []
    for key in ("temperature_scaling_seeded", "reweighting_seeded"):
        path = references.get(key)
        if path:
            lines.append(f"- `{key}`: `{path}`")
    return "\n".join(lines)


def render_stability_report_markdown(
    *,
    report_title: str,
    stability_summary: dict[str, Any],
    table_paths: dict[str, str],
) -> str:
    """Render the canonical seeded stability Markdown findings report."""
    headline_findings = list(stability_summary.get("headline_findings", []))[:5]
    key_takeaway = str(stability_summary.get("key_takeaway", "No key takeaway available."))
    milestone_assessment = stability_summary.get("milestone_assessment", {})
    if not isinstance(milestone_assessment, dict):
        milestone_assessment = {}
    findings_status = str(milestone_assessment.get("v1_1_findings_status", "n/a"))
    dataset_expansion = str(
        milestone_assessment.get("dataset_expansion_recommendation", "n/a")
    )
    recommendation_reason = str(
        milestone_assessment.get("recommendation_reason", "No recommendation reason available.")
    )
    next_step = str(
        milestone_assessment.get("next_step", "Choose the next milestone from saved evidence.")
    )

    sections = [
        f"# {report_title}",
        "## Overview",
        (
            "This report aggregates saved official evaluation bundles only. "
            "No new runs are executed in Phase 20; all conclusions come from the locked seeded "
            "baseline and mitigation cohorts."
        ),
        "## Headline findings",
        _render_headline_findings(headline_findings),
        "## Cohort stability labels",
        _render_stability_cohort_summaries(stability_summary),
        (
            f"- Baseline stability table: `{table_paths['baseline_stability']}`"
            if table_paths.get("baseline_stability")
            else ""
        ),
        (
            f"- Temperature-scaling deltas: `{table_paths['temperature_scaling_deltas']}`"
            if table_paths.get("temperature_scaling_deltas")
            else ""
        ),
        (
            f"- Reweighting deltas: `{table_paths['reweighting_deltas']}`"
            if table_paths.get("reweighting_deltas")
            else ""
        ),
        "## Baseline model comparison",
        _render_stability_model_comparison(stability_summary),
        "## Existing seeded mitigation packages",
        _render_stability_references(stability_summary),
        "## Milestone recommendation",
        f"- Original `v1.1` findings under seed variation: `{findings_status}`",
        f"- Dataset expansion recommendation: `{dataset_expansion}`",
        f"- Reason: {recommendation_reason}",
        f"- Next step: {next_step}",
        "## Key takeaway",
        key_takeaway,
    ]
    return "\n\n".join(section for section in sections if section.strip()) + "\n"
