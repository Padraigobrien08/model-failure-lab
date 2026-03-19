from __future__ import annotations

from model_failure_lab.config.loader import load_experiment_config
from model_failure_lab.data import resolve_split_policy
from model_failure_lab.utils.paths import (
    build_data_dir,
    build_data_manifest_dir,
    build_data_manifest_path,
    build_data_summary_dir,
)


def test_repository_civilcomments_config_preserves_raw_split_policy(temp_artifact_root):
    config = load_experiment_config("configs/experiments/civilcomments_logistic_baseline.yaml")

    assert config["data"]["raw_splits"] == {"train": "train", "val": "val", "test": "test"}
    assert config["split_details"]["id_test"] == "train_holdout"
    assert config["data"]["validation"]["preview_samples"] == 5
    assert set(resolve_split_policy(config["data"])) == {
        "train",
        "validation",
        "id_test",
        "ood_test",
    }


def test_data_artifact_helpers_resolve_under_artifacts_data(temp_artifact_root):
    data_dir = build_data_dir(create=True)
    manifest_dir = build_data_manifest_dir(create=True)
    summary_dir = build_data_summary_dir(create=True)
    manifest_path = build_data_manifest_path("civilcomments")

    assert data_dir == temp_artifact_root / "data"
    assert manifest_dir == temp_artifact_root / "data" / "manifests"
    assert summary_dir == temp_artifact_root / "data" / "summaries"
    assert manifest_path == manifest_dir / "civilcomments_manifest.json"
