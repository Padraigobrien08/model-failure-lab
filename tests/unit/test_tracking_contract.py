from __future__ import annotations

import json
from datetime import datetime, timezone

from model_failure_lab.tracking.index import append_experiment_index, build_index_entry
from model_failure_lab.tracking.manifest import (
    build_artifact_paths,
    build_run_metadata,
    write_metadata,
)
from model_failure_lab.tracking.metrics import build_metrics_payload, write_metrics
from model_failure_lab.tracking.run_id import generate_run_id
from model_failure_lab.utils.paths import build_baseline_run_dir


def test_generate_run_id_uses_timestamp_prefix_and_suffix():
    run_id = generate_run_id(
        prefix="baseline",
        now=datetime(2026, 3, 18, 22, 30, 0, tzinfo=timezone.utc),
        suffix="AB12",
    )

    assert run_id == "20260318_223000_baseline_ab12"


def test_build_run_metadata_and_write_json(temp_artifact_root):
    run_dir = build_baseline_run_dir(
        model_name="distilbert",
        run_id="20260318_223000_baseline_ab12",
        create=True,
    )
    resolved_config = {
        "experiment_name": "civilcomments_distilbert_baseline",
        "experiment_group": "baselines_v1_1",
        "experiment_type": "baseline",
        "dataset_name": "civilcomments",
        "model_name": "distilbert",
        "split_details": {"train": "train", "id_test": "id_test"},
        "seed": 13,
    }

    metadata_payload = build_run_metadata(
        run_id="20260318_223000_baseline_ab12",
        experiment_type="baseline",
        model_name="distilbert",
        dataset_name="civilcomments",
        split_details={"train": "train", "id_test": "id_test"},
        random_seed=13,
        resolved_config=resolved_config,
        command="python scripts/run_baseline.py --model distilbert",
        run_dir=run_dir,
        git_commit_hash="abc123",
        library_versions={"torch": "2.0.0"},
        notes="bootstrap",
        tags=["baseline", "distilbert"],
        status="scaffold_ready",
    )
    metadata_path = write_metadata(run_dir, metadata_payload)

    assert metadata_payload["run_id"] == "20260318_223000_baseline_ab12"
    assert metadata_payload["timestamp"]
    assert metadata_payload["started_at"] == metadata_payload["timestamp"]
    assert metadata_payload["experiment_group"] == "baselines_v1_1"
    assert metadata_payload["resolved_config"] == resolved_config
    assert metadata_payload["artifact_paths"] == build_artifact_paths(run_dir)
    assert metadata_payload["git_commit_hash"] == "abc123"
    assert metadata_payload["status"] == "scaffold_ready"

    persisted_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert persisted_payload["artifact_paths"]["metrics_json"].endswith("metrics.json")
    assert persisted_payload["parent_run_id"] is None
    assert persisted_payload["started_at"] == persisted_payload["timestamp"]


def test_write_metadata_can_skip_checkpoint_dir(temp_artifact_root):
    run_dir = build_baseline_run_dir(
        model_name="distilbert",
        run_id="20260318_223050_eval_ab12",
        create=True,
    )

    metadata_path = write_metadata(
        run_dir,
        {"run_id": "20260318_223050_eval_ab12"},
        create_checkpoint_dir=False,
    )

    assert metadata_path.exists()
    assert not (run_dir / "checkpoint").exists()


def test_build_metrics_payload_and_write_metrics(temp_artifact_root):
    run_dir = build_baseline_run_dir(
        model_name="logistic_tfidf",
        run_id="20260318_223100_baseline_cd34",
        create=True,
    )
    metrics_payload = build_metrics_payload(
        primary_metric={"name": "accuracy", "value": 0.82},
        worst_group_metric={"name": "accuracy", "value": 0.61},
        robustness_gap={"name": "accuracy_delta", "value": -0.11},
        calibration_metric={"name": "ece", "value": 0.09},
    )
    metrics_path = write_metrics(run_dir, metrics_payload)

    assert metrics_payload["primary_metric"]["name"] == "accuracy"
    assert metrics_payload["worst_group_metric"]["value"] == 0.61
    assert metrics_payload["robustness_gap"]["name"] == "accuracy_delta"
    assert metrics_payload["calibration_metric"]["name"] == "ece"
    persisted_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert persisted_metrics["calibration_metric"]["value"] == 0.09


