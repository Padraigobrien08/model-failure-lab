from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from model_failure_lab.reporting import (
    discover_evaluation_bundles,
    load_report_inputs,
    select_report_candidates,
)
from model_failure_lab.utils.paths import build_baseline_run_dir, build_evaluation_run_dir


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
    dataset_name: str = "civilcomments",
    label_field: str = "toxicity",
    text_field: str = "comment_text",
    evaluator_version: str = "eval-schema-v1",
    subgroup_fields: list[str] | None = None,
    min_group_support: int = 100,
) -> Path:
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
    metadata_payload = {
        "run_id": eval_id,
        "eval_id": eval_id,
        "source_run_id": source_run_id,
        "experiment_type": "shift_eval",
        "model_name": model_name,
        "dataset_name": dataset_name,
        "resolved_config": {
            "experiment_group": experiment_group,
            "data": {
                "dataset_name": dataset_name,
                "label_field": label_field,
                "text_field": text_field,
                "group_fields": subgroup_fields or ["male", "female"],
            },
        },
        "artifact_paths": artifact_paths,
        "evaluator_version": evaluator_version,
        "git_commit_hash": evaluator_version,
        "min_group_support": min_group_support,
        "tags": [experiment_group, "shift_eval"],
    }
    _write_json(eval_dir / "metadata.json", metadata_payload)
    _write_json(
        Path(artifact_paths["overall_metrics_json"]),
        {
            "headline_metrics": {
                "accuracy": 0.75,
                "macro_f1": 0.7,
                "auroc": 0.82,
                "worst_group_f1": 0.45,
                "robustness_gap_f1": 0.18,
            },
            "overall": {"macro_f1": 0.7},
            "id": {"macro_f1": 0.8},
            "ood": {"macro_f1": 0.62},
        },
    )
    _write_json(
        Path(artifact_paths["worst_group_summary_json"]),
        {"worst_group_f1": {"group_id": "group_a", "value": 0.45, "support": 120}},
    )
    _write_json(Path(artifact_paths["confidence_summary_json"]), {"overall": {}})
    _write_json(Path(artifact_paths["diagnostics_json"]), {"score_distribution": {}})
    _write_csv(
        Path(artifact_paths["split_metrics_csv"]),
        [
            {"slice_name": "overall", "macro_f1": 0.7},
            {"slice_name": "id", "macro_f1": 0.8},
            {"slice_name": "ood", "macro_f1": 0.62},
        ],
    )
    _write_csv(
        Path(artifact_paths["id_ood_comparison_csv"]),
        [{"metric": "macro_f1", "id_value": 0.8, "ood_value": 0.62, "delta": 0.18}],
    )
    _write_csv(
        Path(artifact_paths["subgroup_metrics_csv"]),
        [
            {
                "grouping_type": "group_id",
                "group_name": "group_a",
                "support": 120,
                "eligible_for_worst_group": True,
                "macro_f1": 0.45,
                "accuracy": 0.5,
                "error_rate": 0.5,
            }
        ],
    )
    _write_csv(
        Path(artifact_paths["subgroup_support_report_csv"]),
        [{"group_name": "group_a", "support": 120}],
    )
    _write_csv(
        Path(artifact_paths["calibration_summary_csv"]),
        [{"slice_name": "overall", "ece": 0.07, "brier_score": 0.12}],
    )
    _write_csv(
        Path(artifact_paths["calibration_bins_csv"]),
        [{"slice_name": "overall", "bin_lower": 0.0, "bin_upper": 0.1, "count": 1}],
    )
    return eval_dir / "metadata.json"


def test_discover_evaluation_bundles_by_experiment_group(temp_artifact_root):
    first_path = _create_evaluation_bundle(
        model_name="logistic_tfidf",
        source_run_id="baseline_a",
        eval_id="eval_a",
        experiment_group="baselines_v1",
    )
    second_path = _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="baseline_b",
        eval_id="eval_b",
        experiment_group="baselines_v1",
    )
    _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="baseline_c",
        eval_id="eval_c",
        experiment_group="different_group",
    )

    discovered = discover_evaluation_bundles(experiment_group="baselines_v1")

    assert discovered == sorted([first_path.resolve(), second_path.resolve()])


def test_load_report_inputs_by_explicit_eval_ids(temp_artifact_root):
    _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="baseline_c",
        eval_id="eval_c",
        experiment_group="different_group",
    )
    _create_evaluation_bundle(
        model_name="logistic_tfidf",
        source_run_id="baseline_a",
        eval_id="eval_a",
        experiment_group="baselines_v1",
    )

    candidates = load_report_inputs(eval_ids=["eval_a"])

    assert len(candidates) == 1
    assert candidates[0].eval_id == "eval_a"
    assert candidates[0].overall_metrics["headline_metrics"]["macro_f1"] == 0.7


def test_select_report_candidates_rejects_non_comparable_runs(temp_artifact_root):
    _create_evaluation_bundle(
        model_name="logistic_tfidf",
        source_run_id="baseline_a",
        eval_id="eval_a",
        experiment_group="baselines_v1",
        dataset_name="civilcomments",
    )
    _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="baseline_b",
        eval_id="eval_b",
        experiment_group="baselines_v1",
        dataset_name="other_dataset",
    )

    candidates = load_report_inputs(experiment_group="baselines_v1")

    with pytest.raises(ValueError, match="not comparable: dataset mismatch"):
        select_report_candidates(candidates)


def test_select_report_candidates_orders_by_model_and_source_run(temp_artifact_root):
    _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="baseline_b",
        eval_id="eval_b",
        experiment_group="baselines_v1",
    )
    _create_evaluation_bundle(
        model_name="logistic_tfidf",
        source_run_id="baseline_a",
        eval_id="eval_a",
        experiment_group="baselines_v1",
    )

    selected = select_report_candidates(load_report_inputs(experiment_group="baselines_v1"))

    assert [candidate.eval_id for candidate in selected] == ["eval_b", "eval_a"]
