from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

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
    experiment_group: str = "baselines_v1",
    id_score: float = 0.8,
    ood_score: float = 0.62,
    overall_score: float = 0.7,
    worst_group_score: float = 0.45,
) -> None:
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
    _write_json(
        eval_dir / "metadata.json",
        {
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
        },
    )
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
            },
            {
                "grouping_type": "group_id",
                "group_name": "group_mid",
                "support": 140,
                "eligible_for_worst_group": True,
                "macro_f1": 0.55,
                "accuracy": 0.6,
                "error_rate": 0.4,
            },
        ],
    )
    _write_csv(
        Path(artifact_paths["subgroup_support_report_csv"]),
        [{"group_name": "group_low", "support": 150}],
    )
    _write_csv(
        Path(artifact_paths["calibration_summary_csv"]),
        [
            {"slice_name": "overall", "ece": 0.07, "brier_score": 0.12, "sample_count": 100},
            {"slice_name": "id", "ece": 0.05, "brier_score": 0.11, "sample_count": 60},
            {"slice_name": "ood", "ece": 0.09, "brier_score": 0.14, "sample_count": 40},
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
            {
                "slice_name": "overall",
                "avg_confidence": 0.8,
                "empirical_accuracy": 0.7,
                "count": 20,
            },
            {
                "slice_name": "id",
                "avg_confidence": 0.2,
                "empirical_accuracy": 0.25,
                "count": 10,
            },
            {
                "slice_name": "ood",
                "avg_confidence": 0.8,
                "empirical_accuracy": 0.6,
                "count": 10,
            },
        ],
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

    assert Path(artifact_paths["report_markdown"]).exists()
    assert Path(artifact_paths["comparison_table_csv"]).exists()
    assert Path(artifact_paths["id_vs_ood_primary_metric_png"]).exists()
    assert metadata["selection_mode"] == "experiment_group"
    assert metadata["source_eval_ids"] == ["eval_b", "eval_a"]
