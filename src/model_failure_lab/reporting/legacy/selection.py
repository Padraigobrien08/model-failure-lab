"""Selection and comparability gates for report candidates."""

from __future__ import annotations

import json
from typing import Any

from .discovery import ReportCandidate


def _task_signature(metadata: dict[str, Any]) -> str:
    resolved_config = metadata.get("resolved_config", {})
    if not isinstance(resolved_config, dict):
        return "unknown"
    data_config = resolved_config.get("data", {})
    if not isinstance(data_config, dict):
        return "unknown"
    label_field = str(data_config.get("label_field", "unknown"))
    text_field = str(data_config.get("text_field", "unknown"))
    return f"{label_field}:{text_field}"


def _schema_version(metadata: dict[str, Any]) -> str:
    resolved_config = metadata.get("resolved_config", {})
    eval_config = resolved_config.get("eval", {}) if isinstance(resolved_config, dict) else {}
    schema_payload = {
        "experiment_type": metadata.get("experiment_type"),
        "primary_metric": eval_config.get("primary_metric"),
        "tracked_metrics": sorted(str(metric) for metric in eval_config.get("tracked_metrics", [])),
        "calibration_metric": eval_config.get("calibration_metric"),
        "calibration_strategy": eval_config.get("calibration_strategy"),
        "calibration_bins": metadata.get("calibration_bins"),
        "min_group_support": metadata.get("min_group_support"),
        "robustness_gap_metric": eval_config.get("robustness_gap_metric"),
        "worst_group_metric": eval_config.get("worst_group_metric"),
        "evaluated_splits": sorted(str(split) for split in metadata.get("evaluated_splits", [])),
    }
    if any(value not in (None, [], {}) for value in schema_payload.values()):
        return json.dumps(schema_payload, sort_keys=True)

    explicit_schema_version = metadata.get("evaluation_schema_version")
    if explicit_schema_version is not None:
        return str(explicit_schema_version)

    return str(
        metadata.get("evaluator_version")
        or metadata.get("git_commit_hash")
        or "unknown"
    )


def _subgroup_policy_signature(metadata: dict[str, Any]) -> str:
    resolved_config = metadata.get("resolved_config", {})
    data_config = resolved_config.get("data", {}) if isinstance(resolved_config, dict) else {}
    group_fields = data_config.get("group_fields", []) if isinstance(data_config, dict) else []
    normalized_group_fields = ",".join(sorted(str(field) for field in group_fields))
    return f"{normalized_group_fields}|{metadata.get('min_group_support', 'unknown')}"


def validate_report_candidates(candidates: list[ReportCandidate]) -> None:
    """Ensure selected report candidates can be compared in one report."""
    if not candidates:
        raise ValueError("No report candidates were selected")

    dataset_names = {str(candidate.metadata.get("dataset_name")) for candidate in candidates}
    if len(dataset_names) != 1:
        raise ValueError("Selected evaluation bundles are not comparable: dataset mismatch")

    task_signatures = {_task_signature(candidate.metadata) for candidate in candidates}
    if len(task_signatures) != 1:
        raise ValueError("Selected evaluation bundles are not comparable: task mismatch")

    schema_versions = {_schema_version(candidate.metadata) for candidate in candidates}
    if len(schema_versions) != 1:
        raise ValueError(
            "Selected evaluation bundles are not comparable: evaluation schema mismatch"
        )

    subgroup_policies = {_subgroup_policy_signature(candidate.metadata) for candidate in candidates}
    if len(subgroup_policies) != 1:
        raise ValueError(
            "Selected evaluation bundles are not comparable: subgroup policy mismatch"
        )


def select_report_candidates(candidates: list[ReportCandidate]) -> list[ReportCandidate]:
    """Return deterministically ordered report candidates after validation."""
    validate_report_candidates(candidates)
    return sorted(
        candidates,
        key=lambda candidate: (
            str(candidate.metadata.get("model_name", "")),
            str(candidate.metadata.get("source_run_id", "")),
            candidate.eval_id,
        ),
    )


def report_label(candidate: ReportCandidate) -> str:
    """Return the compact label used across report tables and figures."""
    model_name = str(candidate.metadata.get("model_name", candidate.eval_id))
    source_run_id = str(candidate.metadata.get("source_run_id", candidate.eval_id))
    return f"{model_name}:{source_run_id}"
