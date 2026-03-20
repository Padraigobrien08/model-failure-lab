"""Append-only experiment index for local comparisons."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from model_failure_lab.utils.paths import build_report_dir

EXPERIMENT_INDEX_FILENAME = "experiments.jsonl"


def experiment_index_path() -> Path:
    """Return the canonical JSONL experiment index path."""
    return build_report_dir(category="summary_tables", create=True) / EXPERIMENT_INDEX_FILENAME


def build_index_entry(metadata_path: Path, metadata_payload: dict[str, Any]) -> dict[str, Any]:
    """Build a lossless index entry from run metadata."""
    resolved_config = metadata_payload.get("resolved_config", {})
    seed = resolved_config.get("seed") if isinstance(resolved_config, dict) else None
    return {
        "run_id": metadata_payload["run_id"],
        "experiment_type": metadata_payload["experiment_type"],
        "model_name": metadata_payload["model_name"],
        "experiment_group": metadata_payload.get("experiment_group"),
        "tags": metadata_payload.get("tags", []),
        "dataset_name": metadata_payload["dataset_name"],
        "status": metadata_payload.get("status"),
        "timestamp": metadata_payload.get("timestamp"),
        "started_at": metadata_payload.get("started_at"),
        "completed_at": metadata_payload.get("completed_at"),
        "duration_seconds": metadata_payload.get("duration_seconds"),
        "seed": seed,
        "parent_run_id": metadata_payload.get("parent_run_id"),
        "source_run_id": metadata_payload.get("source_run_id"),
        "mitigation_method": metadata_payload.get("mitigation_method"),
        "report_scope": metadata_payload.get("report_scope"),
        "metadata_path": str(metadata_path),
    }


def append_experiment_index(
    entry: dict[str, Any],
    index_path: Path | None = None,
) -> Path:
    """Append a JSON object as a single line to the experiment index."""
    resolved_index_path = index_path or experiment_index_path()
    resolved_index_path.parent.mkdir(parents=True, exist_ok=True)
    with resolved_index_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True))
        handle.write("\n")
    return resolved_index_path
