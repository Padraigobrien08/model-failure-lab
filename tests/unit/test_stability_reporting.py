from __future__ import annotations

from pathlib import Path

import pandas as pd

from model_failure_lab.reporting import (
    build_baseline_stability_table,
    build_mitigation_stability_table,
    build_stability_summary,
)
from model_failure_lab.reporting.discovery import ReportCandidate


def _candidate(
    *,
    seed: int,
    model_name: str,
    source_run_id: str,
    eval_id: str,
    id_macro_f1: float,
    ood_macro_f1: float,
    robustness_gap_f1: float,
    worst_group_f1: float,
    ece: float,
    brier_score: float,
    experiment_group: str,
    tags: list[str],
    source_parent_run_id: str | None = None,
    mitigation_method: str | None = None,
) -> ReportCandidate:
    metadata = {
        "eval_id": eval_id,
        "run_id": eval_id,
        "source_run_id": source_run_id,
        "source_parent_run_id": source_parent_run_id,
        "parent_run_id": source_parent_run_id,
        "model_name": model_name,
        "dataset_name": "civilcomments",
        "experiment_group": experiment_group,
        "tags": tags,
        "random_seed": seed,
        "resolved_config": {
            "seed": seed,
            "tags": tags,
            "experiment_group": experiment_group,
            "data": {
                "dataset_name": "civilcomments",
                "label_field": "toxicity",
                "text_field": "comment_text",
                "group_fields": ["male", "female"],
            },
            "eval": {
                "primary_metric": "macro_f1",
                "tracked_metrics": ["accuracy", "macro_f1", "auroc"],
                "calibration_metric": "ece",
                "calibration_strategy": "uniform",
                "worst_group_metric": "accuracy",
                "robustness_gap_metric": "accuracy_delta",
            },
        },
        "mitigation_method": mitigation_method,
        "min_group_support": 100,
        "evaluated_splits": ["id_test", "ood_test"],
        "evaluation_schema_version": "shift_eval_v1",
    }
    if mitigation_method is not None:
        metadata["mitigation_config"] = {
            "comparison_tolerances": {
                "id_macro_f1_max_drop": 0.01,
                "overall_macro_f1_max_drop": 0.01,
                "ece_neutral_tolerance": 0.005,
            }
        }
        metadata["resolved_config"]["mitigation"] = {  # type: ignore[index]
            "method": mitigation_method,
            "comparison_tolerances": {
                "id_macro_f1_max_drop": 0.01,
                "overall_macro_f1_max_drop": 0.01,
                "ece_neutral_tolerance": 0.005,
            },
        }

    return ReportCandidate(
        eval_id=eval_id,
        metadata_path=Path(f"/tmp/{eval_id}/metadata.json"),
        metadata=metadata,
        overall_metrics={
            "id": {"macro_f1": id_macro_f1},
            "ood": {"macro_f1": ood_macro_f1},
            "overall": {"macro_f1": (id_macro_f1 + ood_macro_f1) / 2.0},
            "headline_metrics": {
                "robustness_gap_f1": robustness_gap_f1,
                "worst_group_f1": worst_group_f1,
            },
        },
        split_metrics=pd.DataFrame(),
        id_ood_comparison=pd.DataFrame(),
        subgroup_metrics=pd.DataFrame(),
        worst_group_summary={},
        calibration_summary=pd.DataFrame(
            [{"slice_name": "overall", "ece": ece, "brier_score": brier_score}]
        ),
        calibration_bins=pd.DataFrame(),
    )


