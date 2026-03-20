from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from model_failure_lab.config.loader import load_experiment_config
from model_failure_lab.data import (
    DataDependencyError,
    materialize_civilcomments,
    prepare_civilcomments_runtime_dataset,
    read_data_manifest,
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


def test_read_data_manifest_returns_none_when_missing(temp_artifact_root):
    assert read_data_manifest("civilcomments") is None


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


def test_prepare_civilcomments_runtime_dataset_reuses_completed_manifest(
    temp_artifact_root,
    monkeypatch,
):
    config = load_experiment_config("configs/experiments/civilcomments_logistic_baseline.yaml")
    materialize_civilcomments(config, get_dataset_fn=_fake_get_dataset)

    def fail_materialize(*_args, **_kwargs):
        raise AssertionError("existing manifest should be reused")

    monkeypatch.setattr(
        "model_failure_lab.data.materialization.materialize_civilcomments",
        fail_materialize,
    )

    result = prepare_civilcomments_runtime_dataset(
        config,
        get_dataset_fn=_fake_get_dataset,
    )

    assert result.manifest_path == build_data_manifest_path("civilcomments")
    assert result.summary_dir == build_data_summary_dir()
    assert result.manifest_payload["validation_status"] == "completed"
    assert len(result.dataset.samples) == 3
    assert read_data_manifest("civilcomments")["dataset_name"] == "civilcomments"


def test_prepare_civilcomments_runtime_dataset_materializes_when_manifest_missing(
    temp_artifact_root,
    monkeypatch,
):
    config = load_experiment_config("configs/experiments/civilcomments_logistic_baseline.yaml")
    call_count = 0

    def fake_materialize(runtime_config: dict[str, object], *, download: bool, get_dataset_fn=None):
        nonlocal call_count
        call_count += 1
        assert runtime_config["dataset_name"] == "civilcomments"
        assert download is True
        return materialize_civilcomments(
            runtime_config,
            download=download,
            get_dataset_fn=get_dataset_fn or _fake_get_dataset,
        )

    monkeypatch.setattr(
        "model_failure_lab.data.materialization.materialize_civilcomments",
        fake_materialize,
    )

    result = prepare_civilcomments_runtime_dataset(
        config,
        get_dataset_fn=_fake_get_dataset,
    )

    assert call_count == 1
    assert result.manifest_path.exists()
    assert len(result.dataset.samples) == 3


def test_prepare_civilcomments_runtime_dataset_rejects_incompatible_split_policy(
    temp_artifact_root,
):
    config = load_experiment_config("configs/experiments/civilcomments_logistic_baseline.yaml")
    manifest_result = materialize_civilcomments(config, get_dataset_fn=_fake_get_dataset)
    manifest_payload = json.loads(manifest_result.manifest_path.read_text(encoding="utf-8"))
    manifest_payload["project_splits"]["roles"]["validation"]["raw_split"] = "train"
    manifest_result.manifest_path.write_text(
        json.dumps(manifest_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="materialization contract"):
        prepare_civilcomments_runtime_dataset(
            config,
            get_dataset_fn=_fake_get_dataset,
            materialize_if_missing=False,
        )


def test_prepare_civilcomments_runtime_dataset_rejects_missing_summary_artifact(
    temp_artifact_root,
):
    config = load_experiment_config("configs/experiments/civilcomments_logistic_baseline.yaml")
    manifest_result = materialize_civilcomments(config, get_dataset_fn=_fake_get_dataset)
    manifest_payload = json.loads(manifest_result.manifest_path.read_text(encoding="utf-8"))
    split_counts_path = Path(manifest_payload["summary_artifacts"]["split_counts_csv"])
    split_counts_path.unlink()

    with pytest.raises(ValueError, match="materialization contract"):
        prepare_civilcomments_runtime_dataset(
            config,
            get_dataset_fn=_fake_get_dataset,
            materialize_if_missing=False,
        )


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
