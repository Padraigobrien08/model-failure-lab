from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from model_failure_lab.reporting import (
    build_mitigation_comparison_table,
    classify_mitigation_verdict,
    load_report_inputs,
    pair_mitigation_candidates_with_parents,
    select_report_candidates,
)
from model_failure_lab.utils.paths import (
    build_baseline_run_dir,
    build_evaluation_run_dir,
    build_mitigation_run_dir,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def _create_evaluation_bundle(
    *,
    model_name: str,
    source_run_id: str,
    eval_id: str,
    experiment_group: str,
    root_kind: str = "baseline",
    mitigation_method: str | None = None,
    source_parent_run_id: str | None = None,
    id_score: float = 0.8,
    ood_score: float = 0.62,
    overall_score: float = 0.68,
    worst_group_score: float = 0.44,
    ece: float = 0.07,
    brier_score: float = 0.12,
) -> None:
    if root_kind == "mitigation":
        source_run_dir = build_mitigation_run_dir(
            mitigation_method or "reweighting",
            model_name,
            source_run_id,
            create=True,
        )
    else:
        source_run_dir = build_baseline_run_dir(model_name, source_run_id, create=True)

    eval_dir = build_evaluation_run_dir(source_run_dir, eval_id, create=True)
    figures_dir = eval_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    artifact_paths = {
        "overall_metrics_json": str(eval_dir / "overall_metrics.json"),
        "split_metrics_csv": str(eval_dir / "split_metrics.csv"),
        "id_ood_comparison_csv": str(eval_dir / "id_ood_comparison.csv"),
        "subgroup_metrics_csv": str(eval_dir / "subgroup_metrics.csv"),
        "worst_group_summary_json": str(eval_dir / "worst_group_summary.json"),
        "subgroup_support_report_csv": str(eval_dir / "subgroup_support_report.csv"),
        "calibration_summary_csv": str(eval_dir / "calibration_summary.csv"),
        "calibration_bins_csv": str(eval_dir / "calibration_bins.csv"),
        "confidence_summary_json": str(eval_dir / "confidence_summary.json"),
        "diagnostics_json": str(eval_dir / "diagnostics.json"),
        "plots": str(figures_dir),
    }
    metadata_payload: dict[str, object] = {
        "run_id": eval_id,
        "eval_id": eval_id,
        "source_run_id": source_run_id,
        "experiment_type": "shift_eval",
        "model_name": model_name,
        "dataset_name": "civilcomments",
        "resolved_config": {
            "experiment_group": experiment_group,
            "data": {
                "dataset_name": "civilcomments",
                "label_field": "toxicity",
                "text_field": "comment_text",
                "group_fields": ["male", "female"],
            },
        },
        "artifact_paths": artifact_paths,
        "evaluator_version": "eval-schema-v1",
        "git_commit_hash": "eval-schema-v1",
        "min_group_support": 100,
        "tags": [experiment_group],
    }
    if source_parent_run_id is not None:
        metadata_payload["source_parent_run_id"] = source_parent_run_id
        metadata_payload["mitigation_method"] = mitigation_method
        metadata_payload["resolved_config"] = {
            **dict(metadata_payload["resolved_config"]),
            "mitigation": {
                "method": mitigation_method,
                "comparison_tolerances": {
                    "id_macro_f1_max_drop": 0.01,
                    "overall_macro_f1_max_drop": 0.01,
                    "ece_neutral_tolerance": 0.005,
                },
            },
        }
    _write_json(eval_dir / "metadata.json", metadata_payload)
    _write_json(
        Path(artifact_paths["overall_metrics_json"]),
        {
            "headline_metrics": {
                "accuracy": overall_score,
                "macro_f1": overall_score,
                "auroc": overall_score + 0.1,
                "worst_group_f1": worst_group_score,
                "robustness_gap_f1": round(id_score - ood_score, 3),
            },
            "overall": {"macro_f1": overall_score},
            "id": {"macro_f1": id_score},
            "ood": {"macro_f1": ood_score},
        },
    )
    _write_json(
        Path(artifact_paths["worst_group_summary_json"]),
        {"worst_group_f1": {"group_id": "group_low", "value": worst_group_score}},
    )
    _write_json(Path(artifact_paths["confidence_summary_json"]), {"overall": {}})
    _write_json(Path(artifact_paths["diagnostics_json"]), {"score_distribution": {}})
    _write_csv(
        Path(artifact_paths["split_metrics_csv"]),
        [
            {"slice_name": "overall", "macro_f1": overall_score},
            {"slice_name": "id", "macro_f1": id_score},
            {"slice_name": "ood", "macro_f1": ood_score},
        ],
    )
    _write_csv(
        Path(artifact_paths["id_ood_comparison_csv"]),
        [
            {
                "metric": "macro_f1",
                "id_value": id_score,
                "ood_value": ood_score,
                "delta": id_score - ood_score,
            }
        ],
    )
    _write_csv(
        Path(artifact_paths["subgroup_metrics_csv"]),
        [
            {
                "grouping_type": "group_id",
                "group_name": "group_low",
                "support": 150,
                "eligible_for_worst_group": True,
                "macro_f1": worst_group_score,
                "accuracy": worst_group_score + 0.05,
                "error_rate": 1.0 - (worst_group_score + 0.05),
            }
        ],
    )
    _write_csv(
        Path(artifact_paths["subgroup_support_report_csv"]),
        [{"group_name": "group_low", "support": 150}],
    )
    _write_csv(
        Path(artifact_paths["calibration_summary_csv"]),
        [
            {
                "slice_name": "overall",
                "ece": ece,
                "brier_score": brier_score,
                "sample_count": 100,
            },
            {
                "slice_name": "id",
                "ece": max(ece - 0.01, 0.0),
                "brier_score": max(brier_score - 0.01, 0.0),
                "sample_count": 60,
            },
            {
                "slice_name": "ood",
                "ece": ece + 0.02,
                "brier_score": brier_score + 0.02,
                "sample_count": 40,
            },
        ],
    )
    _write_csv(
        Path(artifact_paths["calibration_bins_csv"]),
        [
            {
                "slice_name": "overall",
                "avg_confidence": 0.2,
                "empirical_accuracy": 0.3,
                "count": 20,
            },
            {"slice_name": "id", "avg_confidence": 0.4, "empirical_accuracy": 0.5, "count": 10},
            {
                "slice_name": "ood",
                "avg_confidence": 0.8,
                "empirical_accuracy": 0.6,
                "count": 10,
            },
        ],
    )


def test_build_mitigation_comparison_table_pairs_parent_and_child(temp_artifact_root):
    _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="baseline_parent",
        eval_id="eval_parent",
        experiment_group="mitigation_suite",
    )
    _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="reweight_child",
        eval_id="eval_reweight",
        experiment_group="mitigation_suite",
        root_kind="mitigation",
        mitigation_method="reweighting",
        source_parent_run_id="baseline_parent",
        id_score=0.795,
        ood_score=0.66,
        overall_score=0.69,
        worst_group_score=0.48,
        ece=0.069,
        brier_score=0.119,
    )

    candidates = select_report_candidates(load_report_inputs(experiment_group="mitigation_suite"))
    table = build_mitigation_comparison_table(candidates)

    assert table["parent_eval_id"].tolist() == ["eval_parent"]
    assert table["mitigation_eval_id"].tolist() == ["eval_reweight"]
    assert table["ood_macro_f1_delta"].iloc[0] == pytest.approx(0.04)
    assert table["worst_group_f1_delta"].iloc[0] == pytest.approx(0.04)
    assert table["verdict"].iloc[0] == "win"


