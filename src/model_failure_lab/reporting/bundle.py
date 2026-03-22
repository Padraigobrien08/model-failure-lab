"""Report bundle writers and metadata builders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from model_failure_lab.tracking import build_run_metadata
from model_failure_lab.utils.paths import (
    build_perturbation_report_artifact_paths,
    build_report_artifact_paths,
    build_stability_report_artifact_paths,
)


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_csv(path: Path, frame: pd.DataFrame) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path


def _frame_records(frame: pd.DataFrame | None) -> list[dict[str, Any]]:
    if frame is None or frame.empty:
        return []
    sanitized = frame.where(pd.notna(frame), None)
    return list(sanitized.to_dict(orient="records"))


def build_report_data_payload(
    *,
    report_summary: dict[str, Any],
    comparison_table: pd.DataFrame,
    mitigation_comparison_table: pd.DataFrame | None,
    subgroup_table: pd.DataFrame,
    calibration_table: pd.DataFrame,
) -> dict[str, Any]:
    """Build a structured report payload for future UI consumers."""
    return {
        "report_summary": report_summary,
        "mitigation_verdict_counts": report_summary.get("mitigation_verdict_counts"),
        "seeded_interpretation": report_summary.get("seeded_interpretation"),
        "mitigation_method_summaries": report_summary.get("mitigation_method_summaries"),
        "comparison_table": _frame_records(comparison_table),
        "mitigation_comparison_table": _frame_records(mitigation_comparison_table),
        "subgroup_table": _frame_records(subgroup_table),
        "calibration_table": _frame_records(calibration_table),
    }


def build_perturbation_report_data_payload(
    *,
    report_summary: dict[str, Any],
    suite_summary: pd.DataFrame,
    family_summary: pd.DataFrame,
    severity_summary: pd.DataFrame,
    family_severity_matrix: pd.DataFrame,
) -> dict[str, Any]:
    """Build a structured perturbation report payload for future UI consumers."""
    return {
        "report_summary": report_summary,
        "suite_summary": _frame_records(suite_summary),
        "family_summary": _frame_records(family_summary),
        "severity_summary": _frame_records(severity_summary),
        "family_severity_matrix": _frame_records(family_severity_matrix),
    }


def build_stability_report_data_payload(
    *,
    stability_summary: dict[str, Any],
    baseline_stability_table: pd.DataFrame,
    temperature_scaling_deltas: pd.DataFrame,
    reweighting_deltas: pd.DataFrame,
) -> dict[str, Any]:
    """Build a structured seeded stability payload for future UI consumers."""
    return {
        "stability_summary": stability_summary,
        "baseline_stability_table": _frame_records(baseline_stability_table),
        "temperature_scaling_deltas": _frame_records(temperature_scaling_deltas),
        "reweighting_deltas": _frame_records(reweighting_deltas),
    }


def build_report_metadata(
    *,
    report_id: str,
    report_scope: str,
    selection_mode: str,
    source_eval_ids: list[str],
    resolved_config: dict[str, Any],
    command: str,
    run_dir: Path,
    dataset_name: str,
    split_details: dict[str, str],
    artifact_paths: dict[str, str] | None = None,
    git_commit_hash: str | None = None,
    library_versions: dict[str, str | None] | None = None,
    timestamp: str | None = None,
    status: str | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
    duration_seconds: float | None = None,
) -> dict[str, Any]:
    """Build persisted metadata for a completed report package."""
    metadata = build_run_metadata(
        run_id=report_id,
        experiment_type="report",
        model_name="comparison_report",
        dataset_name=dataset_name,
        split_details=split_details,
        random_seed=int(resolved_config["seed"]),
        resolved_config=resolved_config,
        command=command,
        run_dir=run_dir,
        git_commit_hash=git_commit_hash,
        library_versions=library_versions,
        artifact_paths=artifact_paths or build_report_artifact_paths(run_dir),
        notes=str(resolved_config.get("notes", "")),
        tags=[*resolved_config.get("tags", []), "report"],
        timestamp=timestamp,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=duration_seconds,
    )
    report_config = resolved_config.get("report", {})
    metadata["report_id"] = report_id
    metadata["report_scope"] = report_scope
    metadata["selection_mode"] = selection_mode
    metadata["source_eval_ids"] = list(source_eval_ids)
    metadata["report_name"] = report_config.get("report_name")
    metadata["output_format"] = report_config.get("output_format", "markdown")
    metadata["top_k_subgroups"] = int(report_config.get("top_k_subgroups", 5))
    metadata["min_group_support"] = int(resolved_config.get("eval", {}).get("min_group_support", 0))
    return metadata


def build_perturbation_report_metadata(
    *,
    report_id: str,
    report_scope: str,
    selection_mode: str,
    source_eval_ids: list[str],
    resolved_config: dict[str, Any],
    command: str,
    run_dir: Path,
    dataset_name: str,
    split_details: dict[str, str],
    artifact_paths: dict[str, str] | None = None,
    git_commit_hash: str | None = None,
    library_versions: dict[str, str | None] | None = None,
    timestamp: str | None = None,
    status: str | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
    duration_seconds: float | None = None,
) -> dict[str, Any]:
    """Build persisted metadata for a completed perturbation report package."""
    metadata = build_run_metadata(
        run_id=report_id,
        experiment_type="perturbation_report",
        model_name="perturbation_report",
        dataset_name=dataset_name,
        split_details=split_details,
        random_seed=int(resolved_config["seed"]),
        resolved_config=resolved_config,
        command=command,
        run_dir=run_dir,
        git_commit_hash=git_commit_hash,
        library_versions=library_versions,
        artifact_paths=artifact_paths or build_perturbation_report_artifact_paths(run_dir),
        notes=str(resolved_config.get("notes", "")),
        tags=[*resolved_config.get("tags", []), "perturbation_report"],
        timestamp=timestamp,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=duration_seconds,
    )
    report_config = resolved_config.get("report", {})
    metadata["report_id"] = report_id
    metadata["report_scope"] = report_scope
    metadata["selection_mode"] = selection_mode
    metadata["source_eval_ids"] = list(source_eval_ids)
    metadata["report_name"] = report_config.get("report_name")
    metadata["output_format"] = report_config.get("output_format", "markdown")
    return metadata


def build_stability_report_metadata(
    *,
    report_id: str,
    report_scope: str,
    selection_mode: str,
    source_eval_ids: list[str],
    cohort_eval_ids: dict[str, list[str]],
    resolved_config: dict[str, Any],
    command: str,
    run_dir: Path,
    dataset_name: str,
    split_details: dict[str, str],
    artifact_paths: dict[str, str] | None = None,
    git_commit_hash: str | None = None,
    library_versions: dict[str, str | None] | None = None,
    timestamp: str | None = None,
    status: str | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
    duration_seconds: float | None = None,
) -> dict[str, Any]:
    """Build persisted metadata for a seeded stability report package."""
    metadata = build_run_metadata(
        run_id=report_id,
        experiment_type="stability_report",
        model_name="stability_report",
        dataset_name=dataset_name,
        split_details=split_details,
        random_seed=int(resolved_config["seed"]),
        resolved_config=resolved_config,
        command=command,
        run_dir=run_dir,
        git_commit_hash=git_commit_hash,
        library_versions=library_versions,
        artifact_paths=artifact_paths or build_stability_report_artifact_paths(run_dir),
        notes=str(resolved_config.get("notes", "")),
        tags=[*resolved_config.get("tags", []), "stability_report"],
        timestamp=timestamp,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=duration_seconds,
    )
    report_config = resolved_config.get("report", {})
    metadata["report_id"] = report_id
    metadata["report_scope"] = report_scope
    metadata["selection_mode"] = selection_mode
    metadata["source_eval_ids"] = list(source_eval_ids)
    metadata["cohort_eval_ids"] = {str(key): list(value) for key, value in cohort_eval_ids.items()}
    metadata["report_name"] = report_config.get("report_name")
    metadata["output_format"] = report_config.get("output_format", "markdown")
    return metadata


def write_report_bundle(
    run_dir: Path,
    *,
    markdown: str,
    report_summary: dict[str, Any],
    figures: dict[str, Figure],
    comparison_table: pd.DataFrame,
    mitigation_comparison_table: pd.DataFrame | None = None,
    subgroup_table: pd.DataFrame,
    calibration_table: pd.DataFrame,
) -> dict[str, str]:
    """Persist the full Phase 5 report package."""
    artifact_paths = build_report_artifact_paths(run_dir)
    report_data = build_report_data_payload(
        report_summary=report_summary,
        comparison_table=comparison_table,
        mitigation_comparison_table=mitigation_comparison_table,
        subgroup_table=subgroup_table,
        calibration_table=calibration_table,
    )
    _write_json(Path(artifact_paths["report_summary_json"]), report_summary)
    _write_json(Path(artifact_paths["report_data_json"]), report_data)
    Path(artifact_paths["figures_dir"]).mkdir(parents=True, exist_ok=True)
    Path(artifact_paths["tables_dir"]).mkdir(parents=True, exist_ok=True)
    Path(artifact_paths["report_markdown"]).write_text(markdown, encoding="utf-8")
    _write_csv(Path(artifact_paths["comparison_table_csv"]), comparison_table)
    _write_csv(
        Path(artifact_paths["mitigation_comparison_table_csv"]),
        mitigation_comparison_table
        if mitigation_comparison_table is not None
        else pd.DataFrame(),
    )
    _write_csv(Path(artifact_paths["subgroup_table_csv"]), subgroup_table)
    _write_csv(Path(artifact_paths["calibration_table_csv"]), calibration_table)

    for key, figure in figures.items():
        output_path = Path(artifact_paths[f"{key}_png"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(output_path, dpi=200, bbox_inches="tight")
        plt.close(figure)

    return artifact_paths


def write_perturbation_report_bundle(
    run_dir: Path,
    *,
    markdown: str,
    report_summary: dict[str, Any],
    figures: dict[str, Figure],
    suite_summary: pd.DataFrame,
    family_summary: pd.DataFrame,
    severity_summary: pd.DataFrame,
    family_severity_matrix: pd.DataFrame,
) -> dict[str, str]:
    """Persist the full perturbation report package."""
    artifact_paths = build_perturbation_report_artifact_paths(run_dir)
    report_data = build_perturbation_report_data_payload(
        report_summary=report_summary,
        suite_summary=suite_summary,
        family_summary=family_summary,
        severity_summary=severity_summary,
        family_severity_matrix=family_severity_matrix,
    )
    _write_json(Path(artifact_paths["report_summary_json"]), report_summary)
    _write_json(Path(artifact_paths["report_data_json"]), report_data)
    Path(artifact_paths["figures_dir"]).mkdir(parents=True, exist_ok=True)
    Path(artifact_paths["tables_dir"]).mkdir(parents=True, exist_ok=True)
    Path(artifact_paths["report_markdown"]).write_text(markdown, encoding="utf-8")
    _write_csv(Path(artifact_paths["suite_summary_csv"]), suite_summary)
    _write_csv(Path(artifact_paths["family_summary_csv"]), family_summary)
    _write_csv(Path(artifact_paths["severity_summary_csv"]), severity_summary)
    _write_csv(Path(artifact_paths["family_severity_matrix_csv"]), family_severity_matrix)

    for key, figure in figures.items():
        output_path = Path(artifact_paths[f"{key}_png"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(output_path, dpi=200, bbox_inches="tight")
        plt.close(figure)

    return artifact_paths


def write_stability_report_bundle(
    run_dir: Path,
    *,
    markdown: str,
    stability_summary: dict[str, Any],
    baseline_stability_table: pd.DataFrame,
    temperature_scaling_deltas: pd.DataFrame,
    reweighting_deltas: pd.DataFrame,
) -> dict[str, str]:
    """Persist the full seeded stability report package."""
    artifact_paths = build_stability_report_artifact_paths(run_dir)
    report_data = build_stability_report_data_payload(
        stability_summary=stability_summary,
        baseline_stability_table=baseline_stability_table,
        temperature_scaling_deltas=temperature_scaling_deltas,
        reweighting_deltas=reweighting_deltas,
    )
    _write_json(Path(artifact_paths["stability_summary_json"]), stability_summary)
    _write_json(Path(artifact_paths["report_data_json"]), report_data)
    Path(artifact_paths["tables_dir"]).mkdir(parents=True, exist_ok=True)
    Path(artifact_paths["report_markdown"]).write_text(markdown, encoding="utf-8")
    _write_csv(Path(artifact_paths["baseline_stability_csv"]), baseline_stability_table)
    _write_csv(
        Path(artifact_paths["temperature_scaling_deltas_csv"]),
        temperature_scaling_deltas,
    )
    _write_csv(Path(artifact_paths["reweighting_deltas_csv"]), reweighting_deltas)
    return artifact_paths
