"""Evaluation bundle writers and metadata builders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from model_failure_lab.tracking import build_run_metadata
from model_failure_lab.utils.paths import build_evaluation_artifact_paths


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    for column in columns:
        if column not in frame.columns:
            frame[column] = pd.Series(dtype=object)
    frame.loc[:, columns].to_csv(path, index=False)
    return path


def _rows_by_name(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("slice_name")): dict(row) for row in rows}


def _build_overall_metrics_payload(
    split_metric_rows: list[dict[str, Any]],
    *,
    worst_group_summary: dict[str, Any],
    robustness_gaps: dict[str, Any],
) -> dict[str, Any]:
    rows = _rows_by_name(split_metric_rows)
    overall_row = rows.get("overall")
    return {
        "headline_metrics": {
            "accuracy": None if overall_row is None else overall_row.get("accuracy"),
            "macro_f1": None if overall_row is None else overall_row.get("macro_f1"),
            "auroc": None if overall_row is None else overall_row.get("auroc"),
            "worst_group_f1": (
                None
                if worst_group_summary.get("worst_group_f1") is None
                else worst_group_summary["worst_group_f1"]["value"]
            ),
            "worst_group_accuracy": (
                None
                if worst_group_summary.get("worst_group_accuracy") is None
                else worst_group_summary["worst_group_accuracy"]["value"]
            ),
            **robustness_gaps,
        },
        "overall": overall_row,
        "id": rows.get("id"),
        "ood": rows.get("ood"),
        "worst_group": worst_group_summary,
    }


def build_evaluation_metadata(
    *,
    eval_id: str,
    source_run_metadata: dict[str, Any],
    source_metadata_path: Path,
    resolved_config: dict[str, Any],
    command: str,
    eval_dir: Path,
    evaluated_splits: list[str],
    min_group_support: int,
    calibration_bins: int,
    output_tag: str | None = None,
    artifact_paths: dict[str, str] | None = None,
    git_commit_hash: str | None = None,
    library_versions: dict[str, str | None] | None = None,
    timestamp: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Build the persisted metadata payload for one evaluation bundle."""
    metadata = build_run_metadata(
        run_id=eval_id,
        experiment_type="shift_eval",
        model_name=str(source_run_metadata["model_name"]),
        dataset_name=str(source_run_metadata["dataset_name"]),
        split_details=dict(source_run_metadata["split_details"]),
        random_seed=int(resolved_config["seed"]),
        resolved_config=resolved_config,
        command=command,
        run_dir=eval_dir,
        git_commit_hash=git_commit_hash,
        library_versions=library_versions,
        artifact_paths=artifact_paths or build_evaluation_artifact_paths(eval_dir),
        parent_run_id=str(source_run_metadata["run_id"]),
        notes=str(resolved_config.get("notes", "")),
        tags=[*resolved_config.get("tags", []), "shift_eval"],
        timestamp=timestamp,
        status=status,
    )
    metadata["eval_id"] = eval_id
    metadata["source_run_id"] = str(source_run_metadata["run_id"])
    metadata["source_metadata_path"] = str(source_metadata_path)
    metadata["evaluator_version"] = metadata.get("git_commit_hash")
    metadata["min_group_support"] = int(min_group_support)
    metadata["calibration_bins"] = int(calibration_bins)
    metadata["evaluated_splits"] = [str(split) for split in evaluated_splits]
    metadata["output_tag"] = output_tag
    return metadata


def write_evaluation_bundle(
    eval_dir: Path,
    *,
    split_metric_rows: list[dict[str, Any]],
    id_ood_comparison_rows: list[dict[str, Any]],
    subgroup_rows: list[dict[str, Any]],
    worst_group_summary: dict[str, Any],
    robustness_gaps: dict[str, Any],
    calibration_summary_rows: list[dict[str, Any]],
    calibration_bin_rows: list[dict[str, Any]],
    confidence_summary: dict[str, Any],
    diagnostics_payload: dict[str, Any],
) -> dict[str, str]:
    """Persist the full evaluation artifact bundle under one evaluation directory."""
    artifact_paths = build_evaluation_artifact_paths(eval_dir)
    overall_metrics = _build_overall_metrics_payload(
        split_metric_rows,
        worst_group_summary=worst_group_summary,
        robustness_gaps=robustness_gaps,
    )
    _write_json(Path(artifact_paths["overall_metrics_json"]), overall_metrics)
    _write_json(Path(artifact_paths["worst_group_summary_json"]), worst_group_summary)
    _write_json(Path(artifact_paths["confidence_summary_json"]), confidence_summary)
    _write_json(Path(artifact_paths["diagnostics_json"]), diagnostics_payload)

    _write_csv(
        Path(artifact_paths["split_metrics_csv"]),
        split_metric_rows,
        [
            "slice_type",
            "slice_name",
            "sample_count",
            "support",
            "accuracy",
            "macro_f1",
            "precision",
            "recall",
            "binary_f1",
            "auroc",
            "avg_predicted_score",
            "avg_negative_score",
            "mean_confidence",
            "score_std",
            "positive_label_rate",
            "positive_prediction_rate",
            "tn",
            "fp",
            "fn",
            "tp",
        ],
    )
    _write_csv(
        Path(artifact_paths["id_ood_comparison_csv"]),
        id_ood_comparison_rows,
        ["metric", "id_value", "ood_value", "delta", "id_support", "ood_support"],
    )
    _write_csv(
        Path(artifact_paths["subgroup_metrics_csv"]),
        subgroup_rows,
        [
            "grouping_type",
            "group_column",
            "group_name",
            "attribute_name",
            "support",
            "eligible_for_worst_group",
            "accuracy",
            "macro_f1",
            "binary_f1",
            "precision",
            "recall",
            "auroc",
            "avg_predicted_score",
            "mean_confidence",
            "error_rate",
            "minimum_support",
        ],
    )
    _write_csv(
        Path(artifact_paths["subgroup_support_report_csv"]),
        [
            {
                "grouping_type": row["grouping_type"],
                "group_name": row["group_name"],
                "support": row["support"],
                "eligible_for_worst_group": row["eligible_for_worst_group"],
                "minimum_support": row["minimum_support"],
            }
            for row in subgroup_rows
        ],
        [
            "grouping_type",
            "group_name",
            "support",
            "eligible_for_worst_group",
            "minimum_support",
        ],
    )
    _write_csv(
        Path(artifact_paths["calibration_summary_csv"]),
        calibration_summary_rows,
        ["slice_name", "sample_count", "ece", "brier_score", "bin_count", "non_empty_bin_count"],
    )
    _write_csv(
        Path(artifact_paths["calibration_bins_csv"]),
        calibration_bin_rows,
        [
            "slice_name",
            "bin_index",
            "bin_lower",
            "bin_upper",
            "count",
            "avg_confidence",
            "empirical_accuracy",
            "calibration_gap",
        ],
    )
    Path(artifact_paths["plots"]).mkdir(parents=True, exist_ok=True)
    return artifact_paths
