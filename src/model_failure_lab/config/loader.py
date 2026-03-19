"""Safe YAML loading and experiment preset composition."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from model_failure_lab.utils.paths import config_root, repository_root

from .schema import RunConfig

COMPONENT_REFERENCE_KEYS = {
    "data": "data_config",
    "model": "model_config",
    "train": "train_config",
    "eval": "eval_config",
}
ALLOWED_OVERRIDE_KEYS = {
    "seed",
    "notes",
    "run_id",
    "experiment_group",
    "eval_splits",
    "min_group_support",
    "calibration_bins",
    "output_tag",
    "eval_ids",
    "report_name",
    "output_format",
    "top_k_subgroups",
    "source_split",
    "max_source_samples",
    "families",
    "severities",
    "selection_seed",
    "perturbation_seed",
}


def _load_yaml_file(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Config file must contain a mapping: {path}")
    return payload


def _resolve_preset_path(preset_path: str | Path) -> Path:
    candidate = Path(preset_path)
    if candidate.is_absolute() and candidate.exists():
        return candidate
    if candidate.exists():
        return candidate.resolve()
    if candidate.suffix:
        relative_candidate = config_root().parent / candidate
        if relative_candidate.exists():
            return relative_candidate.resolve()
    named_candidate = config_root() / "experiments" / f"{candidate.stem}.yaml"
    if named_candidate.exists():
        return named_candidate.resolve()
    raise FileNotFoundError(f"Experiment preset not found: {preset_path}")


def _resolve_component_path(reference: str, preset_file: Path) -> Path:
    reference_path = Path(reference)
    candidates = []
    if reference_path.is_absolute():
        candidates.append(reference_path)
    else:
        candidates.append((preset_file.parent / reference_path).resolve())
        candidates.append((config_root() / reference_path).resolve())
        if reference_path.parts and reference_path.parts[0] == "configs":
            candidates.append((repository_root() / reference_path).resolve())

    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Referenced config not found: {reference}")


def load_experiment_config(preset_path: str | Path) -> dict[str, Any]:
    """Load, compose, and validate an experiment preset."""
    resolved_preset_path = _resolve_preset_path(preset_path)
    preset_payload = _load_yaml_file(resolved_preset_path)
    mitigation_payload = preset_payload.get("mitigation")
    mitigation_method = None
    if isinstance(mitigation_payload, dict):
        mitigation_method = mitigation_payload.get("method")

    resolved_payload: dict[str, Any] = {
        "run_id": preset_payload.get("run_id"),
        "experiment_name": preset_payload.get("experiment_name", resolved_preset_path.stem),
        "experiment_group": preset_payload.get(
            "experiment_group",
            preset_payload.get("experiment_name", resolved_preset_path.stem),
        ),
        "experiment_type": preset_payload.get("experiment_type", "baseline"),
        "tags": list(preset_payload.get("tags", [])),
        "notes": preset_payload.get("notes", ""),
        "parent_run_id": preset_payload.get("parent_run_id"),
        "parent_model_name": preset_payload.get("parent_model_name"),
        "mitigation_method": preset_payload.get("mitigation_method", mitigation_method),
        "mitigation_config": preset_payload.get("mitigation_config", mitigation_payload),
        "mitigation": mitigation_payload,
        "perturbation": preset_payload.get("perturbation"),
        "preset_path": str(resolved_preset_path),
    }

    for section_name, reference_key in COMPONENT_REFERENCE_KEYS.items():
        component_reference = preset_payload.get(reference_key)
        if not component_reference:
            raise ValueError(f"Preset is missing {reference_key}: {resolved_preset_path}")
        component_path = _resolve_component_path(str(component_reference), resolved_preset_path)
        component_payload = _load_yaml_file(component_path)
        resolved_payload[section_name] = component_payload

    resolved_payload["dataset_name"] = preset_payload.get(
        "dataset_name",
        resolved_payload["data"].get("dataset_name"),
    )
    resolved_payload["model_name"] = preset_payload.get(
        "model_name",
        resolved_payload["model"].get("model_name"),
    )
    resolved_payload["split_details"] = preset_payload.get(
        "split_details",
        resolved_payload["data"].get("split_details", {}),
    )
    resolved_payload["seed"] = int(
        preset_payload.get("seed", resolved_payload["train"].get("seed", 13))
    )

    validated = RunConfig.from_dict(resolved_payload)
    return validated.to_dict()


def apply_cli_overrides(config: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Apply a small, explicit set of CLI overrides to a resolved config."""
    unsupported_keys = sorted(set(overrides) - ALLOWED_OVERRIDE_KEYS)
    if unsupported_keys:
        unsupported_text = ", ".join(unsupported_keys)
        raise ValueError(f"Unsupported config override keys: {unsupported_text}")

    updated_config = deepcopy(config)
    for key, value in overrides.items():
        if value is None:
            continue
        if key == "seed":
            updated_config[key] = int(value)
        elif key in {"notes", "run_id", "experiment_group"}:
            updated_config[key] = str(value)
        elif key == "eval_splits":
            if isinstance(value, str):
                split_values = [item.strip() for item in value.split(",") if item.strip()]
            else:
                split_values = [str(item).strip() for item in value if str(item).strip()]
            updated_config.setdefault("eval", {})["requested_splits"] = split_values
        elif key == "min_group_support":
            updated_config.setdefault("eval", {})["min_group_support"] = int(value)
        elif key == "calibration_bins":
            updated_config.setdefault("eval", {})["calibration_bins"] = int(value)
        elif key == "output_tag":
            if str(updated_config.get("experiment_type")) == "perturbation_eval":
                updated_config.setdefault("perturbation", {})["output_tag"] = str(value)
            else:
                updated_config.setdefault("eval", {})["output_tag"] = str(value)
        elif key == "eval_ids":
            if isinstance(value, str):
                eval_id_values = [item.strip() for item in value.split(",") if item.strip()]
            else:
                eval_id_values = [str(item).strip() for item in value if str(item).strip()]
            updated_config.setdefault("report", {})["eval_ids"] = eval_id_values
        elif key == "report_name":
            updated_config.setdefault("report", {})["report_name"] = str(value)
        elif key == "output_format":
            updated_config.setdefault("report", {})["output_format"] = str(value)
        elif key == "top_k_subgroups":
            updated_config.setdefault("report", {})["top_k_subgroups"] = int(value)
        elif key == "source_split":
            updated_config.setdefault("perturbation", {})["source_split"] = str(value)
        elif key == "max_source_samples":
            updated_config.setdefault("perturbation", {})["max_source_samples"] = int(value)
        elif key == "families":
            if isinstance(value, str):
                family_values = [item.strip() for item in value.split(",") if item.strip()]
            else:
                family_values = [str(item).strip() for item in value if str(item).strip()]
            updated_config.setdefault("perturbation", {})["families"] = family_values
            updated_config.setdefault("perturbation", {})["default_family_order"] = family_values
        elif key == "severities":
            if isinstance(value, str):
                severity_values = [item.strip() for item in value.split(",") if item.strip()]
            else:
                severity_values = [str(item).strip() for item in value if str(item).strip()]
            updated_config.setdefault("perturbation", {})["severities"] = severity_values
        elif key == "selection_seed":
            updated_config.setdefault("perturbation", {})["selection_seed"] = int(value)
        elif key == "perturbation_seed":
            updated_config.setdefault("perturbation", {})["perturbation_seed"] = int(value)

    validated = RunConfig.from_dict(updated_config)
    return validated.to_dict()
