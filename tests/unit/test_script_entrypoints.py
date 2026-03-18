from __future__ import annotations

import json

import pytest

from scripts.build_report import run_command as run_build_report_command
from scripts.download_data import run_command as run_download_data_command
from scripts.run_baseline import run_command as run_baseline_command
from scripts.run_mitigation import run_command as run_mitigation_command
from scripts.run_shift_eval import run_command as run_shift_eval_command


@pytest.mark.parametrize(
    ("model_name", "expected_segment"),
    [
        ("logistic_tfidf", "artifacts/baselines/logistic_tfidf"),
        ("distilbert", "artifacts/baselines/distilbert"),
    ],
)
def test_run_baseline_bootstrap_writes_metadata(temp_artifact_root, model_name, expected_segment):
    result = run_baseline_command(["--model", model_name, "--run-id", f"{model_name}_baseline"])
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert expected_segment in result.run_dir.as_posix()
    assert metadata["model_name"] == model_name
    assert metadata["status"] == "scaffold_ready"
    assert result.metadata_path.name == "metadata.json"


@pytest.mark.parametrize(
    ("method_name", "expected_segment"),
    [
        ("reweighting", "artifacts/mitigations/reweighting"),
        ("calibration", "artifacts/mitigations/calibration"),
    ],
)
def test_run_mitigation_bootstrap_uses_separate_root(
    temp_artifact_root,
    method_name,
    expected_segment,
):
    result = run_mitigation_command(
        ["--run-id", "baseline_parent_001", "--method", method_name, "--output-run-id", method_name]
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert expected_segment in result.run_dir.as_posix()
    assert metadata["parent_run_id"] == "baseline_parent_001"
    assert metadata["status"] == "scaffold_ready"
    assert "artifacts/baselines" not in result.run_dir.as_posix()


def test_shift_eval_bootstrap_writes_metadata(temp_artifact_root):
    result = run_shift_eval_command(["--run-id", "baseline_parent_002"])
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "artifacts/reports/comparisons/baseline_parent_002" in result.run_dir.as_posix()
    assert metadata["experiment_type"] == "shift_eval"
    assert metadata["parent_run_id"] == "baseline_parent_002"


def test_build_report_bootstrap_writes_metadata(temp_artifact_root):
    result = run_build_report_command(["--experiment-group", "mvp_summary"])
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "artifacts/reports/comparisons/mvp_summary" in result.run_dir.as_posix()
    assert metadata["experiment_type"] == "report"
    assert result.metadata_path.exists()


def test_download_data_bootstrap_writes_metadata(temp_artifact_root):
    result = run_download_data_command([])
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "artifacts/reports/summary_tables/data_download" in result.run_dir.as_posix()
    assert metadata["experiment_type"] == "data_download"
    assert result.metadata_path.exists()
