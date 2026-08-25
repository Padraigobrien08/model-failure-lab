"""Helpers for Phase 26 robustness synthesis and promotion audits."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from model_failure_lab.utils.paths import repository_root

_DELTA_METRIC_KEYS = {
    "id_macro_f1": "id_macro_f1_delta",
    "ood_macro_f1": "ood_macro_f1_delta",
    "worst_group_f1": "worst_group_f1_delta",
    "robustness_gap_f1": "robustness_gap_delta",
    "ece": "ece_delta",
    "brier_score": "brier_score_delta",
}

_METHOD_ORDER = [
    "distilbert_baseline",
    "temperature_scaling",
    "reweighting",
    "group_dro",
    "group_balanced_sampling",
]


def _canonical_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repository_root()))
    except ValueError:
        return path.as_posix()


def load_saved_report_payload(path: Path | str) -> dict[str, Any]:
    """Load one saved JSON payload from disk."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_saved_report_metadata(path: Path | str) -> dict[str, Any]:
    """Load report metadata for a saved report bundle."""
    metadata_path = Path(path).with_name("metadata.json")
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def _report_markdown_relative(path: Path | str) -> str:
    return _canonical_relative(Path(path).with_name("report.md"))


def _aggregate_row(rows: list[dict[str, Any]], *, seed_label: str) -> dict[str, Any] | None:
    for row in rows:
        if row.get("row_type") == "aggregate" and str(row.get("seed")) == seed_label:
            return row
    return None


def _seed_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("row_type") == "seed"]


def _metric_block(
    mean_row: dict[str, Any] | None,
    std_row: dict[str, Any] | None,
    *,
    delta_mode: bool,
) -> dict[str, dict[str, float | None]]:
    mean_key_map = _DELTA_METRIC_KEYS if delta_mode else {key: key for key in _DELTA_METRIC_KEYS}
    mean_metrics: dict[str, float | None] = {}
    std_metrics: dict[str, float | None] = {}
    for public_key, source_key in mean_key_map.items():
        mean_value = None if mean_row is None else mean_row.get(source_key)
        std_value = None if std_row is None else std_row.get(source_key)
        mean_metrics[public_key] = None if mean_value is None else float(mean_value)
        std_metrics[public_key] = None if std_value is None else float(std_value)
    return {"mean": mean_metrics, "std": std_metrics}


def _verdict_counts_from_rows(rows: list[dict[str, Any]]) -> dict[str, int]:
    verdict_counts = {"win": 0, "tradeoff": 0, "failure": 0}
    for row in _seed_rows(rows):
        verdict = str(row.get("verdict", ""))
        if verdict in verdict_counts:
            verdict_counts[verdict] += 1
    return verdict_counts


def build_seeded_baseline_summary(
    *,
    stability_report_data: dict[str, Any],
    stability_summary: dict[str, Any],
) -> dict[str, Any]:
    """Summarize the official DistilBERT baseline cohort for final robustness comparison."""
    rows = [
        row
        for row in stability_report_data.get("baseline_stability_table", [])
        if row.get("cohort") == "distilbert_baseline"
    ]
    mean_row = _aggregate_row(rows, seed_label="mean")
    std_row = _aggregate_row(rows, seed_label="std")
    seed_rows = _seed_rows(rows)
    cohort_summary = stability_summary.get("cohort_summaries", {}).get("distilbert_baseline", {})
    return {
        "method_name": "distilbert_baseline",
        "display_name": "DistilBERT Baseline",
        "is_exploratory": False,
        "evidence_scope": "official_seeded",
        "comparison_mode": "baseline_metric",
        "seed_count": len(seed_rows),
        "stability_label": cohort_summary.get("label"),
        "seeded_interpretation": None,
        "verdict_counts": None,
        "primary_verdict": cohort_summary.get("label"),
        "metrics": _metric_block(mean_row, std_row, delta_mode=False),
        "story_note": "Stable reference baseline showing the benchmark robustness gap under shift.",
    }


