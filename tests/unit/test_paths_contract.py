from __future__ import annotations

from model_failure_lab.utils.paths import (
    artifact_root,
    build_artifact_index_path,
    build_baseline_run_dir,
    build_evaluation_run_dir,
    build_mitigation_run_dir,
    build_perturbation_artifact_paths,
    build_perturbation_report_artifact_paths,
    build_perturbation_report_run_dir,
    build_perturbation_run_dir,
    build_report_artifact_paths,
    build_report_dir,
    build_report_run_dir,
    build_stability_report_artifact_paths,
    config_root,
    find_run_metadata_path,
)


def test_artifact_root_uses_temporary_override(temp_artifact_root):
    assert artifact_root() == temp_artifact_root.resolve()


def test_config_root_uses_temporary_override(temp_config_root):
    assert config_root() == temp_config_root.resolve()


def test_baseline_run_dir_uses_expected_structure(temp_artifact_root):
    run_dir = build_baseline_run_dir(
        model_name="Logistic TF-IDF",
        run_id="20260318 221500 BASELINE-AB12",
    )

    assert run_dir == (
        temp_artifact_root / "baselines" / "logistic_tf_idf" / "20260318_221500_baseline_ab12"
    )
    assert "baselines" in run_dir.parts


def test_mitigation_run_dir_uses_expected_structure(temp_artifact_root):
    run_dir = build_mitigation_run_dir(
        method_name="Group Reweighting",
        model_name="DistilBERT",
        run_id="20260318 221500 MITIGATION-CD34",
    )

    assert run_dir == (
        temp_artifact_root
        / "mitigations"
        / "group_reweighting"
        / "distilbert"
        / "20260318_221500_mitigation_cd34"
    )
    assert "mitigations" in run_dir.parts


def test_report_dir_uses_reports_root_without_shared_dumping_ground(temp_artifact_root):
    report_dir = build_report_dir(experiment_group="MVP Comparison", category="comparisons")
    summary_dir = build_report_dir(experiment_group="Table Export", category="summary_tables")

    assert report_dir == temp_artifact_root / "reports" / "comparisons" / "mvp_comparison"
    assert summary_dir == temp_artifact_root / "reports" / "summary_tables" / "table_export"
    assert report_dir.parent.name == "comparisons"
    assert summary_dir.parent.name == "summary_tables"


def test_report_run_dir_and_artifact_paths_use_expected_structure(temp_artifact_root):
    report_run_dir = build_report_run_dir("MVP Comparison", "report_run", create=True)
    artifact_paths = build_report_artifact_paths(report_run_dir)

    assert report_run_dir == (
        temp_artifact_root / "reports" / "comparisons" / "mvp_comparison" / "report_run"
    )
    assert artifact_paths["report_markdown"].endswith("report.md")
    assert artifact_paths["report_data_json"].endswith("report_data.json")
    assert artifact_paths["comparison_table_csv"].endswith("tables/comparison_table.csv")
    assert artifact_paths["id_vs_ood_primary_metric_png"].endswith(
        "figures/id_vs_ood_primary_metric.png"
    )


def test_evaluation_run_dir_nests_under_source_run(temp_artifact_root):
    source_run_dir = build_baseline_run_dir("distilbert", "source_run", create=True)
    evaluation_dir = build_evaluation_run_dir(source_run_dir, "eval_run")

    assert evaluation_dir == source_run_dir / "evaluations" / "eval_run"


def test_perturbation_run_dir_nests_under_source_run(temp_artifact_root):
    source_run_dir = build_baseline_run_dir("distilbert", "source_run", create=True)
    perturbation_dir = build_perturbation_run_dir(source_run_dir, "stress run", create=True)
    artifact_paths = build_perturbation_artifact_paths(perturbation_dir)

    assert perturbation_dir == source_run_dir / "perturbations" / "stress_run"
    assert "evaluations" not in perturbation_dir.parts
    assert artifact_paths["suite_manifest_json"].endswith("suite_manifest.json")
    assert artifact_paths["perturbed_samples_jsonl"].endswith("perturbed_samples.jsonl")
    assert artifact_paths["plots"].endswith("figures")


def test_perturbation_report_run_dir_and_artifact_paths_use_expected_structure(temp_artifact_root):
    report_run_dir = build_perturbation_report_run_dir(
        "Synthetic Stress",
        "report_run",
        create=True,
    )
    artifact_paths = build_perturbation_report_artifact_paths(report_run_dir)

    assert report_run_dir == (
        temp_artifact_root / "reports" / "perturbations" / "synthetic_stress" / "report_run"
    )
    assert artifact_paths["report_markdown"].endswith("report.md")
    assert artifact_paths["report_data_json"].endswith("report_data.json")
    assert artifact_paths["suite_summary_csv"].endswith("tables/suite_summary.csv")
    assert artifact_paths["clean_vs_perturbed_primary_metric_png"].endswith(
        "figures/clean_vs_perturbed_primary_metric.png"
    )


def test_stability_report_artifact_paths_use_expected_structure(temp_artifact_root):
    report_run_dir = build_report_run_dir("Phase20 Stability", "report_run", create=True)
    artifact_paths = build_stability_report_artifact_paths(report_run_dir)

    assert report_run_dir == (
        temp_artifact_root / "reports" / "comparisons" / "phase20_stability" / "report_run"
    )
    assert artifact_paths["report_markdown"].endswith("report.md")
    assert artifact_paths["stability_summary_json"].endswith("stability_summary.json")
    assert artifact_paths["report_data_json"].endswith("report_data.json")
    assert artifact_paths["baseline_stability_csv"].endswith("tables/baseline_stability.csv")
    assert artifact_paths["temperature_scaling_deltas_csv"].endswith(
        "tables/temperature_scaling_deltas.csv"
    )
    assert artifact_paths["reweighting_deltas_csv"].endswith("tables/reweighting_deltas.csv")


def test_artifact_index_path_uses_expected_contract_structure(temp_artifact_root):
    artifact_index_path = build_artifact_index_path(version="v1", create=True)

    assert (
        artifact_index_path
        == temp_artifact_root / "contracts" / "artifact_index" / "v1" / "index.json"
    )
    assert artifact_index_path.parent.exists()


def test_find_run_metadata_path_resolves_saved_baseline_run(temp_artifact_root):
    source_run_dir = build_baseline_run_dir("distilbert", "source_run", create=True)
    metadata_path = source_run_dir / "metadata.json"
    metadata_path.write_text("{}", encoding="utf-8")

    resolved = find_run_metadata_path("source_run")

    assert resolved == metadata_path
