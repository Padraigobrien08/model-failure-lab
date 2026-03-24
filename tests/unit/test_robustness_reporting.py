from __future__ import annotations

from model_failure_lab.reporting.robustness import (
    build_final_robustness_summary,
    build_promotion_audit,
)


def test_build_promotion_audit_marks_tradeoff_candidate_do_not_promote():
    audit = build_promotion_audit(
        candidate_summary={
            "method_name": "group_balanced_sampling",
            "display_name": "Group-Balanced Sampling",
            "primary_verdict": "tradeoff",
            "metrics": {
                "mean": {
                    "worst_group_f1": 0.153,
                    "ood_macro_f1": -0.096,
                    "id_macro_f1": -0.118,
                    "ece": 0.116,
                    "brier_score": 0.092,
                }
            },
        },
        reference_summary={
            "method_name": "reweighting",
            "stability_label": "mixed",
        },
        stability_summary={
            "milestone_assessment": {
                "dataset_expansion_recommendation": "defer",
            }
        },
        audit_name="phase25_group_balanced_sampling",
    )

    assert audit["decision"] == "do_not_promote"
    assert audit["reference_stability_label"] == "mixed"
    assert "OOD Macro F1" in audit["decision_reason"]


def test_build_final_robustness_summary_keeps_mixed_reweighting_story():
    summary = build_final_robustness_summary(
        report_title="phase26_robustness_final",
        baseline_summary={"method_name": "distilbert_baseline"},
        official_method_summaries=[
            {"method_name": "temperature_scaling", "stability_label": "stable"},
            {"method_name": "reweighting", "stability_label": "mixed"},
        ],
        exploratory_method_summaries=[
            {"method_name": "group_dro"},
            {"method_name": "group_balanced_sampling"},
        ],
        promotion_audit={"decision": "do_not_promote"},
        reference_reports={"phase20_stability": "artifacts/reports/comparisons/phase20/report.md"},
        stability_summary={
            "milestone_assessment": {
                "dataset_expansion_recommendation": "defer",
            }
        },
    )

    assert summary["final_robustness_verdict"] == "still_mixed"
    assert summary["dataset_expansion_recommendation"] == "defer"
    assert any(
        "Temperature scaling remains the stable calibration" in item
        for item in summary["headline_findings"]
    )