def build_official_mitigation_summary(
    *,
    method_name: str,
    display_name: str,
    seeded_report_data: dict[str, Any],
    stability_report_data: dict[str, Any],
    stability_summary: dict[str, Any],
) -> dict[str, Any]:
    """Summarize one official mitigation lane from seeded saved artifacts."""
    stability_table_key = f"{method_name}_deltas"
    delta_rows = [
        row
        for row in stability_report_data.get(stability_table_key, [])
        if row.get("mitigation_method") == method_name
    ]
    mean_row = _aggregate_row(delta_rows, seed_label="mean")
    std_row = _aggregate_row(delta_rows, seed_label="std")
    seed_rows = _seed_rows(delta_rows)
    seeded_summary = seeded_report_data.get("report_summary", {})
    cohort_summary = stability_summary.get("cohort_summaries", {}).get(method_name, {})
    story_note = (
        "Stable calibration reference lane with no meaningful robustness upside."
        if method_name == "temperature_scaling"
        else "Best current robustness lane, but the official seeded story remains mixed."
    )
    return {
        "method_name": method_name,
        "display_name": display_name,
        "is_exploratory": False,
        "evidence_scope": "official_seeded",
        "comparison_mode": "delta_vs_baseline",
        "seed_count": len(seed_rows),
        "stability_label": cohort_summary.get("label"),
        "seeded_interpretation": seeded_summary.get("seeded_interpretation"),
        "verdict_counts": seeded_summary.get("mitigation_verdict_counts")
        or _verdict_counts_from_rows(delta_rows),
        "primary_verdict": cohort_summary.get("label")
        or seeded_summary.get("seeded_interpretation"),
        "metrics": _metric_block(mean_row, std_row, delta_mode=True),
        "story_note": story_note,
    }


def build_exploratory_mitigation_summary(
    *,
    method_name: str,
    display_name: str,
    scout_report_data: dict[str, Any],
    promotion_decision: str | None = None,
) -> dict[str, Any]:
    """Summarize one exploratory scout mitigation lane."""
    delta_rows = [
        row
        for row in scout_report_data.get("mitigation_comparison_table", [])
        if row.get("mitigation_method") == method_name
    ]
    seed_rows = _seed_rows(delta_rows)
    scout_row = seed_rows[0] if seed_rows else (delta_rows[0] if delta_rows else {})
    mean_metrics: dict[str, float | None] = {}
    for public_key, source_key in _DELTA_METRIC_KEYS.items():
        value = scout_row.get(source_key)
        mean_metrics[public_key] = None if value is None else float(value)
    verdict = scout_row.get("verdict")
    story_note = (
        "Scout failure against the parent baseline; not worth promotion."
        if method_name == "group_dro"
        else (
            "Worst-group improved on the scout, but OOD, ID, and calibration "
            "regressed enough to stop."
        )
    )
    return {
        "method_name": method_name,
        "display_name": display_name,
        "is_exploratory": True,
        "evidence_scope": "exploratory_scout",
        "comparison_mode": "delta_vs_baseline",
        "seed_count": 1 if scout_row else 0,
        "stability_label": None,
        "seeded_interpretation": scout_report_data.get("report_summary", {}).get(
            "seeded_interpretation"
        ),
        "verdict_counts": _verdict_counts_from_rows(delta_rows),
        "primary_verdict": verdict,
        "promotion_decision": promotion_decision,
        "metrics": {"mean": mean_metrics, "std": {key: None for key in mean_metrics}},
        "story_note": story_note,
    }


def build_promotion_audit(
    *,
    candidate_summary: dict[str, Any],
    reference_summary: dict[str, Any],
    stability_summary: dict[str, Any],
    audit_name: str,
) -> dict[str, Any]:
    """Build the structured promotion-audit decision for the final scout candidate."""
    candidate_metrics = candidate_summary.get("metrics", {}).get("mean", {})
    decision = "do_not_promote"
    decision_reason = (
        "Worst-group F1 improved on the scout, but ID Macro F1, OOD Macro F1, ECE, and "
        "Brier all regressed materially, so the result is less reliable and less interpretable "
        "than the existing reweighting lane."
    )
    milestone_assessment = stability_summary.get("milestone_assessment", {})
    return {
        "audit_name": audit_name,
        "candidate_method": candidate_summary.get("method_name"),
        "candidate_display_name": candidate_summary.get("display_name"),
        "reference_method": reference_summary.get("method_name"),
        "decision": decision,
        "decision_reason": decision_reason,
        "candidate_verdict": candidate_summary.get("primary_verdict"),
        "candidate_metrics": candidate_metrics,
        "reference_stability_label": reference_summary.get("stability_label"),
        "dataset_expansion_recommendation": milestone_assessment.get(
            "dataset_expansion_recommendation"
        ),
    }


