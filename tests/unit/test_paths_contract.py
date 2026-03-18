from __future__ import annotations

from model_failure_lab.utils.paths import (
    artifact_root,
    build_baseline_run_dir,
    build_mitigation_run_dir,
    build_report_dir,
    config_root,
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
