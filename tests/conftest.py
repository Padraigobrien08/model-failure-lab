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
                        "id": "log_eval_a",
                        "entity_type": "evaluation",
                        "eval_id": "log_eval_a",
                        "metadata_path": (
                            "artifacts/baselines/logistic_tfidf/log_a/evaluations/"
                            "log_eval_a/metadata.json"
                        ),
                        "artifact_refs": {
                            "split_metrics_csv": {
                                "exists": True,
                                "path": (
                                    "artifacts/baselines/logistic_tfidf/log_a/evaluations/"
                                    "log_eval_a/split_metrics.csv"
                                ),
                            }
                        },
                        "payload_refs": {},
                        "default_visible": True,
                        "is_official": True,
                        "experiment_group": "baselines_v1_2_logistic",
                        "status": "completed",
                        "seed": 13,
                    },
                    {
                        "id": "dist_eval_a",
                        "entity_type": "evaluation",
                        "eval_id": "dist_eval_a",
                        "metadata_path": (
                            "artifacts/baselines/distilbert/dist_a/evaluations/"
                            "dist_eval_a/metadata.json"
                        ),
                        "artifact_refs": {
                            "split_metrics_csv": {
                                "exists": True,
                                "path": (
                                    "artifacts/baselines/distilbert/dist_a/evaluations/"
                                    "dist_eval_a/split_metrics.csv"
                                ),
                            }
                        },
                        "payload_refs": {},
                        "default_visible": True,
                        "is_official": True,
                        "experiment_group": "baselines_v1_2_distilbert",
                        "status": "completed",
                        "seed": 13,
                    },
                    {
                        "id": "temp_eval_a",
                        "entity_type": "evaluation",
                        "eval_id": "temp_eval_a",
                        "metadata_path": (
                            "artifacts/mitigations/temperature_scaling/distilbert/temp_a/"
                            "evaluations/temp_eval_a/metadata.json"
                        ),
                        "artifact_refs": {
                            "split_metrics_csv": {
                                "exists": True,
                                "path": (
                                    "artifacts/mitigations/temperature_scaling/distilbert/temp_a/"
                                    "evaluations/temp_eval_a/split_metrics.csv"
                                ),
                            }
                        },
                        "payload_refs": {},
                        "default_visible": True,
                        "is_official": True,
                        "experiment_group": "temperature_scaling_v1_2",
                        "status": "completed",
                        "seed": 13,
                    },
                    {
                        "id": "rew_eval_a",
                        "entity_type": "evaluation",
                        "eval_id": "rew_eval_a",
                        "metadata_path": (
                            "artifacts/mitigations/reweighting/distilbert/rew_a/"
                            "evaluations/rew_eval_a/metadata.json"
                        ),
                        "artifact_refs": {
                            "split_metrics_csv": {
                                "exists": True,
                                "path": (
                                    "artifacts/mitigations/reweighting/distilbert/rew_a/"
                                    "evaluations/rew_eval_a/split_metrics.csv"
                                ),
                            }
                        },
                        "payload_refs": {},
                        "default_visible": True,
                        "is_official": True,
                        "experiment_group": "reweighting_v1_2",
                        "status": "completed",
                        "seed": 13,
                    },
                    {
                        "id": "group_dro_eval_a",
                        "entity_type": "evaluation",
                        "eval_id": "group_dro_eval_a",
                        "metadata_path": (
                            "artifacts/mitigations/group_dro/distilbert/gdro_a/"
                            "evaluations/group_dro_eval_a/metadata.json"
                        ),
                        "artifact_refs": {
                            "split_metrics_csv": {
                                "exists": True,
                                "path": (
                                    "artifacts/mitigations/group_dro/distilbert/gdro_a/"
                                    "evaluations/group_dro_eval_a/split_metrics.csv"
                                ),
                            }
                        },
                        "payload_refs": {},
                        "default_visible": False,
                        "is_official": False,
                        "experiment_group": "group_dro_v1_3",
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
                            "baseline_stability_csv": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase20_stability/"
                                    "phase20_report/tables/baseline_stability.csv"
                                ),
                            },
                            "report_markdown": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase20_stability/"
                                    "phase20_report/report.md"
                                ),
                            },
                            "reweighting_deltas_csv": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase20_stability/"
                                    "phase20_report/tables/reweighting_deltas.csv"
                                ),
                            },
                            "temperature_scaling_deltas_csv": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase20_stability/"
                                    "phase20_report/tables/temperature_scaling_deltas.csv"
                                ),
                            },
                        },
                        "payload_refs": {
                            "stability_summary_json": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase20_stability/"
                                    "phase20_report/stability_summary.json"
                                ),
                            }
                        },
                        "default_visible": True,
                        "is_official": True,
                        "experiment_group": "phase20_stability",
                        "status": "completed",
                    },
                    {
                        "id": "phase18_report",
                        "entity_type": "report",
                        "report_id": "phase18_report",
                        "report_scope": "phase18_temperature_scaling_seeded",
                        "metadata_path": (
                            "artifacts/reports/comparisons/phase18_temperature_scaling_seeded/"
                            "phase18_report/metadata.json"
                        ),
                        "artifact_refs": {
                            "mitigation_comparison_table_csv": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase18_temperature_scaling_seeded/"
                                    "phase18_report/tables/mitigation_comparison_table.csv"
                                ),
                            },
                            "report_markdown": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase18_temperature_scaling_seeded/"
                                    "phase18_report/report.md"
                                ),
                            },
                        },
                        "payload_refs": {},
                        "default_visible": True,
                        "is_official": True,
                        "experiment_group": "phase18_temperature_scaling_seeded",
                        "status": "completed",
                    },
                    {
                        "id": "phase19_report",
                        "entity_type": "report",
                        "report_id": "phase19_report",
                        "report_scope": "phase19_reweighting_seeded",
                        "metadata_path": (
                            "artifacts/reports/comparisons/phase19_reweighting_seeded/"
                            "phase19_report/metadata.json"
                        ),
                        "artifact_refs": {
                            "mitigation_comparison_table_csv": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase19_reweighting_seeded/"
                                    "phase19_report/tables/mitigation_comparison_table.csv"
                                ),
                            },
                            "report_markdown": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase19_reweighting_seeded/"
                                    "phase19_report/report.md"
                                ),
                            },
                        },
                        "payload_refs": {},
                        "default_visible": True,
                        "is_official": True,
                        "experiment_group": "phase19_reweighting_seeded",
                        "status": "completed",
                    },
                    {
                        "id": "phase26_report",
                        "entity_type": "report",
                        "report_id": "phase26_report",
                        "report_scope": "phase26_robustness_final",
                        "metadata_path": (
                            "artifacts/reports/comparisons/phase26_robustness_final/"
                            "phase26_report/metadata.json"
                        ),
                        "artifact_refs": {
                            "report_markdown": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase26_robustness_final/"
                                    "phase26_report/report.md"
                                ),
                            },
                            "worst_group_summary_csv": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase26_robustness_final/"
                                    "phase26_report/tables/worst_group_summary.csv"
                                ),
                            },
                            "report_data_json": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase26_robustness_final/"
                                    "phase26_report/report_data.json"
                                ),
                            },
                        },
                        "payload_refs": {
                            "report_summary_json": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase26_robustness_final/"
                                    "phase26_report/report_summary.json"
                                ),
                            }
                        },
                        "default_visible": True,
                        "is_official": True,
                        "experiment_group": "phase26_robustness_final",
                        "status": "completed",
                    },
                    {
                        "id": "phase18_seed13_report",
                        "entity_type": "report",
                        "report_id": "phase18_seed13_report",
                        "report_scope": "phase18_temperature_scaling_seed_13",
                        "metadata_path": (
                            "artifacts/reports/comparisons/phase18_temperature_scaling_seed_13/"
                            "phase18_seed13_report/metadata.json"
                        ),
                        "artifact_refs": {
                            "report_markdown": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase18_temperature_scaling_seed_13/"
                                    "phase18_seed13_report/report.md"
                                ),
                            }
                        },
                        "payload_refs": {},
                        "default_visible": True,
                        "is_official": True,
                        "experiment_group": "phase18_temperature_scaling_seed_13",
                        "status": "completed",
                    },
                    {
                        "id": "phase19_seed13_report",
                        "entity_type": "report",
                        "report_id": "phase19_seed13_report",
                        "report_scope": "phase19_reweighting_seed_13",
                        "metadata_path": (
                            "artifacts/reports/comparisons/phase19_reweighting_seed_13/"
                            "phase19_seed13_report/metadata.json"
                        ),
                        "artifact_refs": {
                            "report_markdown": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase19_reweighting_seed_13/"
                                    "phase19_seed13_report/report.md"
                                ),
                            }
                        },
                        "payload_refs": {},
                        "default_visible": True,
                        "is_official": True,
                        "experiment_group": "phase19_reweighting_seed_13",
                        "status": "completed",
                    },
                    {
                        "id": "phase23_scout_report",
                        "entity_type": "report",
                        "report_id": "phase23_scout_report",
                        "report_scope": "phase23_group_dro_scout_seed_13",
                        "metadata_path": (
                            "artifacts/reports/comparisons/phase23_group_dro_scout_seed_13/"
                            "phase23_scout_report/metadata.json"
                        ),
                        "artifact_refs": {
                            "report_markdown": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase23_group_dro_scout_seed_13/"
                                    "phase23_scout_report/report.md"
                                ),
                            }
                        },
                        "payload_refs": {},
                        "default_visible": False,
                        "is_official": False,
                        "experiment_group": "phase23_group_dro_scout_seed_13",
                        "status": "completed",
                    },
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
                        "per_seed_comparisons": [
                            {
                                "seed": "13",
                                "parent_run_id": "dist_a",
                                "parent_eval_id": "dist_eval_a",
                                "child_run_id": "temp_a",
                                "child_eval_id": "temp_eval_a",
                                "related_report_ids": ["phase18_seed13_report"],
                                "verdict": "win",
                                "deltas": {
                                    "id_macro_f1_delta": 0.0,
                                    "ood_macro_f1_delta": 0.0,
                                    "robustness_gap_delta": 0.0,
                                    "worst_group_f1_delta": 0.0,
                                    "ece_delta": -0.011,
                                    "brier_score_delta": -0.001,
                                },
                            }
                        ],
                        "stability_assessment": {
                            "label": "stable",
                            "verdict_counts": {"win": 3, "tradeoff": 0, "failure": 0},
                            "mean_deltas": {
                                "id_macro_f1_delta": 0.0,
                                "robustness_gap_delta": 0.0,
                                "worst_group_f1_delta": 0.0,
                            },
                            "std_deltas": {
                                "id_macro_f1_delta": 0.0,
                                "robustness_gap_delta": 0.0,
                                "worst_group_f1_delta": 0.0,
                            },
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
                        "per_seed_comparisons": [
                            {
                                "seed": "13",
                                "parent_run_id": "dist_a",
                                "parent_eval_id": "dist_eval_a",
                                "child_run_id": "rew_a",
                                "child_eval_id": "rew_eval_a",
                                "related_report_ids": ["phase19_seed13_report"],
                                "verdict": "tradeoff",
                                "deltas": {
                                    "id_macro_f1_delta": -0.010,
                                    "ood_macro_f1_delta": 0.000,
                                    "robustness_gap_delta": -0.011,
                                    "worst_group_f1_delta": 0.060,
                                    "ece_delta": 0.006,
                                    "brier_score_delta": 0.007,
                                },
                            }
                        ],
                        "stability_assessment": {
                            "label": "mixed",
                            "verdict_counts": {"win": 2, "tradeoff": 1, "failure": 0},
                            "mean_deltas": {
                                "id_macro_f1_delta": -0.010,
                                "robustness_gap_delta": -0.011,
                                "worst_group_f1_delta": 0.060,
                            },
                            "std_deltas": {
                                "id_macro_f1_delta": 0.002,
                                "robustness_gap_delta": 0.002,
                                "worst_group_f1_delta": 0.008,
                            },
                        },
                    },
                    {
                        "view_id": "group_dro",
                        "mitigation_method": "group_dro",
                        "default_visible": False,
                        "is_official": False,
                        "aggregate_report_id": "phase23_scout_report",
                        "aggregate_report_scope": "phase23_group_dro_scout_seed_13",
                        "comparison_summary": {
                            "seeded_interpretation": "failure",
                            "verdict_counts": {"win": 0, "tradeoff": 0, "failure": 1},
                        },
                        "per_seed_comparisons": [
                            {
                                "seed": "13",
                                "parent_run_id": "dist_a",
                                "parent_eval_id": "dist_eval_a",
                                "child_run_id": "gdro_a",
                                "child_eval_id": "group_dro_eval_a",
                                "related_report_ids": ["phase23_scout_report"],
                                "verdict": "failure",
                                "deltas": {
                                    "id_macro_f1_delta": -0.020,
                                    "ood_macro_f1_delta": -0.037,
                                    "robustness_gap_delta": 0.017,
                                    "worst_group_f1_delta": -0.215,
                                    "ece_delta": 0.033,
                                    "brier_score_delta": 0.010,
                                },
                            }
                        ],
                        "stability_assessment": {
                            "label": "failure",
                            "verdict_counts": {"win": 0, "tradeoff": 0, "failure": 1},
                            "mean_deltas": {
                                "id_macro_f1_delta": -0.020,
                                "robustness_gap_delta": 0.017,
                                "worst_group_f1_delta": -0.215,
                            },
                            "std_deltas": {
                                "id_macro_f1_delta": 0.0,
                                "robustness_gap_delta": 0.0,
                                "worst_group_f1_delta": 0.0,
                            },
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
                        "reference_reports": {
                            "temperature_scaling_seeded": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase18_temperature_scaling_seeded/"
                                    "phase18_report/report.md"
                                ),
                            },
                            "reweighting_seeded": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/comparisons/phase19_reweighting_seeded/"
                                    "phase19_report/report.md"
                                ),
                            },
                        },
                    }
                ],
                "research_closeout": [
                    {
                        "view_id": "phase27_gate",
                        "final_robustness_verdict": "still_mixed",
                        "dataset_expansion_decision": "defer_now_reopen_under_conditions",
                        "recommendation_reason": (
                            "Calibration is solved more cleanly than robustness: "
                            "temperature scaling remains stable, reweighting remains mixed, "
                            "and the exploratory challengers did not produce a clearer "
                            "robustness win."
                        ),
                        "reopen_conditions": [
                            "Robustness lane achieves stable improvement instead of remaining mixed.",
                            "At least one mitigation shows consistent gains across seeds.",
                            "Robustness versus calibration tradeoffs are materially reduced or better understood.",
                        ],
                        "summary_bullets": [
                            "The baseline robustness gap remains real and stable.",
                            "Temperature scaling remains the stable calibration lane.",
                        ],
                        "supporting_report_scopes": [
                            "phase20_stability",
                            "phase26_robustness_final",
                        ],
                        "supporting_report_ids": ["phase20_report", "phase26_report"],
                        "artifact_refs": {
                            "final_gate_json": {
                                "exists": True,
                                "path": "artifacts/reports/closeout/phase27_gate/final_gate.json",
                            },
                            "promotion_audit_markdown": {
                                "exists": True,
                                "path": (
                                    "artifacts/reports/robustness_promotion_audit/"
                                    "phase25_group_balanced_sampling.md"
                                ),
                            },
                        },
                        "promotion_audit": {
                            "candidate_method": "group_balanced_sampling",
                            "decision": "do_not_promote",
                        },
                        "official_methods": ["temperature_scaling", "reweighting"],
                        "exploratory_methods": ["group_dro", "group_balanced_sampling"],
                        "findings_doc_path": "docs/v1_4_closeout.md",
                        "ui_entrypoint_path": "scripts/run_results_ui.py",
                        "metadata_path": "artifacts/reports/closeout/phase27_gate/final_gate.json",
                        "default_visible": True,
                        "is_official": True,
                    }
                ],
            },
        },
    )
    return index_path
