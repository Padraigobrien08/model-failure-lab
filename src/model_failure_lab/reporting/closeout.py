"""Helpers for Phase 27 expansion-gate closeout artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from model_failure_lab.tracking.manifest import utc_now_timestamp
from model_failure_lab.utils.paths import repository_root

DEFAULT_REOPEN_CONDITIONS = [
    "Robustness lane achieves stable improvement instead of remaining mixed.",
    "At least one mitigation shows consistent gains across seeds.",
    "Robustness versus calibration tradeoffs are materially reduced or better understood.",
]


def _canonical_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repository_root()))
    except ValueError:
        return path.as_posix()


def load_saved_json(path: Path | str) -> dict[str, Any]:
    """Load one saved JSON payload from disk."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_final_gate(path: Path | str, payload: dict[str, Any]) -> Path:
    """Write the final gate payload to disk."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def _normalize_conditions(conditions: Iterable[str] | None) -> list[str]:
    normalized = [str(item).strip() for item in (conditions or []) if str(item).strip()]
    return normalized or list(DEFAULT_REOPEN_CONDITIONS)


def _method_names(rows: list[dict[str, Any]] | None) -> list[str]:
    if not isinstance(rows, list):
        return []
    names = [
        str(row.get("method_name")).strip()
        for row in rows
        if isinstance(row, dict) and str(row.get("method_name", "")).strip()
    ]
    return names


def build_final_gate_payload(
    *,
    gate_name: str,
    stability_summary: dict[str, Any],
    robustness_summary: dict[str, Any],
    robustness_report_data: dict[str, Any],
    promotion_audit_path: Path,
    stability_summary_path: Path,
    robustness_summary_path: Path,
    robustness_report_data_path: Path,
    reopen_conditions: Iterable[str] | None = None,
    findings_doc_path: str = "docs/v1_4_closeout.md",
    ui_entrypoint_path: str = "scripts/run_results_ui.py",
) -> dict[str, Any]:
    """Build the machine-readable expansion-gate payload for Phase 27."""
    normalized_conditions = _normalize_conditions(reopen_conditions)
    prior_assessment = stability_summary.get("milestone_assessment", {})
    final_verdict = str(robustness_summary.get("final_robustness_verdict", "unknown"))
    promotion_audit = robustness_report_data.get("promotion_audit", {})
    official_methods = _method_names(robustness_report_data.get("official_method_summaries"))
    exploratory_methods = _method_names(
        robustness_report_data.get("exploratory_method_summaries")
    )

    recommendation_reason = (
        "Calibration is solved more cleanly than robustness: temperature scaling remains "
        "stable, reweighting remains mixed, and the exploratory challengers did not "
        "produce a clearer robustness win."
    )
    next_step = (
        "Reopen dataset expansion only after a mitigation produces stable seeded "
        "robustness gains with clearer calibration tradeoffs."
    )
    summary_bullets = [
        "The baseline robustness gap remains real and stable.",
        "Temperature scaling remains the stable calibration lane.",
        "Reweighting remains the best current robustness lane, but it is still mixed.",
        "Group DRO and group-balanced sampling remain exploratory and were not promoted.",
    ]

    return {
        "gate_id": gate_name,
        "phase_number": "27",
        "milestone": "v1.4",
        "generated_at": utc_now_timestamp(),
        "is_official": True,
        "default_visible": True,
        "final_robustness_verdict": final_verdict,
        "dataset_expansion_decision": "defer_now_reopen_under_conditions",
        "recommendation_reason": recommendation_reason,
        "previous_dataset_expansion_recommendation": prior_assessment.get(
            "dataset_expansion_recommendation"
        ),
        "reopen_conditions": normalized_conditions,
        "next_step": next_step,
        "summary_bullets": summary_bullets,
        "official_methods": official_methods,
        "exploratory_methods": exploratory_methods,
        "supporting_report_scopes": [
            "phase20_stability",
            "phase26_robustness_final",
        ],
        "supporting_report_refs": {
            "phase20_stability": _canonical_relative(stability_summary_path.with_name("report.md")),
            "phase26_robustness_final": _canonical_relative(
                robustness_report_data_path.with_name("report.md")
            ),
        },
        "supporting_artifact_refs": {
            "stability_summary_json": _canonical_relative(stability_summary_path),
            "robustness_summary_json": _canonical_relative(robustness_summary_path),
            "robustness_report_data_json": _canonical_relative(robustness_report_data_path),
            "promotion_audit_markdown": _canonical_relative(promotion_audit_path),
        },
        "promotion_audit": {
            "candidate_method": promotion_audit.get("candidate_method"),
            "decision": promotion_audit.get("decision"),
            "decision_reason": promotion_audit.get("decision_reason"),
        },
        "findings_doc_path": findings_doc_path,
        "ui_entrypoint_path": ui_entrypoint_path,
    }
