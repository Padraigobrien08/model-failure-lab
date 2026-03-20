from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from model_failure_lab.models.export import build_prediction_records
from model_failure_lab.reporting import (
    build_calibration_curve_figure,
    build_calibration_table,
    build_comparison_table,
    build_id_ood_comparison_frame,
    build_id_ood_figure,
    build_report_metadata,
    build_report_summary,
    build_subgroup_table,
    build_worst_group_vs_average_figure,
    build_worst_group_vs_average_frame,
    build_worst_subgroups_figure,
    load_report_inputs,
    render_report_markdown,
    select_report_candidates,
    write_report_bundle,
)
from model_failure_lab.utils.paths import build_baseline_run_dir, build_prediction_artifact_path
from scripts.run_shift_eval import run_command as run_shift_eval_command


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def _build_prediction_rows(
    *,
    run_id: str,
    model_name: str,
    split: str,
    is_id: bool,
    is_ood: bool,
    group_accuracy: dict[str, float],
    group_support: dict[str, int],
) -> list[dict[str, object]]:
    sample_ids: list[str] = []
    splits: list[str] = []
    true_labels: list[int] = []
    predicted_labels: list[int] = []
    probability_rows: list[list[float]] = []
    group_ids: list[str] = []
    is_id_flags: list[bool] = []
    is_ood_flags: list[bool] = []

    for group_name, support in group_support.items():
        accuracy = float(group_accuracy[group_name])
        correct_count = int(round(support * accuracy))
        for index in range(support):
            true_label = index % 2
            predicted_label = true_label if index < correct_count else 1 - true_label
            confidence = 0.85 if predicted_label == true_label else 0.78
            prob_1 = confidence if predicted_label == 1 else 1.0 - confidence

            sample_ids.append(f"{split}_{group_name}_{index}")
            splits.append(split)
            true_labels.append(true_label)
            predicted_labels.append(predicted_label)
            probability_rows.append([1.0 - prob_1, prob_1])
            group_ids.append(group_name)
            is_id_flags.append(is_id)
            is_ood_flags.append(is_ood)

    return build_prediction_records(
        run_id=run_id,
        model_name=model_name,
        sample_ids=sample_ids,
        splits=splits,
        true_labels=true_labels,
        predicted_labels=predicted_labels,
        probability_rows=probability_rows,
        group_ids=group_ids,
        is_id_flags=is_id_flags,
        is_ood_flags=is_ood_flags,
    )


