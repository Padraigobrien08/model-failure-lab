"""Bundle writers for perturbation suite artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from model_failure_lab.utils.paths import build_perturbation_artifact_paths

from .schema import PerturbationSuite


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")
    return path


def build_suite_manifest_payload(
    suite: PerturbationSuite,
    *,
    source_run_metadata: dict[str, Any],
    resolved_config: dict[str, Any],
) -> dict[str, Any]:
    """Build the manifest payload for one perturbation suite bundle."""
    perturbation_config = dict(resolved_config.get("perturbation", {}))
    return {
        "schema_version": suite.schema_version,
        "source_run_id": suite.source_run_id,
        "source_model_name": source_run_metadata.get("model_name"),
        "dataset_name": suite.dataset_name,
        "source_split": suite.source_split,
        "selection_seed": suite.selection_seed,
        "perturbation_seed": suite.perturbation_seed,
        "families": list(suite.families),
        "severities": list(suite.severities),
        "max_source_samples": perturbation_config.get("max_source_samples"),
        "output_tag": perturbation_config.get("output_tag"),
        "source_sample_count": suite.source_sample_count,
        "perturbed_sample_count": suite.perturbed_sample_count,
    }


def write_perturbation_bundle(
    run_dir: Path,
    *,
    suite: PerturbationSuite,
    source_run_metadata: dict[str, Any],
    resolved_config: dict[str, Any],
    preview_limit: int = 5,
) -> dict[str, str]:
    """Persist the perturbation suite contract under one bundle directory."""
    artifact_paths = build_perturbation_artifact_paths(run_dir)
    manifest_payload = build_suite_manifest_payload(
        suite,
        source_run_metadata=source_run_metadata,
        resolved_config=resolved_config,
    )
    _write_json(Path(artifact_paths["suite_manifest_json"]), manifest_payload)
    records = suite.to_records()
    _write_jsonl(Path(artifact_paths["perturbed_samples_jsonl"]), records)
    _write_jsonl(Path(artifact_paths["sample_preview_jsonl"]), records[:preview_limit])
    Path(artifact_paths["figures_dir"]).mkdir(parents=True, exist_ok=True)
    return artifact_paths

