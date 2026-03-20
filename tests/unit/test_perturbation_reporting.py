from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from model_failure_lab.reporting import (
    build_clean_vs_perturbed_figure,
    build_perturbation_family_drop_figure,
    build_perturbation_report_metadata,
    build_perturbation_report_summary,
    build_perturbation_report_tables,
    build_severity_ladder_figure,
    load_perturbation_report_inputs,
    render_perturbation_report_markdown,
    write_perturbation_report_bundle,
)
from model_failure_lab.utils.paths import (
    build_baseline_run_dir,
    build_perturbation_report_run_dir,
    build_perturbation_run_dir,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def _write_perturbation_bundle(
    *,
    model_name: str,
    source_run_id: str,
    eval_id: str,
    experiment_group: str,
    families: list[str] | None = None,
    severities: list[str] | None = None,
    source_split: str = "validation",
    macro_f1_drop: float = 0.18,
) -> Path:
    resolved_families = families or ["typo_noise", "format_degradation", "slang_rewrite"]
    resolved_severities = severities or ["low", "medium", "high"]
    source_run_dir = build_baseline_run_dir(model_name, source_run_id, create=True)
    perturbation_dir = build_perturbation_run_dir(source_run_dir, eval_id, create=True)
    figures_dir = perturbation_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    artifact_paths = {
        "suite_manifest_json": str(perturbation_dir / "suite_manifest.json"),
        "perturbed_samples_jsonl": str(perturbation_dir / "perturbed_samples.jsonl"),
        "sample_preview_jsonl": str(perturbation_dir / "sample_preview.jsonl"),
        "predictions_perturbed_parquet": str(perturbation_dir / "predictions_perturbed.parquet"),
        "suite_summary_csv": str(perturbation_dir / "suite_summary.csv"),
        "family_summary_csv": str(perturbation_dir / "family_summary.csv"),
        "severity_summary_csv": str(perturbation_dir / "severity_summary.csv"),
        "family_severity_matrix_csv": str(perturbation_dir / "family_severity_matrix.csv"),
        "source_delta_summary_csv": str(perturbation_dir / "source_delta_summary.csv"),
        "figures_dir": str(figures_dir),
        "plots": str(figures_dir),
    }
    (perturbation_dir / "metadata.json").write_text(
        json.dumps(
            {
                "run_id": eval_id,
                "source_run_id": source_run_id,
                "experiment_type": "perturbation_eval",
                "model_name": model_name,
                "dataset_name": "civilcomments",
                "split_details": {
                    "train": "train",
                    "validation": "validation",
                    "id_test": "id_test",
                    "ood_test": "ood_test",
                },
                "source_split": source_split,
                "perturbation_schema_version": "perturbation-suite-v1",
                "resolved_config": {
                    "experiment_group": experiment_group,
                    "perturbation": {
                        "families": resolved_families,
                        "severities": resolved_severities,
                    },
                },
                "artifact_paths": artifact_paths,
                "tags": [experiment_group, "perturbation", "synthetic_stress"],
            }
        ),
        encoding="utf-8",
    )

    _write_csv(
        Path(artifact_paths["suite_summary_csv"]),
        [
            {
                "row_type": "suite",
                "row_name": "overall",
                "source_sample_count": 25,
                "perturbed_sample_count": 225,
                "clean_accuracy": 0.84,
                "perturbed_accuracy": 0.71,
                "accuracy_drop": 0.13,
                "clean_macro_f1": 0.82,
                "perturbed_macro_f1": 0.82 - macro_f1_drop,
                "macro_f1_drop": macro_f1_drop,
                "clean_auroc": 0.9,
                "perturbed_auroc": 0.84,
                "auroc_drop": 0.06,
            }
        ],
    )
    _write_csv(
        Path(artifact_paths["family_summary_csv"]),
        [
            {
                "row_type": "family",
                "row_name": "typo_noise",
                "perturbation_family": "typo_noise",
                "source_sample_count": 25,
                "perturbed_sample_count": 75,
                "clean_accuracy": 0.84,
                "perturbed_accuracy": 0.73,
                "accuracy_drop": 0.11,
                "clean_macro_f1": 0.82,
                "perturbed_macro_f1": 0.69,
                "macro_f1_drop": 0.13,
                "clean_auroc": 0.9,
                "perturbed_auroc": 0.85,
                "auroc_drop": 0.05,
            },
            {
                "row_type": "family",
                "row_name": "slang_rewrite",
                "perturbation_family": "slang_rewrite",
                "source_sample_count": 25,
                "perturbed_sample_count": 75,
                "clean_accuracy": 0.84,
                "perturbed_accuracy": 0.66,
                "accuracy_drop": 0.18,
                "clean_macro_f1": 0.82,
                "perturbed_macro_f1": 0.58,
                "macro_f1_drop": 0.24,
                "clean_auroc": 0.9,
                "perturbed_auroc": 0.8,
                "auroc_drop": 0.1,
            },
        ],
    )
    _write_csv(
        Path(artifact_paths["severity_summary_csv"]),
        [
            {
                "row_type": "severity",
                "row_name": "low",
                "severity": "low",
                "source_sample_count": 25,
                "perturbed_sample_count": 75,
                "clean_accuracy": 0.84,
                "perturbed_accuracy": 0.78,
                "accuracy_drop": 0.06,
                "clean_macro_f1": 0.82,
                "perturbed_macro_f1": 0.75,
                "macro_f1_drop": 0.07,
                "clean_auroc": 0.9,
                "perturbed_auroc": 0.88,
                "auroc_drop": 0.02,
            },
            {
                "row_type": "severity",
                "row_name": "medium",
                "severity": "medium",
                "source_sample_count": 25,
                "perturbed_sample_count": 75,
                "clean_accuracy": 0.84,
                "perturbed_accuracy": 0.72,
                "accuracy_drop": 0.12,
                "clean_macro_f1": 0.82,
                "perturbed_macro_f1": 0.68,
                "macro_f1_drop": 0.14,
                "clean_auroc": 0.9,
                "perturbed_auroc": 0.84,
                "auroc_drop": 0.06,
            },
            {
                "row_type": "severity",
                "row_name": "high",
                "severity": "high",
                "source_sample_count": 25,
                "perturbed_sample_count": 75,
                "clean_accuracy": 0.84,
                "perturbed_accuracy": 0.62,
                "accuracy_drop": 0.22,
                "clean_macro_f1": 0.82,
                "perturbed_macro_f1": 0.52,
                "macro_f1_drop": 0.3,
                "clean_auroc": 0.9,
                "perturbed_auroc": 0.78,
                "auroc_drop": 0.12,
            },
        ],
    )
    _write_csv(
        Path(artifact_paths["family_severity_matrix_csv"]),
        [
            {
                "row_type": "family_severity",
                "row_name": "typo_noise:low",
                "perturbation_family": "typo_noise",
                "severity": "low",
                "source_sample_count": 25,
                "perturbed_sample_count": 25,
                "clean_accuracy": 0.84,
                "perturbed_accuracy": 0.79,
                "accuracy_drop": 0.05,
                "clean_macro_f1": 0.82,
                "perturbed_macro_f1": 0.76,
                "macro_f1_drop": 0.06,
                "clean_auroc": 0.9,
                "perturbed_auroc": 0.88,
                "auroc_drop": 0.02,
            }
        ],
    )
    return perturbation_dir / "metadata.json"


def test_load_perturbation_report_inputs_orders_candidates_by_model_and_source_run(
    temp_artifact_root,
):
    _write_perturbation_bundle(
        model_name="logistic_tfidf",
        source_run_id="baseline_a",
        eval_id="perturb_a",
        experiment_group="stress_v1",
    )
    _write_perturbation_bundle(
        model_name="distilbert",
        source_run_id="baseline_b",
        eval_id="perturb_b",
        experiment_group="stress_v1",
    )

    candidates = load_perturbation_report_inputs(experiment_group="stress_v1")

    assert [candidate.eval_id for candidate in candidates] == ["perturb_b", "perturb_a"]


def test_load_perturbation_report_inputs_rejects_family_mismatch(temp_artifact_root):
    _write_perturbation_bundle(
        model_name="logistic_tfidf",
        source_run_id="baseline_a",
        eval_id="perturb_a",
        experiment_group="stress_v1",
        families=["typo_noise", "format_degradation"],
    )
    _write_perturbation_bundle(
        model_name="distilbert",
        source_run_id="baseline_b",
        eval_id="perturb_b",
        experiment_group="stress_v1",
        families=["typo_noise", "slang_rewrite"],
    )

    with pytest.raises(ValueError, match="family-set mismatch"):
        load_perturbation_report_inputs(experiment_group="stress_v1")


def test_render_and_write_perturbation_report_bundle(temp_artifact_root):
    _write_perturbation_bundle(
        model_name="logistic_tfidf",
        source_run_id="baseline_a",
        eval_id="perturb_a",
        experiment_group="stress_v1",
    )
    _write_perturbation_bundle(
        model_name="distilbert",
        source_run_id="baseline_b",
        eval_id="perturb_b",
        experiment_group="stress_v1",
        macro_f1_drop=0.11,
    )

    candidates = load_perturbation_report_inputs(experiment_group="stress_v1")
    tables = build_perturbation_report_tables(candidates)
    report_summary = build_perturbation_report_summary(
        candidates,
        suite_summary=tables["suite_summary"],
        family_summary=tables["family_summary"],
        severity_summary=tables["severity_summary"],
        report_title="Synthetic Stress Report",
    )
    markdown = render_perturbation_report_markdown(
        report_title="Synthetic Stress Report",
        report_summary=report_summary,
        figure_paths={
            "clean_vs_perturbed_primary_metric": "figures/clean_vs_perturbed_primary_metric.png",
            "perturbation_family_drop": "figures/perturbation_family_drop.png",
            "severity_ladder": "figures/severity_ladder.png",
        },
        table_paths={
            "suite_summary": "tables/suite_summary.csv",
            "family_summary": "tables/family_summary.csv",
            "severity_summary": "tables/severity_summary.csv",
            "family_severity_matrix": "tables/family_severity_matrix.csv",
        },
    )
    report_run_dir = build_perturbation_report_run_dir("stress_v1", "report_run", create=True)
    artifact_paths = write_perturbation_report_bundle(
        report_run_dir,
        markdown=markdown,
        report_summary=report_summary,
        figures={
            "clean_vs_perturbed_primary_metric": build_clean_vs_perturbed_figure(
                tables["suite_summary"]
            ),
            "perturbation_family_drop": build_perturbation_family_drop_figure(
                tables["family_summary"]
            ),
            "severity_ladder": build_severity_ladder_figure(tables["severity_summary"]),
        },
        suite_summary=tables["suite_summary"],
        family_summary=tables["family_summary"],
        severity_summary=tables["severity_summary"],
        family_severity_matrix=tables["family_severity_matrix"],
    )
    metadata = build_perturbation_report_metadata(
        report_id="report_run",
        report_scope="stress_v1",
        selection_mode="experiment_group",
        source_eval_ids=[candidate.eval_id for candidate in candidates],
        resolved_config={
            "seed": 13,
            "notes": "",
            "tags": ["perturbation"],
            "report": {"report_name": "Synthetic Stress Report"},
        },
        command="python scripts/build_perturbation_report.py --experiment-group stress_v1",
        run_dir=report_run_dir,
        dataset_name="civilcomments",
        split_details={
            "train": "train",
            "validation": "validation",
            "id_test": "id_test",
            "ood_test": "ood_test",
        },
        artifact_paths=artifact_paths,
        status="completed",
    )
    report_data = json.loads(Path(artifact_paths["report_data_json"]).read_text(encoding="utf-8"))

    assert "synthetic perturbation bundles only" in markdown
    assert "not canonical WILDS" in markdown
    assert Path(artifact_paths["report_markdown"]).exists()
    assert Path(artifact_paths["report_data_json"]).exists()
    assert Path(artifact_paths["clean_vs_perturbed_primary_metric_png"]).exists()
    assert metadata["selection_mode"] == "experiment_group"
    assert metadata["source_eval_ids"] == ["perturb_b", "perturb_a"]
    assert report_data["report_summary"]["report_title"] == "Synthetic Stress Report"
    assert len(report_data["suite_summary"]) == 2
