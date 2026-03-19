"""Thin dispatch layer behind the public scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from model_failure_lab.evaluation import (
    build_confidence_summary,
    build_diagnostics_payload,
    build_id_ood_comparison,
    build_split_metrics_rows,
    build_worst_group_summary,
    compute_calibration_summary,
    compute_robustness_gaps,
    compute_subgroup_metrics,
    load_saved_predictions,
)
from model_failure_lab.evaluation.bundle import (
    build_evaluation_metadata,
    write_evaluation_bundle,
)
from model_failure_lab.models import train_distilbert_baseline, train_logistic_baseline
from model_failure_lab.tracking import (
    build_artifact_paths,
    build_run_metadata,
    write_metadata,
    write_metrics,
)
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
        artifact_paths = build_artifact_paths(run_dir, prediction_splits=["train", "validation"])
        artifact_paths["checkpoint"] = str(artifacts.checkpoint_dir)
        artifact_paths["predictions"] = {
            split: str(path) for split, path in artifacts.prediction_paths.items()
        }
        artifact_paths["selected_checkpoint"] = str(artifacts.model_path)
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

    if config["model_name"] == "distilbert":
        artifacts = train_distilbert_baseline(config, run_dir)
        metrics_path = write_metrics(run_dir, artifacts.metrics_payload)

        existing_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        artifact_paths = build_artifact_paths(run_dir, prediction_splits=["train", "validation"])
        artifact_paths["checkpoint"] = str(artifacts.checkpoint_dir)
        artifact_paths["predictions"] = {
            split: str(path) for split, path in artifacts.prediction_paths.items()
        }
        artifact_paths["selected_checkpoint"] = str(artifacts.checkpoint_path)
        artifact_paths["training_history_json"] = str(artifacts.history_path)
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
    source_metadata_path: Path,
    run_dir: Path,
    metadata_path: Path,
    metrics_path: Path,
    preset_name: str,
) -> DispatchResult:
    source_metadata = json.loads(source_metadata_path.read_text(encoding="utf-8"))
    _, prediction_frame = load_saved_predictions(
        source_metadata,
        splits=config.get("eval", {}).get("requested_splits"),
    )
    split_metric_rows = build_split_metrics_rows(prediction_frame)
    group_fields = (
        source_metadata.get("resolved_config", {}).get("data", {}).get("group_fields", [])
    )
    attribute_columns = [
        str(field) for field in group_fields if str(field) in prediction_frame.columns
    ]
    subgroup_rows = compute_subgroup_metrics(
        prediction_frame,
        min_support=int(config["eval"]["min_group_support"]),
        attribute_columns=attribute_columns or None,
    )
    worst_group_summary = build_worst_group_summary(
        subgroup_rows,
        min_support=int(config["eval"]["min_group_support"]),
    )
    id_ood_comparison_rows = build_id_ood_comparison(split_metric_rows)
    robustness_gaps = compute_robustness_gaps(split_metric_rows)
    calibration = compute_calibration_summary(
        prediction_frame,
        n_bins=int(config["eval"]["calibration_bins"]),
        strategy=str(config["eval"].get("calibration_strategy", "uniform")),
    )
    confidence_summary = build_confidence_summary(
        prediction_frame,
        bins=int(config["eval"]["calibration_bins"]),
    )
    diagnostics_payload = build_diagnostics_payload(prediction_frame)
    artifact_paths = write_evaluation_bundle(
        run_dir,
        split_metric_rows=split_metric_rows,
        id_ood_comparison_rows=id_ood_comparison_rows,
        subgroup_rows=subgroup_rows,
        worst_group_summary=worst_group_summary,
        robustness_gaps=robustness_gaps,
        calibration_summary_rows=calibration["summary_rows"],
        calibration_bin_rows=calibration["bin_rows"],
        confidence_summary=confidence_summary,
        diagnostics_payload=diagnostics_payload,
    )
    existing_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    evaluated_splits = [
        str(split) for split in prediction_frame["split"].dropna().astype(str).unique()
    ]
    metadata_payload = build_evaluation_metadata(
        eval_id=str(config["run_id"]),
        source_run_metadata=source_metadata,
        source_metadata_path=source_metadata_path,
        resolved_config=config,
        command=str(existing_metadata.get("command", "")),
        eval_dir=run_dir,
        evaluated_splits=evaluated_splits,
        min_group_support=int(config["eval"]["min_group_support"]),
        calibration_bins=int(config["eval"]["calibration_bins"]),
        output_tag=config["eval"].get("output_tag"),
        artifact_paths=artifact_paths,
        git_commit_hash=existing_metadata.get("git_commit_hash"),
        library_versions=existing_metadata.get("library_versions"),
        timestamp=existing_metadata.get("timestamp"),
        status="completed",
    )
    metadata_path = write_metadata(run_dir, metadata_payload, create_checkpoint_dir=False)
    return DispatchResult(
        status="completed",
        message=f"Shift evaluation completed for {target_run_id}",
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=Path(artifact_paths["overall_metrics_json"]),
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
