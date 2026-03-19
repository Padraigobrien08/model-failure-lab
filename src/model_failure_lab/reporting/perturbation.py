"""Dedicated discovery and table helpers for perturbation reports."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .discovery import PerturbationReportCandidate, load_perturbation_candidates
from .selection import report_label


def _schema_version(metadata: dict[str, Any]) -> str:
    return str(metadata.get("perturbation_schema_version", "unknown"))


def _family_signature(metadata: dict[str, Any]) -> tuple[str, ...]:
    perturbation_config = metadata.get("resolved_config", {}).get("perturbation", {})
    families = perturbation_config.get("families", [])
    return tuple(str(item) for item in families)


def _severity_signature(metadata: dict[str, Any]) -> tuple[str, ...]:
    perturbation_config = metadata.get("resolved_config", {}).get("perturbation", {})
    severities = perturbation_config.get("severities", [])
    return tuple(str(item) for item in severities)


def validate_perturbation_report_candidates(
    candidates: list[PerturbationReportCandidate],
) -> None:
    """Ensure saved perturbation bundles are comparable in one report."""
    if not candidates:
        raise ValueError("No perturbation report candidates were selected")

    dataset_names = {str(candidate.metadata.get("dataset_name")) for candidate in candidates}
    if len(dataset_names) != 1:
        raise ValueError("Selected perturbation bundles are not comparable: dataset mismatch")

    source_splits = {str(candidate.metadata.get("source_split")) for candidate in candidates}
    if len(source_splits) != 1:
        raise ValueError("Selected perturbation bundles are not comparable: source split mismatch")

    schema_versions = {_schema_version(candidate.metadata) for candidate in candidates}
    if len(schema_versions) != 1:
        raise ValueError(
            "Selected perturbation bundles are not comparable: perturbation schema mismatch"
        )

    family_signatures = {_family_signature(candidate.metadata) for candidate in candidates}
    if len(family_signatures) != 1:
        raise ValueError("Selected perturbation bundles are not comparable: family-set mismatch")

    severity_signatures = {_severity_signature(candidate.metadata) for candidate in candidates}
    if len(severity_signatures) != 1:
        raise ValueError(
            "Selected perturbation bundles are not comparable: severity-set mismatch"
        )


def load_perturbation_report_inputs(
    *,
    experiment_group: str | None = None,
    eval_ids: list[str] | None = None,
) -> list[PerturbationReportCandidate]:
    """Load deterministically ordered perturbation report candidates."""
    candidates = load_perturbation_candidates(
        experiment_group=experiment_group,
        eval_ids=eval_ids,
    )
    validate_perturbation_report_candidates(candidates)
    return sorted(
        candidates,
        key=lambda candidate: (
            str(candidate.metadata.get("model_name", "")),
            str(candidate.metadata.get("source_run_id", "")),
            candidate.eval_id,
        ),
    )


def build_perturbation_report_tables(
    candidates: list[PerturbationReportCandidate],
) -> dict[str, pd.DataFrame]:
    """Build labeled tables for the perturbation report package."""
    suite_frames: list[pd.DataFrame] = []
    family_frames: list[pd.DataFrame] = []
    severity_frames: list[pd.DataFrame] = []
    matrix_frames: list[pd.DataFrame] = []

    for candidate in candidates:
        label = report_label(candidate)
        for source_frame, target_frames in [
            (candidate.suite_summary, suite_frames),
            (candidate.family_summary, family_frames),
            (candidate.severity_summary, severity_frames),
            (candidate.family_severity_matrix, matrix_frames),
        ]:
            prepared = source_frame.copy()
            if prepared.empty:
                continue
            prepared.insert(0, "label", label)
            prepared.insert(1, "perturbation_eval_id", candidate.eval_id)
            target_frames.append(prepared)

    return {
        "suite_summary": (
            pd.concat(suite_frames, ignore_index=True) if suite_frames else pd.DataFrame()
        ),
        "family_summary": (
            pd.concat(family_frames, ignore_index=True) if family_frames else pd.DataFrame()
        ),
        "severity_summary": (
            pd.concat(severity_frames, ignore_index=True) if severity_frames else pd.DataFrame()
        ),
        "family_severity_matrix": (
            pd.concat(matrix_frames, ignore_index=True) if matrix_frames else pd.DataFrame()
        ),
    }
