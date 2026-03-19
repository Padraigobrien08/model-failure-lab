from __future__ import annotations

import json

import pytest

from model_failure_lab.config.loader import load_experiment_config
from model_failure_lab.mitigations import (
    build_inherited_mitigation_config,
    load_parent_run_context,
    validate_distilbert_parent_run,
)
from model_failure_lab.runners.contracts import DispatchResult
from model_failure_lab.tracking import build_run_metadata, write_metadata
from model_failure_lab.utils.paths import build_baseline_run_dir
from scripts.run_mitigation import run_command as run_mitigation_command


def _write_parent_metadata(
    *,
    run_id: str,
    model_name: str = "distilbert",
    experiment_type: str = "baseline",
) -> str:
    resolved_config = load_experiment_config(
        "configs/experiments/civilcomments_distilbert_baseline.yaml"
    )
    resolved_config["run_id"] = run_id
    resolved_config["experiment_type"] = experiment_type
    resolved_config["model_name"] = model_name
    resolved_config["model"]["model_name"] = model_name

    run_dir = build_baseline_run_dir(model_name, run_id, create=True)
    metadata_payload = build_run_metadata(
        run_id=run_id,
        experiment_type=experiment_type,
        model_name=model_name,
        dataset_name=resolved_config["dataset_name"],
        split_details=resolved_config["split_details"],
        random_seed=int(resolved_config["seed"]),
        resolved_config=resolved_config,
        command="python scripts/run_baseline.py --model distilbert",
        run_dir=run_dir,
        notes="parent fixture",
        tags=[experiment_type, model_name],
        status="completed",
    )
    write_metadata(run_dir, metadata_payload)
    return run_id


def test_reweighting_preset_contains_mitigation_payload():
    config = load_experiment_config(
        "configs/experiments/civilcomments_distilbert_reweighting.yaml"
    )

    assert config["mitigation"]["method"] == "reweighting"
    assert config["mitigation"]["parent_model_name"] == "distilbert"
    assert config["mitigation"]["reweighting"]["grouping_field"] == "group_id"
    assert config["mitigation"]["reweighting"]["strategy"] == "inverse_sqrt_frequency"
    assert (
        config["mitigation"]["comparison_tolerances"]["ece_neutral_tolerance"] == 0.005
    )


def test_validate_distilbert_parent_run_rejects_non_baseline_parent(temp_artifact_root):
    parent_run_id = _write_parent_metadata(
        run_id="not_a_baseline_parent",
        experiment_type="mitigation",
    )

    with pytest.raises(ValueError, match="must be a baseline run"):
        validate_distilbert_parent_run(load_parent_run_context(parent_run_id))


def test_validate_distilbert_parent_run_rejects_non_distilbert_parent(temp_artifact_root):
    parent_run_id = _write_parent_metadata(
        run_id="logistic_parent",
        model_name="logistic_tfidf",
    )

    with pytest.raises(ValueError, match="only supports DistilBERT parent baselines"):
        validate_distilbert_parent_run(load_parent_run_context(parent_run_id))


def test_build_inherited_mitigation_config_clones_parent_resolved_config(temp_artifact_root):
    parent_run_id = _write_parent_metadata(run_id="distilbert_parent")
    parent_context = load_parent_run_context(parent_run_id)
    mitigation_preset = load_experiment_config(
        "configs/experiments/civilcomments_distilbert_reweighting.yaml"
    )
    mitigation_preset["run_id"] = "reweighting_child"

    child_config = build_inherited_mitigation_config(parent_context, mitigation_preset)

    assert child_config["experiment_type"] == "mitigation"
    assert child_config["parent_run_id"] == parent_run_id
    assert child_config["parent_model_name"] == "distilbert"
    assert child_config["mitigation_method"] == "reweighting"
    assert child_config["mitigation_config"]["reweighting"]["max_weight"] == 5.0
    assert child_config["train"] == parent_context["resolved_config"]["train"]
    assert child_config["eval"] == parent_context["resolved_config"]["eval"]
    assert child_config["preset_path"].endswith("civilcomments_distilbert_baseline.yaml")


def test_run_mitigation_reweighting_uses_inherited_parent_config(
    temp_artifact_root,
    monkeypatch,
):
    parent_run_id = _write_parent_metadata(run_id="distilbert_parent_runtime")
    captured: dict[str, object] = {}

    def fake_dispatch(**kwargs):
        captured.update(kwargs)
        return DispatchResult(
            status="scaffold_ready",
            message="stubbed reweighting dispatch",
            run_dir=kwargs["run_dir"],
            metadata_path=kwargs["metadata_path"],
            metrics_path=kwargs["metrics_path"],
            preset_name=kwargs["preset_name"],
        )

    monkeypatch.setattr("scripts.run_mitigation.dispatch_mitigation", fake_dispatch)

    result = run_mitigation_command(
        [
            "--run-id",
            parent_run_id,
            "--method",
            "reweighting",
            "--output-run-id",
            "reweighting_child_runtime",
        ]
    )
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    dispatched_config = captured["config"]

    assert result.run_dir.as_posix().endswith(
        "artifacts/mitigations/reweighting/distilbert/reweighting_child_runtime"
    )
    assert dispatched_config["parent_run_id"] == parent_run_id
    assert dispatched_config["parent_model_name"] == "distilbert"
    assert dispatched_config["mitigation_method"] == "reweighting"
    assert dispatched_config["mitigation_config"]["reweighting"]["grouping_field"] == "group_id"
    assert dispatched_config["preset_path"].endswith("civilcomments_distilbert_baseline.yaml")
    assert metadata["resolved_config"]["mitigation_method"] == "reweighting"
    assert metadata["resolved_config"]["parent_model_name"] == "distilbert"
    assert metadata["parent_run_id"] == parent_run_id