def test_build_baseline_stability_table_preserves_seed_rows_and_aggregate_rows():
    logistic_candidates = [
        _candidate(
            seed=13,
            model_name="logistic_tfidf",
            source_run_id="logistic_seed_13",
            eval_id="logistic_eval_13",
            id_macro_f1=0.80,
            ood_macro_f1=0.74,
            robustness_gap_f1=0.06,
            worst_group_f1=0.31,
            ece=0.11,
            brier_score=0.16,
            experiment_group="baselines_v1_2_logistic",
            tags=["baseline", "official", "seed_13"],
        ),
        _candidate(
            seed=42,
            model_name="logistic_tfidf",
            source_run_id="logistic_seed_42",
            eval_id="logistic_eval_42",
            id_macro_f1=0.80,
            ood_macro_f1=0.74,
            robustness_gap_f1=0.06,
            worst_group_f1=0.31,
            ece=0.11,
            brier_score=0.16,
            experiment_group="baselines_v1_2_logistic",
            tags=["baseline", "official", "seed_42"],
        ),
        _candidate(
            seed=87,
            model_name="logistic_tfidf",
            source_run_id="logistic_seed_87",
            eval_id="logistic_eval_87",
            id_macro_f1=0.80,
            ood_macro_f1=0.74,
            robustness_gap_f1=0.06,
            worst_group_f1=0.31,
            ece=0.11,
            brier_score=0.16,
            experiment_group="baselines_v1_2_logistic",
            tags=["baseline", "official", "seed_87"],
        ),
    ]
    distilbert_candidates = [
        _candidate(
            seed=13,
            model_name="distilbert",
            source_run_id="distilbert_seed_13",
            eval_id="distilbert_eval_13",
            id_macro_f1=0.87,
            ood_macro_f1=0.80,
            robustness_gap_f1=0.07,
            worst_group_f1=0.32,
            ece=0.03,
            brier_score=0.05,
            experiment_group="baselines_v1_2_distilbert",
            tags=["baseline", "official", "seed_13"],
        ),
        _candidate(
            seed=42,
            model_name="distilbert",
            source_run_id="distilbert_seed_42",
            eval_id="distilbert_eval_42",
            id_macro_f1=0.869,
            ood_macro_f1=0.799,
            robustness_gap_f1=0.070,
            worst_group_f1=0.302,
            ece=0.03,
            brier_score=0.05,
            experiment_group="baselines_v1_2_distilbert",
            tags=["baseline", "official", "seed_42"],
        ),
        _candidate(
            seed=87,
            model_name="distilbert",
            source_run_id="distilbert_seed_87",
            eval_id="distilbert_eval_87",
            id_macro_f1=0.871,
            ood_macro_f1=0.801,
            robustness_gap_f1=0.069,
            worst_group_f1=0.302,
            ece=0.03,
            brier_score=0.05,
            experiment_group="baselines_v1_2_distilbert",
            tags=["baseline", "official", "seed_87"],
        ),
    ]

    table = build_baseline_stability_table(
        logistic_candidates=logistic_candidates,
        distilbert_candidates=distilbert_candidates,
    )

    assert set(table["cohort"]) == {"logistic_baseline", "distilbert_baseline"}
    assert set(table["seed"]) >= {"13", "42", "87", "mean", "std"}
    mean_row = table.loc[
        (table["cohort"] == "distilbert_baseline") & (table["seed"] == "mean")
    ].iloc[0]
    assert mean_row["row_type"] == "aggregate"
    assert float(mean_row["ood_macro_f1"]) > 0.79