def render_promotion_audit_markdown(
    *,
    promotion_audit: dict[str, Any],
    reference_reports: dict[str, str],
) -> str:
    """Render the standalone promotion audit markdown artifact."""
    candidate_metrics = promotion_audit.get("candidate_metrics", {})
    sections = [
        f"# {promotion_audit.get('audit_name', 'robustness_promotion_audit')}",
        "## Verdict",
        f"- Candidate: `{promotion_audit.get('candidate_method', 'unknown')}`",
        f"- Decision: `{promotion_audit.get('decision', 'n/a')}`",
        f"- Reason: {promotion_audit.get('decision_reason', 'No audit reason available.')}",
        "## Scout metrics",
        f"- Worst-group F1 delta: `{candidate_metrics.get('worst_group_f1', 'n/a')}`",
        f"- OOD Macro F1 delta: `{candidate_metrics.get('ood_macro_f1', 'n/a')}`",
        f"- ID Macro F1 delta: `{candidate_metrics.get('id_macro_f1', 'n/a')}`",
        f"- ECE delta: `{candidate_metrics.get('ece', 'n/a')}`",
        f"- Brier delta: `{candidate_metrics.get('brier_score', 'n/a')}`",
        "## Context",
        (
            f"- Existing robustness reference: `{promotion_audit.get('reference_method', 'n/a')}` "
            f"with official label `{promotion_audit.get('reference_stability_label', 'n/a')}`"
        ),
        (
            "- Dataset expansion recommendation remains "
            f"`{promotion_audit.get('dataset_expansion_recommendation', 'n/a')}`"
        ),
        "## Referenced reports",
        "\n".join(f"- `{name}`: `{path}`" for name, path in reference_reports.items()),
    ]
    return "\n\n".join(section for section in sections if section.strip()) + "\n"


def build_robustness_reference_reports(
    *,
    temperature_report_data_path: Path | str,
    reweighting_report_data_path: Path | str,
    stability_report_data_path: Path | str,
    group_dro_report_data_path: Path | str,
    group_balanced_report_data_path: Path | str,
) -> dict[str, str]:
    """Return the canonical saved-report references for the final robustness package."""
    return {
        "temperature_scaling_seeded": _report_markdown_relative(temperature_report_data_path),
        "reweighting_seeded": _report_markdown_relative(reweighting_report_data_path),
        "phase20_stability": _report_markdown_relative(stability_report_data_path),
        "group_dro_scout": _report_markdown_relative(group_dro_report_data_path),
        "group_balanced_sampling_scout": _report_markdown_relative(group_balanced_report_data_path),
    }


def build_robustness_story(
    *,
    baseline_summary: dict[str, Any],
    official_method_summaries: list[dict[str, Any]],
    exploratory_method_summaries: list[dict[str, Any]],
    promotion_audit: dict[str, Any],
    stability_summary: dict[str, Any],
) -> list[str]:
    """Build the ordered headline findings for the final robustness package."""
    del baseline_summary, exploratory_method_summaries, promotion_audit
    dataset_expansion = (
        stability_summary.get("milestone_assessment", {}).get(
            "dataset_expansion_recommendation",
            "defer",
        )
    )
    reweighting_summary = next(
        summary for summary in official_method_summaries if summary["method_name"] == "reweighting"
    )
    return [
        (
            "The DistilBERT baseline remains a stable reference lane, confirming that the "
            "robustness gap under shift is not a one-seed artifact."
        ),
        (
            "Temperature scaling remains the stable calibration reference lane across the "
            "official seeded cohort."
        ),
        (
            "Reweighting is still the best current robustness-oriented lane, but its official "
            f"label remains `{reweighting_summary.get('stability_label', 'mixed')}` "
            "rather than a clean win."
        ),
        (
            "Group DRO stayed exploratory after a scout failure, and group-balanced sampling "
            "was not promoted after trading worst-group gains for worse ID/OOD and calibration."
        ),
        (
            "The final robustness conclusion therefore remains `still_mixed`, and dataset "
            f"expansion stays `{dataset_expansion}`."
        ),
    ]