def _create_evaluation_bundle(
    *,
    model_name: str,
    source_run_id: str,
    eval_id: str,
    experiment_group: str = "baselines_v1",
    id_score: float = 0.8,
    ood_score: float = 0.62,
    overall_score: float = 0.7,
    worst_group_score: float = 0.45,
) -> None:
    del overall_score
    source_run_dir = build_baseline_run_dir(model_name, source_run_id, create=True)
    group_support = {"group_low": 150, "group_mid": 140}
    id_group_accuracy = {
        "group_low": max(min(id_score - 0.03, 0.99), 0.0),
        "group_mid": max(min(id_score + 0.03, 0.99), 0.0),
    }
    ood_group_accuracy = {
        "group_low": max(min(worst_group_score, 0.99), 0.0),
        "group_mid": max(min((2 * ood_score) - worst_group_score, 0.99), 0.0),
    }
    prediction_records = {
        "id_test": _build_prediction_rows(
            run_id=source_run_id,
            model_name=model_name,
            split="id_test",
            is_id=True,
            is_ood=False,
            group_accuracy=id_group_accuracy,
            group_support=group_support,
        ),
        "ood_test": _build_prediction_rows(
            run_id=source_run_id,
            model_name=model_name,
            split="ood_test",
            is_id=False,
            is_ood=True,
            group_accuracy=ood_group_accuracy,
            group_support=group_support,
        ),
    }

    artifact_paths = {"predictions": {}}
    for split, records in prediction_records.items():
        output_path = build_prediction_artifact_path(source_run_dir, split)
        pd.DataFrame(records).to_parquet(output_path, index=False)
        artifact_paths["predictions"][split] = str(output_path)

    metadata_payload = {
        "run_id": source_run_id,
        "experiment_type": "baseline",
        "model_name": model_name,
        "dataset_name": "civilcomments",
        "experiment_group": experiment_group,
        "split_details": {
            "train": "train",
            "validation": "validation",
            "id_test": "id_test",
            "ood_test": "ood_test",
        },
        "resolved_config": {
            "experiment_group": experiment_group,
            "seed": 13,
            "tags": ["baseline", model_name, experiment_group],
            "data": {
                "dataset_name": "civilcomments",
                "label_field": "toxicity",
                "text_field": "comment_text",
                "group_fields": ["male", "female"],
                "raw_splits": {"train": "train", "val": "val", "test": "test"},
                "split_details": {
                    "train": "train",
                    "validation": "validation",
                    "id_test": "id_test",
                    "ood_test": "ood_test",
                },
                "split_role_policy": {
                    "train": {
                        "raw_split": "train",
                        "selector": "train_remainder",
                        "is_id": True,
                        "is_ood": False,
                    },
                    "validation": {
                        "raw_split": "val",
                        "selector": "full_split",
                        "is_id": False,
                        "is_ood": True,
                    },
                    "id_test": {
                        "raw_split": "train",
                        "selector": "deterministic_holdout",
                        "is_id": True,
                        "is_ood": False,
                        "holdout_fraction": 0.1,
                        "holdout_seed": 13,
                    },
                    "ood_test": {
                        "raw_split": "test",
                        "selector": "full_split",
                        "is_id": False,
                        "is_ood": True,
                    },
                },
                "validation": {
                    "subgroup_min_samples_warning": 25,
                    "preview_samples": 5,
                },
            },
            "eval": {"primary_metric": "macro_f1"},
        },
        "artifact_paths": artifact_paths,
    }
    _write_json(source_run_dir / "metadata.json", metadata_payload)

    with patch("scripts.run_shift_eval.generate_run_id", return_value=eval_id):
        run_shift_eval_command(
            [
                "--run-id",
                source_run_id,
                "--splits",
                "id_test,ood_test",
                "--min-group-support",
                "100",
                "--calibration-bins",
                "5",
            ]
        )


def test_build_calibration_outputs_and_tables(temp_artifact_root):
    _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="run_b",
        eval_id="eval_b",
    )
    _create_evaluation_bundle(
        model_name="logistic_tfidf",
        source_run_id="run_a",
        eval_id="eval_a",
    )

    candidates = select_report_candidates(load_report_inputs(experiment_group="baselines_v1"))
    calibration_table = build_calibration_table(candidates)
    calibration_figure = build_calibration_curve_figure(candidates)

    assert calibration_table["slice_name"].tolist() == [
        "overall",
        "overall",
        "id",
        "id",
        "ood",
        "ood",
    ]
    assert len(calibration_figure.axes) == 3


def test_render_report_markdown_and_summary_payload(temp_artifact_root):
    _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="run_b",
        eval_id="eval_b",
    )
    _create_evaluation_bundle(
        model_name="logistic_tfidf",
        source_run_id="run_a",
        eval_id="eval_a",
    )

    candidates = select_report_candidates(load_report_inputs(experiment_group="baselines_v1"))
    comparison_table = build_comparison_table(build_id_ood_comparison_frame(candidates))
    subgroup_table = build_subgroup_table(candidates, top_k=2, min_group_support=100)
    calibration_table = build_calibration_table(candidates)
    report_summary = build_report_summary(
        candidates,
        comparison_table=comparison_table,
        subgroup_table=subgroup_table,
        calibration_table=calibration_table,
        report_title="Baseline Robustness Report",
    )

    markdown = render_report_markdown(
        report_title="Baseline Robustness Report",
        report_summary=report_summary,
        figure_paths={
            "id_vs_ood_primary_metric": "figures/id_vs_ood_primary_metric.png",
            "worst_group_vs_average": "figures/worst_group_vs_average.png",
            "worst_subgroups": "figures/worst_subgroups.png",
            "calibration_curve": "figures/calibration_curve.png",
        },
        table_paths={
            "comparison_table": "tables/comparison_table.csv",
            "subgroup_table": "tables/subgroup_table.csv",
            "calibration_table": "tables/calibration_table.csv",
        },
    )

    assert markdown.index("## Overview") < markdown.index("## Compared runs")
    assert markdown.index("## Compared runs") < markdown.index("## Headline findings")
    assert markdown.index("## Headline findings") < markdown.index("## ID vs OOD degradation")
    assert markdown.index("## Calibration summary") < markdown.index("## Key takeaway")
    assert markdown.count("- ") >= 3
    assert "figures/id_vs_ood_primary_metric.png" in markdown
    assert "tables/calibration_table.csv" in markdown
    assert 3 <= len(report_summary["headline_findings"]) <= 5
    assert len(report_summary["headline_findings"]) <= 5
    assert report_summary["compared_runs"][0]["label"] == "distilbert:run_b"