def test_pair_mitigation_candidates_with_parents_fails_without_parent(temp_artifact_root):
    _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="temperature_child",
        eval_id="eval_temperature",
        experiment_group="mitigation_missing_parent",
        root_kind="mitigation",
        mitigation_method="temperature_scaling",
        source_parent_run_id="baseline_parent_missing",
        ece=0.03,
        brier_score=0.08,
    )

    candidates = load_report_inputs(experiment_group="mitigation_missing_parent")
    with pytest.raises(ValueError, match="missing its parent baseline evaluation"):
        pair_mitigation_candidates_with_parents(candidates)


def test_classify_mitigation_verdict_covers_tradeoff_and_failure_cases():
    tradeoff = classify_mitigation_verdict(
        mitigation_method="reweighting",
        deltas={
            "id_macro_f1_delta": -0.03,
            "overall_macro_f1_delta": 0.0,
            "ood_macro_f1_delta": 0.05,
            "worst_group_f1_delta": 0.02,
        },
    )
    failure = classify_mitigation_verdict(
        mitigation_method="temperature_scaling",
        deltas={
            "id_macro_f1_delta": 0.0,
            "overall_macro_f1_delta": 0.0,
            "ood_macro_f1_delta": 0.0,
            "worst_group_f1_delta": 0.0,
            "ece_delta": 0.0,
            "brier_score_delta": 0.0,
        },
    )

    assert tradeoff == "tradeoff"
    assert failure == "failure"
