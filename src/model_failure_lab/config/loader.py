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
ALLOWED_OVERRIDE_KEYS = {"seed", "notes", "run_id", "experiment_group"}


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

    validated = RunConfig.from_dict(updated_config)
    return validated.to_dict()
