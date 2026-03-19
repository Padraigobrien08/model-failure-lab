"""Thin dispatch layer behind the public scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from model_failure_lab.models import train_logistic_baseline
from model_failure_lab.tracking import build_run_metadata, write_metadata, write_metrics
from model_failure_lab.tracking.metrics import build_metrics_payload

from .contracts import DispatchResult


def build_scaffold_metrics(config: dict[str, Any]) -> dict[str, Any]:
    """Build placeholder metrics for scaffold-mode runs."""
    eval_config = config.get("eval", {})
    return build_metrics_payload(
        primary_metric={"name": eval_config.get("primary_metric", "accuracy"), "value": None},
        worst_group_metric={
            "name": eval_config.get("worst_group_metric", "accuracy"),
            "value": None,
        },
        robustness_gap={
            "name": eval_config.get("robustness_gap_metric", "accuracy_delta"),
            "value": None,
        },
        calibration_metric={
            "name": eval_config.get("calibration_metric", "ece"),
            "value": None,
        },
    )


def dispatch_baseline(
    *,
    config: dict[str, Any],
    run_dir: Path,
    metadata_path: Path,
    metrics_path: Path,
    preset_name: str,
) -> DispatchResult:
    if config["model_name"] == "logistic_tfidf":
        artifacts = train_logistic_baseline(config, run_dir)
        metrics_path = write_metrics(run_dir, artifacts.metrics_payload)

        existing_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        artifact_paths = dict(existing_metadata.get("artifact_paths", {}))
        artifact_paths["checkpoint"] = str(artifacts.checkpoint_dir)
        artifact_paths["predictions"] = str(artifacts.prediction_path)
        metadata_payload = build_run_metadata(
            run_id=str(config["run_id"]),
            experiment_type="baseline",
            model_name=str(config["model_name"]),
            dataset_name=str(config["dataset_name"]),
            split_details=dict(config["split_details"]),
            random_seed=int(config["seed"]),
            resolved_config=config,
            command=str(existing_metadata.get("command", "")),
            run_dir=run_dir,
            git_commit_hash=existing_metadata.get("git_commit_hash"),
            library_versions=existing_metadata.get("library_versions"),
            artifact_paths=artifact_paths,
            parent_run_id=existing_metadata.get("parent_run_id"),
            notes=str(config.get("notes", "")),
            tags=list(config.get("tags", [])),
            timestamp=existing_metadata.get("timestamp"),
            status="completed",
        )
        metadata_path = write_metadata(run_dir, metadata_payload)
        return DispatchResult(
            status="completed",
            message=f"Baseline completed for {config['model_name']}",
            run_dir=run_dir,
            metadata_path=metadata_path,
            metrics_path=metrics_path,
            preset_name=preset_name,
        )

    return DispatchResult(
        status="scaffold_ready",
        message=f"Baseline scaffold ready for {config['model_name']}",
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=metrics_path,
        preset_name=preset_name,
    )


def dispatch_mitigation(
    *,
    config: dict[str, Any],
    method_name: str,
    parent_run_id: str,
    run_dir: Path,
    metadata_path: Path,
    metrics_path: Path,
    preset_name: str,
) -> DispatchResult:
    return DispatchResult(
        status="scaffold_ready",
        message=f"Mitigation scaffold ready for {method_name} on {config['model_name']}",
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=metrics_path,
        preset_name=preset_name,
        extras={"method_name": method_name, "parent_run_id": parent_run_id},
    )


def dispatch_shift_eval(
    *,
    config: dict[str, Any],
    target_run_id: str,
    run_dir: Path,
    metadata_path: Path,
    metrics_path: Path,
    preset_name: str,
) -> DispatchResult:
    return DispatchResult(
        status="scaffold_ready",
        message=f"Shift-eval scaffold ready for {target_run_id}",
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=metrics_path,
        preset_name=preset_name,
        extras={"target_run_id": target_run_id, "model_name": config["model_name"]},
    )


def dispatch_report(
    *,
    config: dict[str, Any],
    experiment_group: str,
    run_dir: Path,
    metadata_path: Path,
    metrics_path: Path,
    preset_name: str,
) -> DispatchResult:
    return DispatchResult(
        status="scaffold_ready",
        message=f"Report scaffold ready for {experiment_group}",
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=metrics_path,
        preset_name=preset_name,
        extras={"experiment_group": experiment_group, "model_name": config["model_name"]},
    )


def dispatch_data_download(
    *,
    config: dict[str, Any],
    run_dir: Path,
    metadata_path: Path,
    metrics_path: Path,
    preset_name: str,
) -> DispatchResult:
    return DispatchResult(
        status="scaffold_ready",
        message=f"Data download scaffold ready for {config['dataset_name']}",
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=metrics_path,
        preset_name=preset_name,
    )