def test_build_stability_summary_marks_temperature_stable_and_reweighting_mixed():
    parent_candidates = [
        _candidate(
            seed=13,
            model_name="distilbert",
            source_run_id="distilbert_seed_13",
            eval_id="parent_eval_13",
            id_macro_f1=0.87,
            ood_macro_f1=0.80,
            robustness_gap_f1=0.07,
            worst_group_f1=0.32,
            ece=0.03,
            brier_score=0.05,
            experiment_group="baselines_v1_2_distilbert",
            tags=["baseline", "official", "seed_13"],
        ),
        _candidate(
            seed=42,
            model_name="distilbert",
            source_run_id="distilbert_seed_42",
            eval_id="parent_eval_42",
            id_macro_f1=0.87,
            ood_macro_f1=0.80,
            robustness_gap_f1=0.07,
            worst_group_f1=0.31,
            ece=0.03,
            brier_score=0.05,
            experiment_group="baselines_v1_2_distilbert",
            tags=["baseline", "official", "seed_42"],
        ),
        _candidate(
            seed=87,
            model_name="distilbert",
            source_run_id="distilbert_seed_87",
            eval_id="parent_eval_87",
            id_macro_f1=0.87,
            ood_macro_f1=0.80,
            robustness_gap_f1=0.07,
            worst_group_f1=0.31,
            ece=0.03,
            brier_score=0.05,
            experiment_group="baselines_v1_2_distilbert",
            tags=["baseline", "official", "seed_87"],
        ),
    ]
    logistic_candidates = [
        _candidate(
            seed=13,
            model_name="logistic_tfidf",
            source_run_id="logistic_seed_13",
            eval_id="logistic_eval_13",
            id_macro_f1=0.80,
            ood_macro_f1=0.74,
            robustness_gap_f1=0.06,
            worst_group_f1=0.30,
            ece=0.11,
            brier_score=0.16,
            experiment_group="baselines_v1_2_logistic",
            tags=["baseline", "official", "seed_13"],
        ),
        _candidate(
            seed=42,
            model_name="logistic_tfidf",
            source_run_id="logistic_seed_42",
            eval_id="logistic_eval_42",
            id_macro_f1=0.80,
            ood_macro_f1=0.74,
            robustness_gap_f1=0.06,
            worst_group_f1=0.30,
            ece=0.11,
            brier_score=0.16,
            experiment_group="baselines_v1_2_logistic",
            tags=["baseline", "official", "seed_42"],
        ),
        _candidate(
            seed=87,
            model_name="logistic_tfidf",
            source_run_id="logistic_seed_87",
            eval_id="logistic_eval_87",
            id_macro_f1=0.80,
            ood_macro_f1=0.74,
            robustness_gap_f1=0.06,
            worst_group_f1=0.30,
            ece=0.11,
            brier_score=0.16,
            experiment_group="baselines_v1_2_logistic",
            tags=["baseline", "official", "seed_87"],
        ),
    ]
    temperature_candidates = [
        _candidate(
            seed=13,
            model_name="distilbert",
            source_run_id="temp_seed_13",
            eval_id="temp_eval_13",
            id_macro_f1=0.87,
            ood_macro_f1=0.80,
            robustness_gap_f1=0.07,
            worst_group_f1=0.32,
            ece=0.019,
            brier_score=0.048,
            experiment_group="temperature_scaling_v1_2",
            tags=["mitigation", "official", "seed_13"],
            source_parent_run_id="distilbert_seed_13",
            mitigation_method="temperature_scaling",
        ),
        _candidate(
            seed=42,
            model_name="distilbert",
            source_run_id="temp_seed_42",
            eval_id="temp_eval_42",
            id_macro_f1=0.87,
            ood_macro_f1=0.80,
            robustness_gap_f1=0.07,
            worst_group_f1=0.31,
            ece=0.018,
            brier_score=0.047,
            experiment_group="temperature_scaling_v1_2",
            tags=["mitigation", "official", "seed_42"],
            source_parent_run_id="distilbert_seed_42",
            mitigation_method="temperature_scaling",
        ),
        _candidate(
            seed=87,
            model_name="distilbert",
            source_run_id="temp_seed_87",
            eval_id="temp_eval_87",
            id_macro_f1=0.87,
            ood_macro_f1=0.80,
            robustness_gap_f1=0.07,
            worst_group_f1=0.31,
            ece=0.020,
            brier_score=0.048,
            experiment_group="temperature_scaling_v1_2",
            tags=["mitigation", "official", "seed_87"],
            source_parent_run_id="distilbert_seed_87",
            mitigation_method="temperature_scaling",
        ),
    ]
    reweighting_candidates = [
        _candidate(
            seed=13,
            model_name="distilbert",
            source_run_id="reweight_seed_13",
            eval_id="reweight_eval_13",
            id_macro_f1=0.856,
            ood_macro_f1=0.7998,
            robustness_gap_f1=0.083,
            worst_group_f1=0.382,
            ece=0.037,
            brier_score=0.058,
            experiment_group="reweighting_v1_2",
            tags=["mitigation", "official", "seed_13"],
            source_parent_run_id="distilbert_seed_13",
            mitigation_method="reweighting",
        ),
        _candidate(
            seed=42,
            model_name="distilbert",
            source_run_id="reweight_seed_42",
            eval_id="reweight_eval_42",
            id_macro_f1=0.861,
            ood_macro_f1=0.801,
            robustness_gap_f1=0.080,
            worst_group_f1=0.379,
            ece=0.034,
            brier_score=0.056,
            experiment_group="reweighting_v1_2",
            tags=["mitigation", "official", "seed_42"],
            source_parent_run_id="distilbert_seed_42",
            mitigation_method="reweighting",
        ),
        _candidate(
            seed=87,
            model_name="distilbert",
            source_run_id="reweight_seed_87",
            eval_id="reweight_eval_87",
            id_macro_f1=0.860,
            ood_macro_f1=0.7995,
            robustness_gap_f1=0.079,
            worst_group_f1=0.359,
            ece=0.036,
            brier_score=0.056,
            experiment_group="reweighting_v1_2",
            tags=["mitigation", "official", "seed_87"],
            source_parent_run_id="distilbert_seed_87",
            mitigation_method="reweighting",
        ),
    ]

    baseline_table = build_baseline_stability_table(
        logistic_candidates=logistic_candidates,
        distilbert_candidates=parent_candidates,
    )
    temp_deltas = build_mitigation_stability_table(
        parent_candidates=parent_candidates,
        mitigation_candidates=temperature_candidates,
    )
    reweight_deltas = build_mitigation_stability_table(
        parent_candidates=parent_candidates,
        mitigation_candidates=reweighting_candidates,
    )
    summary = build_stability_summary(
        report_title="phase20_stability",
        baseline_stability_table=baseline_table,
        temperature_scaling_deltas=temp_deltas,
        reweighting_deltas=reweight_deltas,
        reference_reports={
            "temperature_scaling_seeded": "phase18/report.md",
            "reweighting_seeded": "phase19/report.md",
        },
    )

    assert summary["cohort_summaries"]["distilbert_baseline"]["label"] == "stable"
    assert summary["cohort_summaries"]["temperature_scaling"]["label"] == "stable"
    assert summary["cohort_summaries"]["reweighting"]["label"] == "mixed"
    assert summary["baseline_model_comparison"]["label"] == "stable"
    assert summary["milestone_assessment"]["v1_1_findings_status"] == "stable"
    assert summary["milestone_assessment"]["dataset_expansion_recommendation"] == "defer"
