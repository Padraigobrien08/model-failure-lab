from __future__ import annotations

import pytest

from model_failure_lab.artifact_index import (
    assert_valid_artifact_index_payload,
    validate_artifact_index_payload,
)


def _base_payload() -> dict[str, object]:
    return {
        "schema_version": "artifact_index_v1",
        "generated_at": "2026-03-22T00:00:00Z",
        "artifact_root": "artifacts",
        "default_filters": {"official_only": True},
        "entities": {
            "runs": [
                {
                    "run_id": "parent_run",
                    "is_official": True,
                    "default_visible": True,
                    "metadata_path": "artifacts/baselines/distilbert/parent_run/metadata.json",
                    "artifact_refs": {
                        "metrics_json": {
                            "path": "artifacts/baselines/distilbert/parent_run/metrics.json",
                            "exists": True,
                        }
                    },
                },
                {
                    "run_id": "child_run",
                    "is_official": True,
                    "default_visible": True,
                    "metadata_path": (
                        "artifacts/mitigations/reweighting/distilbert/child_run/metadata.json"
                    ),
                    "artifact_refs": {
                        "metrics_json": {
                            "path": (
                                "artifacts/mitigations/reweighting/distilbert/"
                                "child_run/metrics.json"
                            ),
                            "exists": True,
                        }
                    },
                },
            ],
            "evaluations": [
                {
                    "eval_id": "parent_eval",
                    "source_run_id": "parent_run",
                    "source_parent_run_id": None,
                    "is_official": True,
                    "default_visible": True,
                    "metadata_path": (
                        "artifacts/baselines/distilbert/parent_run/evaluations/"
                        "parent_eval/metadata.json"
                    ),
                    "artifact_refs": {
                        "ui_summary_json": {
                            "path": (
                                "artifacts/baselines/distilbert/parent_run/evaluations/"
                                "parent_eval/ui_summary.json"
                            ),
                            "exists": True,
                        }
                    },
                },
                {
                    "eval_id": "child_eval",
                    "source_run_id": "child_run",
                    "source_parent_run_id": "parent_run",
                    "is_official": True,
                    "default_visible": True,
                    "metadata_path": (
                        "artifacts/mitigations/reweighting/distilbert/child_run/"
                        "evaluations/child_eval/metadata.json"
                    ),
                    "artifact_refs": {
                        "ui_summary_json": {
                            "path": (
                                "artifacts/mitigations/reweighting/distilbert/child_run/"
                                "evaluations/child_eval/ui_summary.json"
                            ),
                            "exists": True,
                        }
                    },
                },
            ],
            "reports": [
                {
                    "report_id": "phase19_report",
                    "source_eval_ids": ["parent_eval", "child_eval"],
                    "is_official": True,
                    "default_visible": True,
                    "report_scope": "phase19_reweighting_seeded",
                    "metadata_path": (
                        "artifacts/reports/comparisons/phase19_reweighting_seeded/"
                        "phase19_report/metadata.json"
                    ),
                    "artifact_refs": {
                        "report_data_json": {
                            "path": (
                                "artifacts/reports/comparisons/phase19_reweighting_seeded/"
                                "phase19_report/report_data.json"
                            ),
                            "exists": True,
                        }
                    },
                },
                {
                    "report_id": "phase20_report",
                    "source_eval_ids": ["parent_eval", "child_eval"],
                    "is_official": True,
                    "default_visible": True,
                    "report_scope": "phase20_stability",
                    "metadata_path": (
                        "artifacts/reports/comparisons/phase20_stability/"
                        "phase20_report/metadata.json"
                    ),
                    "artifact_refs": {
                        "stability_summary_json": {
                            "path": (
                                "artifacts/reports/comparisons/phase20_stability/"
                                "phase20_report/stability_summary.json"
                            ),
                            "exists": True,
                        }
                    },
                },
                {
                    "report_id": "phase26_report",
                    "source_eval_ids": ["parent_eval", "child_eval"],
                    "is_official": True,
                    "default_visible": True,
                    "report_scope": "phase26_robustness_final",
                    "metadata_path": (
                        "artifacts/reports/comparisons/phase26_robustness_final/"
                        "phase26_report/metadata.json"
                    ),
                    "artifact_refs": {
                        "report_data_json": {
                            "path": (
                                "artifacts/reports/comparisons/phase26_robustness_final/"
                                "phase26_report/report_data.json"
                            ),
                            "exists": True,
                        }
                    },
                },
            ],
        },
        "views": {
            "seeded_cohorts": [
                {
                    "cohort_id": "reweighting",
                    "evaluation_ids": ["child_eval"],
                    "is_official": True,
                    "default_visible": True,
                }
            ],
            "mitigation_comparisons": [
                {
                    "view_id": "reweighting",
                    "aggregate_report_id": "phase19_report",
                    "comparison_summary": {"seeded_interpretation": "stable"},
                    "stability_assessment": {"label": "mixed"},
                    "per_seed_comparisons": [
                        {"parent_eval_id": "parent_eval", "child_eval_id": "child_eval"}
                    ],
                }
            ],
            "stability_packages": [
                {
                    "package_id": "phase20_report",
                    "report_id": "phase20_report",
                    "milestone_assessment": {
                        "dataset_expansion_recommendation": "defer",
                    },
                    "reference_reports": {
                        "reweighting_seeded": {
                            "path": (
                                "artifacts/reports/comparisons/phase19_reweighting_seeded/"
                                "phase19_report/report.md"
                            ),
                            "exists": True,
                        }
                    },
                }
            ],
            "research_closeout": [
                {
                    "view_id": "phase27_gate",
                    "final_robustness_verdict": "still_mixed",
                    "dataset_expansion_decision": "defer_now_reopen_under_conditions",
                    "supporting_report_ids": ["phase20_report", "phase26_report"],
                    "artifact_refs": {
                        "final_gate_json": {
                            "path": "artifacts/reports/closeout/phase27_gate/final_gate.json",
                            "exists": True,
                        }
                    },
                    "metadata_path": "artifacts/reports/closeout/phase27_gate/final_gate.json",
                    "is_official": True,
                    "default_visible": True,
                }
            ],
        },
    }


def test_validate_artifact_index_payload_rejects_absolute_paths_and_unknown_refs():
    payload = _base_payload()
    payload["entities"]["runs"][0]["artifact_refs"]["metrics_json"]["path"] = (
        "/Users/example/report.json"  # type: ignore[index]
    )
    payload["entities"]["evaluations"][1]["source_run_id"] = "missing_run"  # type: ignore[index]

    errors = validate_artifact_index_payload(payload)

    assert any("absolute artifact path" in error for error in errors)
    assert any("unknown source_run_id" in error for error in errors)


def test_validate_artifact_index_payload_requires_official_report_closure_and_stability_labels():
    payload = _base_payload()
    payload["entities"]["evaluations"][1]["is_official"] = False  # type: ignore[index]
    payload["views"]["mitigation_comparisons"][0]["stability_assessment"] = {}  # type: ignore[index]

    errors = validate_artifact_index_payload(payload)

    assert any("official without official source-eval closure" in error for error in errors)
    assert any("missing stability_assessment.label" in error for error in errors)


def test_assert_valid_artifact_index_payload_raises_on_invalid_payload():
    payload = _base_payload()
    payload["default_filters"]["official_only"] = False  # type: ignore[index]

    with pytest.raises(ValueError, match="official_only"):
        assert_valid_artifact_index_payload(payload)
