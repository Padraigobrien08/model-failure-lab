from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from scripts.build_report import run_command as run_build_report_command
from scripts.download_data import run_command as run_download_data_command
from scripts.run_baseline import run_command as run_baseline_command
from scripts.run_mitigation import run_command as run_mitigation_command
from scripts.run_shift_eval import run_command as run_shift_eval_command


@dataclass
class _FakeDataset:
    split_dict: dict[str, int]
    data_dir: str
    version: str
    metadata_fields: list[str]


def _fake_materialize(config: dict[str, object], *, download: bool):
    from model_failure_lab.data import materialize_civilcomments

    def fake_get_dataset(**_: object) -> _FakeDataset:
        return _FakeDataset(
            split_dict={"train": 0, "val": 1, "test": 2},
            data_dir="/tmp/fake_civilcomments",
            version="1.0",
            metadata_fields=["male", "female", "y"],
        )

    assert download is True
    return materialize_civilcomments(config, get_dataset_fn=fake_get_dataset)


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
    result = run_download_data_command([], materialize_fn=_fake_materialize)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert "artifacts/data/runs" in result.run_dir.as_posix()
    assert metadata["experiment_type"] == "data_download"
    assert metadata["status"] == "materialized"
    assert metadata["artifact_paths"]["manifest_json"].endswith("civilcomments_manifest.json")
    assert result.metadata_path.exists()
