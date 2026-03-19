from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from model_failure_lab.config.loader import load_experiment_config
from model_failure_lab.data import (
    DataDependencyError,
    materialize_civilcomments,
    resolve_split_policy,
)
from model_failure_lab.utils.paths import (
    build_data_dir,
    build_data_manifest_dir,
    build_data_manifest_path,
    build_data_summary_dir,
)
from scripts.download_data import run_command as run_download_data_command


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


@dataclass
class _FakeDataset:
    split_dict: dict[str, int]
    data_dir: str
    version: str
    metadata_fields: list[str]
    source_records: list[dict[str, object]]


def _fake_get_dataset(**_: object) -> _FakeDataset:
    return _FakeDataset(
        split_dict={"train": 0, "val": 1, "test": 2},
        data_dir="/tmp/fake_civilcomments",
        version="1.0",
        metadata_fields=["male", "female", "y"],
        source_records=[
            {
                "raw_index": 0,
                "raw_split": "train",
                "comment_text": "sample train zero",
                "toxicity": 0,
                "male": 1,
                "female": 0,
                "LGBTQ": 0,
                "christian": 0,
                "muslim": 0,
                "other_religions": 0,
                "black": 0,
                "white": 1,
                "identity_any": 1,
                "severe_toxicity": 0,
                "obscene": 0,
                "threat": 0,
                "insult": 0,
                "identity_attack": 0,
                "sexual_explicit": 0,
            },
            {
                "raw_index": 1,
                "raw_split": "val",
                "comment_text": "sample val one",
                "toxicity": 1,
                "male": 0,
                "female": 1,
                "LGBTQ": 0,
                "christian": 1,
                "muslim": 0,
                "other_religions": 0,
                "black": 1,
                "white": 0,
                "identity_any": 1,
                "severe_toxicity": 0,
                "obscene": 1,
                "threat": 0,
                "insult": 1,
                "identity_attack": 0,
                "sexual_explicit": 0,
            },
            {
                "raw_index": 2,
                "raw_split": "test",
                "comment_text": "sample test two",
                "toxicity": 0,
                "male": 0,
                "female": 0,
                "LGBTQ": 1,
                "christian": 0,
                "muslim": 1,
                "other_religions": 0,
                "black": 0,
                "white": 1,
                "identity_any": 1,
                "severe_toxicity": 0,
                "obscene": 0,
                "threat": 0,
                "insult": 0,
                "identity_attack": 0,
                "sexual_explicit": 0,
            },
        ],
    )


def test_load_civilcomments_dataset_requires_wilds_dependency():
    config = load_experiment_config("configs/experiments/civilcomments_logistic_baseline.yaml")

    with pytest.raises(DataDependencyError, match="requires the 'wilds' package"):
        materialize_civilcomments(config)


def test_materialize_civilcomments_writes_manifest_with_mocked_wilds(
    temp_artifact_root,
):
    config = load_experiment_config("configs/experiments/civilcomments_logistic_baseline.yaml")

    result = materialize_civilcomments(config, get_dataset_fn=_fake_get_dataset)
    manifest_payload = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    assert result.manifest_path == build_data_manifest_path("civilcomments")
    assert manifest_payload["raw_splits"]["available"] == ["test", "train", "val"]
    assert manifest_payload["project_splits"]["roles"]["id_test"]["selector"] == (
        "deterministic_holdout"
    )
    assert manifest_payload["validation_status"] == "completed"
    assert (result.summary_dir / "data_validation.json").exists()


def test_download_data_command_materializes_with_mocked_loader(temp_artifact_root):
    def fake_materialize(config: dict[str, object], *, download: bool) -> object:
        assert config["dataset_name"] == "civilcomments"
        assert download is True
        return materialize_civilcomments(config, get_dataset_fn=_fake_get_dataset)

    result = run_download_data_command([], materialize_fn=fake_materialize)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert result.status == "materialized"
    assert result.run_dir == temp_artifact_root / "data" / "runs" / metadata["run_id"]
    assert metadata["status"] == "materialized"
    assert metadata["artifact_paths"]["manifest_json"].endswith("civilcomments_manifest.json")
