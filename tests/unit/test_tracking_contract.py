from __future__ import annotations

import json
from datetime import datetime, timezone

from model_failure_lab.tracking.manifest import (
    build_artifact_paths,
    build_run_metadata,
    write_metadata,
)
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
    assert metadata_payload["resolved_config"] == resolved_config
    assert metadata_payload["artifact_paths"] == build_artifact_paths(run_dir)
    assert metadata_payload["git_commit_hash"] == "abc123"
    assert metadata_payload["status"] == "scaffold_ready"

    persisted_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert persisted_payload["artifact_paths"]["metrics_json"].endswith("metrics.json")
    assert persisted_payload["parent_run_id"] is None
