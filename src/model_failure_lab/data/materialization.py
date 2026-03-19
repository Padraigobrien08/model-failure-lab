"""Manifest-writing helpers for CivilComments dataset materialization."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from model_failure_lab.utils.paths import build_data_manifest_path, build_data_summary_dir

from .civilcomments import SplitRole, load_civilcomments_dataset, resolve_split_policy


@dataclass(slots=True)
class MaterializationResult:
    """Serializable summary of a dataset materialization run."""

    dataset_name: str
    manifest_path: Path
    summary_dir: Path
    manifest_payload: dict[str, Any]
    raw_split_names: list[str]
    split_policy: dict[str, SplitRole]


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _extract_raw_split_names(dataset: Any, data_config: dict[str, Any]) -> list[str]:
    split_dict = getattr(dataset, "split_dict", None)
    if isinstance(split_dict, dict) and split_dict:
        return sorted(str(split_name) for split_name in split_dict)
    return sorted(str(split_name) for split_name in data_config["raw_splits"].values())


def _build_project_split_payload(
    split_policy: dict[str, SplitRole],
    available_raw_splits: list[str],
) -> dict[str, dict[str, Any]]:
    available_set = set(available_raw_splits)
    payload: dict[str, dict[str, Any]] = {}
    for role_name, role in split_policy.items():
        role_payload = asdict(role)
        role_payload["raw_split_available"] = role.raw_split in available_set
        payload[role_name] = role_payload
    return payload


def build_data_manifest_payload(
    config: dict[str, Any],
    dataset: Any,
) -> tuple[dict[str, Any], dict[str, SplitRole], list[str]]:
    """Build the persisted manifest payload for CivilComments materialization."""
    data_config = config["data"]
    split_policy = resolve_split_policy(data_config)
    raw_split_names = _extract_raw_split_names(dataset, data_config)
    summary_dir = build_data_summary_dir(create=True)

    manifest_payload: dict[str, Any] = {
        "dataset_name": str(config["dataset_name"]),
        "source": {
            "provider": "wilds",
            "wilds_dataset_name": str(data_config.get("wilds_dataset_name", config["dataset_name"])),
            "root_dir": str(data_config.get("wilds_root_dir", "data/wilds")),
            "data_dir": str(getattr(dataset, "data_dir", data_config.get("wilds_root_dir", "data/wilds"))),
            "split_scheme": str(data_config.get("split_scheme", "official")),
            "version": getattr(dataset, "version", None),
        },
        "raw_splits": {
            "configured": dict(data_config["raw_splits"]),
            "available": raw_split_names,
        },
        "project_splits": {
            "split_details": dict(config["split_details"]),
            "roles": _build_project_split_payload(split_policy, raw_split_names),
        },
        "metadata_fields": [str(field) for field in getattr(dataset, "metadata_fields", [])],
        "summary_artifacts": {
            "split_counts_csv": str(summary_dir / "split_counts.csv"),
            "label_distribution_csv": str(summary_dir / "label_distribution.csv"),
            "subgroup_coverage_csv": str(summary_dir / "subgroup_coverage.csv"),
            "text_length_summary_csv": str(summary_dir / "text_length_summary.csv"),
            "data_validation_json": str(summary_dir / "data_validation.json"),
            "sample_preview_jsonl": str(summary_dir / "sample_preview.jsonl"),
        },
        "validation_status": "not_run",
    }
    return manifest_payload, split_policy, raw_split_names


def write_data_manifest(dataset_name: str, payload: dict[str, Any]) -> Path:
    """Persist a dataset manifest under the canonical artifact location."""
    return _write_json(build_data_manifest_path(dataset_name), payload)


def materialize_civilcomments(
    config: dict[str, Any],
    *,
    download: bool = True,
    get_dataset_fn: Callable[..., Any] | None = None,
) -> MaterializationResult:
    """Load CivilComments and persist the project-local dataset manifest."""
    dataset = load_civilcomments_dataset(
        config["data"],
        download=download,
        get_dataset_fn=get_dataset_fn,
    )
    manifest_payload, split_policy, raw_split_names = build_data_manifest_payload(config, dataset)
    manifest_path = write_data_manifest(config["dataset_name"], manifest_payload)
    return MaterializationResult(
        dataset_name=str(config["dataset_name"]),
        manifest_path=manifest_path,
        summary_dir=build_data_summary_dir(create=True),
        manifest_payload=manifest_payload,
        raw_split_names=raw_split_names,
        split_policy=split_policy,
    )