def build_final_robustness_summary(
    *,
    report_title: str,
    baseline_summary: dict[str, Any],
    official_method_summaries: list[dict[str, Any]],
    exploratory_method_summaries: list[dict[str, Any]],
    promotion_audit: dict[str, Any],
    reference_reports: dict[str, str],
    stability_summary: dict[str, Any],
) -> dict[str, Any]:
    """Build the final scout-stop robustness verdict summary."""
    reweighting_summary = next(
        summary for summary in official_method_summaries if summary["method_name"] == "reweighting"
    )
    stability_label = str(reweighting_summary.get("stability_label") or "unresolved")
    if stability_label == "stable":
        final_verdict = "stronger"
    elif stability_label == "mixed":
        final_verdict = "still_mixed"
    else:
        final_verdict = "unresolved"
    milestone_assessment = stability_summary.get("milestone_assessment", {})
    headline_findings = build_robustness_story(
        baseline_summary=baseline_summary,
        official_method_summaries=official_method_summaries,
        exploratory_method_summaries=exploratory_method_summaries,
        promotion_audit=promotion_audit,
        stability_summary=stability_summary,
    )
    return {
        "report_title": report_title,
        "final_robustness_verdict": final_verdict,
        "headline_findings": headline_findings,
        "key_takeaway": (
            "Calibration is solved more cleanly than robustness in the current benchmark: "
            "temperature scaling is stable, reweighting remains mixed, and the two final "
            "challengers did not justify promotion."
        ),
        "next_step": (
            "Carry the scout-stop verdict into the expansion gate and keep the second-dataset "
            "decision deferred unless the research milestone explicitly chooses to widen scope."
        ),
        "dataset_expansion_recommendation": milestone_assessment.get(
            "dataset_expansion_recommendation"
        ),
        "official_methods": [baseline_summary, *official_method_summaries],
        "exploratory_methods": exploratory_method_summaries,
        "promotion_audit": promotion_audit,
        "reference_reports": reference_reports,
    }


def _metric_table_row(
    summary: dict[str, Any],
    *,
    metric_key: str,
) -> dict[str, Any]:
    metrics = summary.get("metrics", {})
    mean_metrics = metrics.get("mean", {})
    std_metrics = metrics.get("std", {})
    return {
        "method_name": summary.get("method_name"),
        "display_name": summary.get("display_name"),
        "is_exploratory": bool(summary.get("is_exploratory", False)),
        "evidence_scope": summary.get("evidence_scope"),
        "comparison_mode": summary.get("comparison_mode"),
        "seed_count": summary.get("seed_count"),
        "stability_label": summary.get("stability_label"),
        "seeded_interpretation": summary.get("seeded_interpretation"),
        "primary_verdict": summary.get("primary_verdict"),
        "promotion_decision": summary.get("promotion_decision"),
        "metric_key": metric_key,
        "mean": mean_metrics.get(metric_key),
        "std": std_metrics.get(metric_key),
        "story_note": summary.get("story_note"),
    }


def build_robustness_method_tables(
    *,
    baseline_summary: dict[str, Any],
    official_method_summaries: list[dict[str, Any]],
    exploratory_method_summaries: list[dict[str, Any]],
) -> dict[str, pd.DataFrame]:
    """Build the final robustness comparison tables."""
    summary_lookup = {baseline_summary["method_name"]: baseline_summary}
    for summary in [*official_method_summaries, *exploratory_method_summaries]:
        summary_lookup[str(summary["method_name"])] = summary

    ordered_summaries = [
        summary_lookup[method_name]
        for method_name in _METHOD_ORDER
        if method_name in summary_lookup
    ]
    worst_group_rows = [
        _metric_table_row(summary, metric_key="worst_group_f1") for summary in ordered_summaries
    ]
    ood_rows = [
        _metric_table_row(summary, metric_key="ood_macro_f1") for summary in ordered_summaries
    ]
    id_rows = [
        _metric_table_row(summary, metric_key="id_macro_f1") for summary in ordered_summaries
    ]
    calibration_rows = []
    for summary in ordered_summaries:
        metrics = summary.get("metrics", {})
        calibration_rows.append(
            {
                "method_name": summary.get("method_name"),
                "display_name": summary.get("display_name"),
                "is_exploratory": bool(summary.get("is_exploratory", False)),
                "evidence_scope": summary.get("evidence_scope"),
                "comparison_mode": summary.get("comparison_mode"),
                "seed_count": summary.get("seed_count"),
                "stability_label": summary.get("stability_label"),
                "seeded_interpretation": summary.get("seeded_interpretation"),
                "primary_verdict": summary.get("primary_verdict"),
                "promotion_decision": summary.get("promotion_decision"),
                "ece_mean": metrics.get("mean", {}).get("ece"),
                "ece_std": metrics.get("std", {}).get("ece"),
                "brier_score_mean": metrics.get("mean", {}).get("brier_score"),
                "brier_score_std": metrics.get("std", {}).get("brier_score"),
                "story_note": summary.get("story_note"),
            }
        )
    return {
        "worst_group_summary": pd.DataFrame(worst_group_rows),
        "ood_summary": pd.DataFrame(ood_rows),
        "id_summary": pd.DataFrame(id_rows),
        "calibration_summary": pd.DataFrame(calibration_rows),
    }
