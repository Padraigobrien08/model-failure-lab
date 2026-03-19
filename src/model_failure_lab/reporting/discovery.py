"""Discovery and loading helpers for saved evaluation bundles."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from model_failure_lab.utils.paths import artifact_root


@dataclass(slots=True)
class ReportCandidate:
    """Loaded evaluation bundle ready for report selection and rendering."""

    eval_id: str
    metadata_path: Path
    metadata: dict[str, Any]
    overall_metrics: dict[str, Any]
    split_metrics: pd.DataFrame
    id_ood_comparison: pd.DataFrame
    subgroup_metrics: pd.DataFrame
    worst_group_summary: dict[str, Any]
    calibration_summary: pd.DataFrame
    calibration_bins: pd.DataFrame


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _iter_evaluation_metadata_paths() -> list[Path]:
    patterns = [
        artifact_root().glob("baselines/*/*/evaluations/*/metadata.json"),
        artifact_root().glob("mitigations/*/*/*/evaluations/*/metadata.json"),
    ]
    paths: list[Path] = []
    for matches in patterns:
        paths.extend(matches)
    return sorted(path.resolve() for path in paths)


def _matches_experiment_group(metadata: dict[str, Any], experiment_group: str) -> bool:
    if metadata.get("experiment_group") == experiment_group:
        return True
    resolved_config = metadata.get("resolved_config", {})
    if isinstance(resolved_config, dict):
        if resolved_config.get("experiment_group") == experiment_group:
            return True
    tags = metadata.get("tags", [])
    return experiment_group in tags


def _load_candidate(metadata_path: Path) -> ReportCandidate:
    metadata = _read_json(metadata_path)
    artifact_paths = dict(metadata.get("artifact_paths", {}))
    eval_id = str(metadata.get("eval_id", metadata.get("run_id")))
    return ReportCandidate(
        eval_id=eval_id,
        metadata_path=metadata_path,
        metadata=metadata,
        overall_metrics=_read_json(Path(artifact_paths["overall_metrics_json"])),
        split_metrics=_read_csv(Path(artifact_paths["split_metrics_csv"])),
        id_ood_comparison=_read_csv(Path(artifact_paths["id_ood_comparison_csv"])),
        subgroup_metrics=_read_csv(Path(artifact_paths["subgroup_metrics_csv"])),
        worst_group_summary=_read_json(Path(artifact_paths["worst_group_summary_json"])),
        calibration_summary=_read_csv(Path(artifact_paths["calibration_summary_csv"])),
        calibration_bins=_read_csv(Path(artifact_paths["calibration_bins_csv"])),
    )


def discover_evaluation_bundles(
    *,
    experiment_group: str | None = None,
    eval_ids: list[str] | None = None,
) -> list[Path]:
    """Return metadata paths for saved evaluation bundles."""
    if not experiment_group and not eval_ids:
        raise ValueError("Either experiment_group or eval_ids must be provided")

    metadata_paths = _iter_evaluation_metadata_paths()
    if eval_ids:
        requested = {str(item).strip() for item in eval_ids if str(item).strip()}
        matched = []
        for metadata_path in metadata_paths:
            metadata = _read_json(metadata_path)
            eval_id = str(metadata.get("eval_id", metadata.get("run_id")))
            if eval_id in requested:
                matched.append(metadata_path)

        found_ids = {
            str(_read_json(path).get("eval_id", _read_json(path).get("run_id"))) for path in matched
        }
        missing_ids = sorted(requested - found_ids)
        if missing_ids:
            missing_text = ", ".join(missing_ids)
            raise FileNotFoundError(f"Saved evaluation bundle(s) not found: {missing_text}")
        return sorted(matched)

    assert experiment_group is not None
    matched = []
    for metadata_path in metadata_paths:
        metadata = _read_json(metadata_path)
        if _matches_experiment_group(metadata, experiment_group):
            matched.append(metadata_path)
    if not matched:
        raise FileNotFoundError(
            f"No saved evaluation bundles found for experiment group: {experiment_group}"
        )
    return sorted(matched)


def load_report_inputs(
    *,
    experiment_group: str | None = None,
    eval_ids: list[str] | None = None,
) -> list[ReportCandidate]:
    """Load report candidates from saved evaluation bundles."""
    metadata_paths = discover_evaluation_bundles(
        experiment_group=experiment_group,
        eval_ids=eval_ids,
    )
    return [_load_candidate(path) for path in metadata_paths]
