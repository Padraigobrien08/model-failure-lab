"""Shared mitigation helpers for parent-run validation and config inheritance."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from model_failure_lab.config import RunConfig
from model_failure_lab.utils.paths import find_run_metadata_path


def load_parent_run_context(parent_run_id: str) -> dict[str, Any]:
    """Load saved parent-run metadata and the validated resolved config."""
    metadata_path = find_run_metadata_path(parent_run_id)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise ValueError(f"Saved metadata must be a mapping: {metadata_path}")

    resolved_config = metadata.get("resolved_config")
    if not isinstance(resolved_config, dict):
        raise ValueError(
            f"Saved parent metadata is missing a resolved_config mapping: {metadata_path}"
        )

    return {
        "run_id": str(metadata.get("run_id", parent_run_id)),
        "metadata_path": metadata_path,
        "run_dir": metadata_path.parent,
        "metadata": metadata,
        "resolved_config": RunConfig.from_dict(resolved_config).to_dict(),
    }


def validate_distilbert_parent_run(parent_context: dict[str, Any]) -> dict[str, Any]:
    """Require a baseline DistilBERT parent run before launching a mitigation child."""
    metadata = dict(parent_context.get("metadata", {}))
    resolved_config = dict(parent_context.get("resolved_config", {}))
    run_label = str(parent_context.get("run_id", metadata.get("run_id", "unknown")))

    experiment_type = str(
        metadata.get("experiment_type", resolved_config.get("experiment_type", ""))
    )
    if experiment_type != "baseline":
        raise ValueError(
            f"Mitigation parent run {run_label!r} must be a baseline run; "
            f"found experiment_type={experiment_type!r}."
        )

    model_name = str(metadata.get("model_name", resolved_config.get("model_name", "")))
    if model_name != "distilbert":
        raise ValueError(
            "Group reweighting only supports DistilBERT parent baselines; "
            f"found model_name={model_name!r} for run {run_label!r}."
        )

    return parent_context


def _merge_tags(parent_tags: list[Any], child_tags: list[Any]) -> list[str]:
    merged: list[str] = []
    for raw_tag in [*parent_tags, *child_tags]:
        tag = str(raw_tag)
        if tag not in merged:
            merged.append(tag)
    return merged


def build_inherited_mitigation_config(
    parent_context: dict[str, Any],
    mitigation_preset_config: dict[str, Any],
) -> dict[str, Any]:
    """Clone the parent config and inject mitigation lineage plus method settings."""
    validated_parent = validate_distilbert_parent_run(parent_context)
    parent_metadata = dict(validated_parent["metadata"])
    parent_resolved_config = deepcopy(validated_parent["resolved_config"])
    mitigation_config = deepcopy(
        mitigation_preset_config.get("mitigation_config")
        or mitigation_preset_config.get("mitigation")
    )
    if mitigation_config is None:
        raise ValueError("Mitigation preset must define a mitigation configuration block.")

    child_config = deepcopy(parent_resolved_config)
    child_config["run_id"] = mitigation_preset_config.get("run_id")
    child_config["experiment_name"] = mitigation_preset_config.get(
        "experiment_name",
        parent_resolved_config.get("experiment_name"),
    )
    child_config["experiment_group"] = mitigation_preset_config.get(
        "experiment_group",
        parent_resolved_config.get("experiment_group"),
    )
    child_config["experiment_type"] = "mitigation"
    child_config["seed"] = int(
        mitigation_preset_config.get("seed", parent_resolved_config["seed"])
    )
    child_config["tags"] = _merge_tags(
        list(parent_resolved_config.get("tags", [])),
        list(mitigation_preset_config.get("tags", [])),
    )
    child_config["notes"] = str(mitigation_preset_config.get("notes", ""))
    child_config["parent_run_id"] = str(parent_metadata.get("run_id", validated_parent["run_id"]))
    child_config["parent_model_name"] = str(
        parent_metadata.get("model_name", parent_resolved_config["model_name"])
    )
    child_config["mitigation_method"] = str(mitigation_config["method"])
    child_config["mitigation_config"] = deepcopy(mitigation_config)
    child_config["mitigation"] = deepcopy(mitigation_config)

    return RunConfig.from_dict(child_config).to_dict()
