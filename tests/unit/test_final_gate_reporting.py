from __future__ import annotations

from pathlib import Path

from model_failure_lab.reporting import build_final_gate_payload


def test_build_final_gate_payload_surfaces_locked_phase27_decision(tmp_path: Path):
    promotion_audit_path = tmp_path / "promotion_audit.md"
    promotion_audit_path.write_text("# audit\n", encoding="utf-8")
    stability_summary_path = tmp_path / "stability_summary.json"
    robustness_summary_path = tmp_path / "report_summary.json"
    robustness_report_data_path = tmp_path / "report_data.json"

    payload = build_final_gate_payload(
        gate_name="phase27_gate",
        stability_summary={
            "milestone_assessment": {
                "dataset_expansion_recommendation": "defer",
            }
        },
        robustness_summary={"final_robustness_verdict": "still_mixed"},
        robustness_report_data={
            "promotion_audit": {
                "candidate_method": "group_balanced_sampling",
                "decision": "do_not_promote",
                "decision_reason": "Scout regressed too many reliability metrics.",
            },
            "official_method_summaries": [
                {"method_name": "temperature_scaling"},
                {"method_name": "reweighting"},
            ],
            "exploratory_method_summaries": [
                {"method_name": "group_dro"},
                {"method_name": "group_balanced_sampling"},
            ],
        },
        promotion_audit_path=promotion_audit_path,
        stability_summary_path=stability_summary_path,
        robustness_summary_path=robustness_summary_path,
        robustness_report_data_path=robustness_report_data_path,
    )

    assert payload["final_robustness_verdict"] == "still_mixed"
    assert payload["dataset_expansion_decision"] == "defer_now_reopen_under_conditions"
    assert len(payload["reopen_conditions"]) == 3
    assert payload["supporting_report_scopes"] == [
        "phase20_stability",
        "phase26_robustness_final",
    ]
    assert payload["findings_doc_path"] == "docs/v1_4_closeout.md"