def test_write_report_bundle_and_metadata(temp_artifact_root):
    _create_evaluation_bundle(
        model_name="distilbert",
        source_run_id="run_b",
        eval_id="eval_b",
    )
    _create_evaluation_bundle(
        model_name="logistic_tfidf",
        source_run_id="run_a",
        eval_id="eval_a",
    )

    candidates = select_report_candidates(load_report_inputs(experiment_group="baselines_v1"))
    comparison_table = build_comparison_table(build_id_ood_comparison_frame(candidates))
    subgroup_table = build_subgroup_table(candidates, top_k=2, min_group_support=100)
    calibration_table = build_calibration_table(candidates)
    report_summary = build_report_summary(
        candidates,
        comparison_table=comparison_table,
        subgroup_table=subgroup_table,
        calibration_table=calibration_table,
        report_title="Baseline Robustness Report",
    )
    markdown = render_report_markdown(
        report_title="Baseline Robustness Report",
        report_summary=report_summary,
        figure_paths={
            "id_vs_ood_primary_metric": "figures/id_vs_ood_primary_metric.png",
            "worst_group_vs_average": "figures/worst_group_vs_average.png",
            "worst_subgroups": "figures/worst_subgroups.png",
            "calibration_curve": "figures/calibration_curve.png",
        },
        table_paths={
            "comparison_table": "tables/comparison_table.csv",
            "subgroup_table": "tables/subgroup_table.csv",
            "calibration_table": "tables/calibration_table.csv",
        },
    )
    report_run_dir = temp_artifact_root / "reports" / "comparisons" / "baselines_v1" / "report_run"
    artifact_paths = write_report_bundle(
        report_run_dir,
        markdown=markdown,
        report_summary=report_summary,
        figures={
            "id_vs_ood_primary_metric": build_id_ood_figure(
                build_id_ood_comparison_frame(candidates)
            ),
            "worst_group_vs_average": build_worst_group_vs_average_figure(
                build_worst_group_vs_average_frame(candidates)
            ),
            "worst_subgroups": build_worst_subgroups_figure(subgroup_table),
            "calibration_curve": build_calibration_curve_figure(candidates),
        },
        comparison_table=comparison_table,
        subgroup_table=subgroup_table,
        calibration_table=calibration_table,
    )
    metadata = build_report_metadata(
        report_id="report_run",
        report_scope="baselines_v1",
        selection_mode="experiment_group",
        source_eval_ids=[candidate.eval_id for candidate in candidates],
        resolved_config={
            "seed": 13,
            "notes": "",
            "tags": ["report"],
            "report": {"report_name": "Baseline Robustness Report", "top_k_subgroups": 2},
            "eval": {"min_group_support": 100},
        },
        command="python scripts/build_report.py --experiment-group baselines_v1",
        run_dir=report_run_dir,
        dataset_name="civilcomments",
        split_details={
            "train": "train",
            "validation": "validation",
            "id_test": "id_test",
            "ood_test": "ood_test",
        },
        artifact_paths=artifact_paths,
        git_commit_hash="abc123",
        library_versions={"pandas": "2.1.1"},
        status="completed",
    )
    report_data = json.loads(Path(artifact_paths["report_data_json"]).read_text(encoding="utf-8"))

    assert Path(artifact_paths["report_markdown"]).exists()
    assert Path(artifact_paths["comparison_table_csv"]).exists()
    assert Path(artifact_paths["report_data_json"]).exists()
    assert Path(artifact_paths["id_vs_ood_primary_metric_png"]).exists()
    assert metadata["selection_mode"] == "experiment_group"
    assert metadata["source_eval_ids"] == ["eval_b", "eval_a"]
    assert report_data["report_summary"]["report_title"] == "Baseline Robustness Report"
    assert len(report_data["comparison_table"]) == 2