def test_write_metrics_supports_custom_filename(temp_artifact_root):
    run_dir = build_baseline_run_dir(
        model_name="logistic_tfidf",
        run_id="20260318_223150_eval_cd34",
        create=True,
    )

    metrics_path = write_metrics(
        run_dir,
        {"accuracy": 0.82},
        filename="overall_metrics.json",
    )

    assert metrics_path.name == "overall_metrics.json"
    assert json.loads(metrics_path.read_text(encoding="utf-8"))["accuracy"] == 0.82


def test_experiment_index_appends_lines(temp_artifact_root):
    run_dir = build_baseline_run_dir(
        model_name="distilbert",
        run_id="20260318_223200_baseline_ef56",
        create=True,
    )
    metadata_payload = build_run_metadata(
        run_id="20260318_223200_baseline_ef56",
        experiment_type="baseline",
        model_name="distilbert",
        dataset_name="civilcomments",
        split_details={"train": "train"},
        random_seed=13,
        resolved_config={"model_name": "distilbert", "dataset_name": "civilcomments"},
        command="python scripts/run_baseline.py --model distilbert",
        run_dir=run_dir,
        git_commit_hash="def456",
        library_versions={"torch": "2.0.0"},
        tags=["baseline", "distilbert"],
    )
    metadata_path = write_metadata(run_dir, metadata_payload)
    index_path = temp_artifact_root / "reports" / "summary_tables" / "experiments.jsonl"

    append_experiment_index(
        build_index_entry(metadata_path, metadata_payload),
        index_path=index_path,
    )
    append_experiment_index(
        build_index_entry(metadata_path, metadata_payload),
        index_path=index_path,
    )

    lines = index_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    index_entry = json.loads(lines[0])
    assert index_entry["run_id"] == "20260318_223200_baseline_ef56"
    assert index_entry["experiment_group"] is None
    assert index_entry["seed"] is None
    assert "started_at" in index_entry


def test_build_index_entry_preserves_group_dro_mitigation_metadata(temp_artifact_root):
    run_dir = build_baseline_run_dir(
        model_name="distilbert",
        run_id="20260318_223300_group_dro_cd12",
        create=True,
    )
    metadata_payload = build_run_metadata(
        run_id="20260318_223300_group_dro_cd12",
        experiment_type="mitigation",
        model_name="distilbert",
        dataset_name="civilcomments",
        split_details={
            "train": "train",
            "validation": "validation",
            "id_test": "id_test",
            "ood_test": "ood_test",
        },
        random_seed=13,
        resolved_config={
            "model_name": "distilbert",
            "dataset_name": "civilcomments",
            "seed": 13,
        },
        command="python scripts/run_mitigation.py --method group_dro",
        run_dir=run_dir,
        parent_run_id="parent_13",
        tags=["mitigation", "group_dro", "v1.3_mitigation", "scout", "seed_13"],
        status="completed",
    )
    metadata_payload["mitigation_method"] = "group_dro"
    metadata_path = write_metadata(run_dir, metadata_payload)

    index_entry = build_index_entry(metadata_path, metadata_payload)

    assert index_entry["experiment_type"] == "mitigation"
    assert index_entry["seed"] == 13
    assert index_entry["parent_run_id"] == "parent_13"
    assert index_entry["mitigation_method"] == "group_dro"


def test_build_index_entry_preserves_group_balanced_sampling_mitigation_metadata(
    temp_artifact_root,
):
    run_dir = build_baseline_run_dir(
        model_name="distilbert",
        run_id="20260324_120000_group_balanced_sampling_cd12",
        create=True,
    )
    metadata_payload = build_run_metadata(
        run_id="20260324_120000_group_balanced_sampling_cd12",
        experiment_type="mitigation",
        model_name="distilbert",
        dataset_name="civilcomments",
        split_details={
            "train": "train",
            "validation": "validation",
            "id_test": "id_test",
            "ood_test": "ood_test",
        },
        random_seed=13,
        resolved_config={
            "model_name": "distilbert",
            "dataset_name": "civilcomments",
            "seed": 13,
        },
        command="python scripts/run_mitigation.py --method group_balanced_sampling",
        run_dir=run_dir,
        parent_run_id="parent_13",
        tags=[
            "mitigation",
            "group_balanced_sampling",
            "v1.4_mitigation",
            "scout",
            "seed_13",
        ],
        status="completed",
    )
    metadata_payload["mitigation_method"] = "group_balanced_sampling"
    metadata_path = write_metadata(run_dir, metadata_payload)

    index_entry = build_index_entry(metadata_path, metadata_payload)

    assert index_entry["experiment_type"] == "mitigation"
    assert index_entry["seed"] == 13
    assert index_entry["parent_run_id"] == "parent_13"
    assert index_entry["mitigation_method"] == "group_balanced_sampling"
