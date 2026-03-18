"""Thin dispatch layer behind the public scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
