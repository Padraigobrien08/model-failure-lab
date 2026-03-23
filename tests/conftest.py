from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


@pytest.fixture()
def temp_artifact_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MODEL_FAILURE_LAB_ARTIFACT_ROOT", str(artifact_dir))
    return artifact_dir


@pytest.fixture()
def temp_config_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    config_dir = tmp_path / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MODEL_FAILURE_LAB_CONFIG_ROOT", str(config_dir))
    return config_dir


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


@pytest.fixture()
def results_ui_manifest(tmp_path: Path) -> Path:
    index_path = tmp_path / "artifact_index.json"
    _write_json(
        index_path,
        {
            "schema_version": "artifact_index_v1",
            "generated_at": "2026-03-23T12:00:00Z",
            "artifact_root": "artifacts",
            "default_filters": {"official_only": True},
            "entities": {
                "runs": [
                    {
                        "id": "run_official",
                        "entity_type": "run",
                        "run_id": "run_official",
                        "metadata_path": (
                            "artifacts/baselines/distilbert/run_official/metadata.json"
                        ),
                        "artifact_refs": {},
                        "default_visible": True,
                        "is_official": True,
                        "experiment_group": "baselines_v1_2_distilbert",
                        "status": "completed",
                        "seed": 13,
                    },
                    {
                        "id": "run_exploratory",
                        "entity_type": "run",
                        "run_id": "run_exploratory",
                        "metadata_path": (
                            "artifacts/baselines/distilbert/run_exploratory/metadata.json"
                        ),
                        "artifact_refs": {},
                        "default_visible": False,
                        "is_official": False,
                        "experiment_group": "exploratory",
                        "status": "completed",
                        "seed": 99,
                    },
                ],
                "evaluations": [
                    {
                        "id": "eval_official",
                        "entity_type": "evaluation",
                        "eval_id": "eval_official",
                        "metadata_path": (
                            "artifacts/baselines/distilbert/run_official/evaluations/"
                            "eval_official/metadata.json"
                        ),
                        "artifact_refs": {},
                        "payload_refs": {},
                        "default_visible": True,
                        "is_official": True,
                        "experiment_group": "baselines_v1_2_distilbert",
                        "status": "completed",
                        "seed": 13,
                    }
                ],
                "reports": [
                    {
                        "id": "phase20_report",
                        "entity_type": "report",
                        "report_id": "phase20_report",
                        "report_scope": "phase20_stability",
                        "metadata_path": (
                            "artifacts/reports/comparisons/phase20_stability/"
                            "phase20_report/metadata.json"
                        ),
                        "artifact_refs": {
                            "report_markdown": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase20_stability/"
                                    "phase20_report/report.md"
                                ),
                            }
                        },
                        "payload_refs": {},
                        "default_visible": True,
                        "is_official": True,
                        "experiment_group": "phase20_stability",
                        "status": "completed",
                    }
                ],
            },
            "views": {
                "seeded_cohorts": [
                    {
                        "cohort_id": "logistic_baseline",
                        "display_name": "Logistic TF-IDF Baseline",
                        "default_visible": True,
                        "is_official": True,
                        "cohort_type": "baseline",
                        "experiment_group": "baselines_v1_2_logistic",
                        "model_name": "logistic_tfidf",
                        "mitigation_method": None,
                        "linked_report_id": None,
                        "seed_ids": ["13", "42", "87"],
                        "run_ids": ["log_a", "log_b", "log_c"],
                        "evaluation_ids": ["log_eval_a", "log_eval_b", "log_eval_c"],
                        "aggregate_metrics": {
                            "mean": {
                                "id_macro_f1": 0.780,
                                "robustness_gap_f1": 0.054,
                                "worst_group_f1": 0.309,
                                "ece": None,
                                "brier_score": None,
                            },
                            "std": {
                                "id_macro_f1": 0.0,
                                "robustness_gap_f1": 0.0,
                                "worst_group_f1": 0.0,
                                "ece": None,
                                "brier_score": None,
                            },
                        },
                        "per_seed_metrics": [
                            {
                                "seed": "13",
                                "run_id": "log_a",
                                "eval_id": "log_eval_a",
                                "id_macro_f1": 0.780,
                                "robustness_gap_f1": 0.054,
                                "worst_group_f1": 0.309,
                                "ece": None,
                                "brier_score": None,
                            }
                        ],
                    },
                    {
                        "cohort_id": "distilbert_baseline",
                        "display_name": "DistilBERT Baseline",
                        "default_visible": True,
                        "is_official": True,
                        "cohort_type": "baseline",
                        "experiment_group": "baselines_v1_2_distilbert",
                        "model_name": "distilbert",
                        "mitigation_method": None,
                        "linked_report_id": None,
                        "seed_ids": ["13", "42", "87"],
                        "run_ids": ["dist_a", "dist_b", "dist_c"],
                        "evaluation_ids": ["dist_eval_a", "dist_eval_b", "dist_eval_c"],
                        "aggregate_metrics": {
                            "mean": {
                                "id_macro_f1": 0.842,
                                "robustness_gap_f1": 0.070,
                                "worst_group_f1": 0.306,
                                "ece": None,
                                "brier_score": None,
                            },
                            "std": {},
                        },
                        "per_seed_metrics": [
                            {
                                "seed": "13",
                                "run_id": "dist_a",
                                "eval_id": "dist_eval_a",
                                "id_macro_f1": 0.842,
                                "robustness_gap_f1": 0.070,
                                "worst_group_f1": 0.306,
                                "ece": None,
                                "brier_score": None,
                            }
                        ],
                    },
                    {
                        "cohort_id": "temperature_scaling",
                        "display_name": "Temperature Scaling",
                        "default_visible": True,
                        "is_official": True,
                        "cohort_type": "mitigation",
                        "experiment_group": "temperature_scaling_v1_2",
                        "model_name": "distilbert",
                        "mitigation_method": "temperature_scaling",
                        "linked_report_id": "phase18_report",
                        "seed_ids": ["13", "42", "87"],
                        "run_ids": ["temp_a", "temp_b", "temp_c"],
                        "evaluation_ids": ["temp_eval_a", "temp_eval_b", "temp_eval_c"],
                        "aggregate_metrics": {
                            "mean": {
                                "id_macro_f1": 0.842,
                                "robustness_gap_f1": 0.070,
                                "worst_group_f1": 0.306,
                                "ece": None,
                                "brier_score": None,
                            },
                            "std": {},
                        },
                        "per_seed_metrics": [
                            {
                                "seed": "13",
                                "run_id": "temp_a",
                                "eval_id": "temp_eval_a",
                                "id_macro_f1": 0.842,
                                "robustness_gap_f1": 0.070,
                                "worst_group_f1": 0.306,
                                "ece": None,
                                "brier_score": None,
                            }
                        ],
                    },
                    {
                        "cohort_id": "reweighting",
                        "display_name": "Reweighting",
                        "default_visible": True,
                        "is_official": True,
                        "cohort_type": "mitigation",
                        "experiment_group": "reweighting_v1_2",
                        "model_name": "distilbert",
                        "mitigation_method": "reweighting",
                        "linked_report_id": "phase19_report",
                        "seed_ids": ["13", "42", "87"],
                        "run_ids": ["rew_a", "rew_b", "rew_c"],
                        "evaluation_ids": ["rew_eval_a", "rew_eval_b", "rew_eval_c"],
                        "aggregate_metrics": {
                            "mean": {
                                "id_macro_f1": 0.836,
                                "robustness_gap_f1": 0.059,
                                "worst_group_f1": 0.366,
                                "ece": None,
                                "brier_score": None,
                            },
                            "std": {},
                        },
                        "per_seed_metrics": [
                            {
                                "seed": "13",
                                "run_id": "rew_a",
                                "eval_id": "rew_eval_a",
                                "id_macro_f1": 0.836,
                                "robustness_gap_f1": 0.059,
                                "worst_group_f1": 0.366,
                                "ece": None,
                                "brier_score": None,
                            }
                        ],
                    },
                ],
                "mitigation_comparisons": [
                    {
                        "view_id": "temperature_scaling",
                        "mitigation_method": "temperature_scaling",
                        "default_visible": True,
                        "is_official": True,
                        "aggregate_report_id": "phase18_report",
                        "aggregate_report_scope": "phase18_temperature_scaling_seeded",
                        "comparison_summary": {
                            "seeded_interpretation": "stable",
                            "verdict_counts": {"win": 3, "tradeoff": 0, "failure": 0},
                        },
                        "per_seed_comparisons": [],
                        "stability_assessment": {
                            "label": "stable",
                            "verdict_counts": {"win": 3, "tradeoff": 0, "failure": 0},
                            "mean_deltas": {"robustness_gap_delta": 0.0},
                            "std_deltas": {"robustness_gap_delta": 0.0},
                        },
                    },
                    {
                        "view_id": "reweighting",
                        "mitigation_method": "reweighting",
                        "default_visible": True,
                        "is_official": True,
                        "aggregate_report_id": "phase19_report",
                        "aggregate_report_scope": "phase19_reweighting_seeded",
                        "comparison_summary": {
                            "seeded_interpretation": "stable",
                            "verdict_counts": {"win": 2, "tradeoff": 1, "failure": 0},
                        },
                        "per_seed_comparisons": [],
                        "stability_assessment": {
                            "label": "mixed",
                            "verdict_counts": {"win": 2, "tradeoff": 1, "failure": 0},
                            "mean_deltas": {"robustness_gap_delta": -0.011},
                            "std_deltas": {"robustness_gap_delta": 0.002},
                        },
                    },
                ],
                "stability_packages": [
                    {
                        "package_id": "phase20_stability",
                        "report_id": "phase20_report",
                        "report_scope": "phase20_stability",
                        "default_visible": True,
                        "is_official": True,
                        "cohort_summaries": {
                            "logistic_baseline": {"label": "stable"},
                            "distilbert_baseline": {"label": "stable"},
                            "temperature_scaling": {"label": "stable"},
                            "reweighting": {"label": "mixed"},
                        },
                        "baseline_model_comparison": {"label": "mixed"},
                        "milestone_assessment": {
                            "dataset_expansion_recommendation": "defer",
                            "recommendation_reason": (
                                "Hold dataset expansion until the robustness "
                                "lane is clearer."
                            ),
                            "next_step": (
                                "Consolidate the robustness mitigation story "
                                "before expanding benchmark scope."
                            ),
                            "v1_1_findings_status": "stable",
                        },
                        "reference_reports": {},
                    }
                ],
            },
        },
    )
    return index_path
