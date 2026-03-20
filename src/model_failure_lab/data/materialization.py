"""Manifest-writing and runtime handoff helpers for CivilComments."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from model_failure_lab.utils.paths import build_data_manifest_path, build_data_summary_dir

from .canonical import build_canonical_dataset
from .civilcomments import SplitRole, load_civilcomments_dataset, resolve_split_policy
from .validation import write_validation_summaries


@dataclass(slots=True)
class MaterializationResult:
    """Serializable summary of a dataset materialization run."""

    dataset_name: str
    manifest_path: Path
    summary_dir: Path
    manifest_payload: dict[str, Any]
    raw_split_names: list[str]
    split_policy: dict[str, SplitRole]
    validation_summary: dict[str, Any]


@dataclass(slots=True)
class RuntimeDatasetResult:
    """Runtime dataset plus the persisted materialization contract it used."""

    dataset: Any
    manifest_path: Path
    manifest_payload: dict[str, Any]
    summary_dir: Path


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _extract_raw_split_names(dataset: Any, data_config: dict[str, Any]) -> list[str]:
    split_dict = getattr(dataset, "split_dict", None)
    if isinstance(split_dict, dict) and split_dict:
        return sorted(str(split_name) for split_name in split_dict)
    return sorted(str(split_name) for split_name in data_config["raw_splits"].values())


def _extract_source_records(dataset: Any, data_config: dict[str, Any]) -> list[dict[str, Any]]:
    source_records = getattr(dataset, "source_records", None)
    if isinstance(source_records, list) and source_records:
        return [dict(record) for record in source_records]

    metadata_df = getattr(dataset, "_metadata_df", None)
    if metadata_df is None or not hasattr(metadata_df, "to_dict"):
        raise ValueError(
            "CivilComments dataset extraction requires `source_records` or a WILDS metadata frame."
        )

    rows = metadata_df.to_dict(orient="records")
    indices = list(getattr(metadata_df, "index", range(len(rows))))
    split_lookup = {
        str(split_id): split_name
        for split_name, split_id in getattr(dataset, "split_dict", {}).items()
    }
    text_values = list(getattr(dataset, "_text_array", []))
    label_values = getattr(dataset, "y_array", getattr(dataset, "_y_array", None))
    normalized_labels = None
    if label_values is not None:
        normalized_labels = []
        for value in label_values:
            if hasattr(value, "item"):
                normalized_labels.append(int(value.item()))
            else:
                normalized_labels.append(int(value))

    extracted_records: list[dict[str, Any]] = []
    for position, row in enumerate(rows):
        record = dict(row)
        raw_split_value = row.get("split")
        record["raw_split"] = split_lookup.get(str(raw_split_value), str(raw_split_value))
        record["raw_index"] = indices[position] if position < len(indices) else position
        if position < len(text_values):
            record[data_config["text_field"]] = text_values[position]
        if normalized_labels is not None and position < len(normalized_labels):
            record[data_config["label_field"]] = normalized_labels[position]
        extracted_records.append(record)
    return extracted_records


def extract_source_records(dataset: Any, data_config: dict[str, Any]) -> list[dict[str, Any]]:
    """Public wrapper for source-record extraction from CivilComments datasets."""
    return _extract_source_records(dataset, data_config)


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
            "wilds_dataset_name": str(
                data_config.get("wilds_dataset_name", config["dataset_name"])
            ),
            "root_dir": str(data_config.get("wilds_root_dir", "data/wilds")),
            "data_dir": str(
                getattr(dataset, "data_dir", data_config.get("wilds_root_dir", "data/wilds"))
            ),
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
        "validation_status": "pending",
    }
    return manifest_payload, split_policy, raw_split_names


def write_data_manifest(dataset_name: str, payload: dict[str, Any]) -> Path:
    """Persist a dataset manifest under the canonical artifact location."""
    return _write_json(build_data_manifest_path(dataset_name), payload)


def read_data_manifest(dataset_name: str) -> dict[str, Any] | None:
    """Load a persisted dataset manifest when it exists."""
    manifest_path = build_data_manifest_path(dataset_name)
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _materialization_contract_error(message: str) -> ValueError:
    return ValueError(f"CivilComments materialization contract error: {message}")


def _expected_project_roles(
    config: dict[str, Any],
    *,
    available_raw_splits: list[str],
) -> dict[str, dict[str, Any]]:
    return _build_project_split_payload(
        resolve_split_policy(config["data"]),
        available_raw_splits,
    )


def _validate_manifest_payload(config: dict[str, Any], manifest_payload: dict[str, Any]) -> None:
    dataset_name = str(config["dataset_name"])
    if str(manifest_payload.get("dataset_name")) != dataset_name:
        raise _materialization_contract_error(
            f"dataset_name mismatch: expected {dataset_name!r}, "
            f"found {manifest_payload.get('dataset_name')!r}"
        )

    if manifest_payload.get("validation_status") != "completed":
        raise _materialization_contract_error(
            "validation_status must be 'completed' before runtime loading."
        )

    manifest_raw_splits = (
        manifest_payload.get("raw_splits", {}) if isinstance(manifest_payload, dict) else {}
    )
    configured_raw_splits = manifest_raw_splits.get("configured")
    expected_raw_splits = dict(config["data"]["raw_splits"])
    if configured_raw_splits != expected_raw_splits:
        raise _materialization_contract_error(
            f"raw_splits.configured mismatch: expected {expected_raw_splits!r}, "
            f"found {configured_raw_splits!r}"
        )

    available_raw_splits = [
        str(split_name) for split_name in manifest_raw_splits.get("available", []) or []
    ]
    expected_roles = _expected_project_roles(
        config,
        available_raw_splits=available_raw_splits,
    )
    actual_roles = (
        manifest_payload.get("project_splits", {}).get("roles")
        if isinstance(manifest_payload.get("project_splits"), dict)
        else None
    )
    if actual_roles != expected_roles:
        raise _materialization_contract_error(
            f"project_splits.roles mismatch: expected {expected_roles!r}, "
            f"found {actual_roles!r}"
        )

    summary_artifacts = manifest_payload.get("summary_artifacts")
    if not isinstance(summary_artifacts, dict) or not summary_artifacts:
        raise _materialization_contract_error("summary_artifacts is missing or empty.")
    missing_summary_keys = []
    for key, raw_path in summary_artifacts.items():
        if not raw_path or not Path(raw_path).exists():
            missing_summary_keys.append(key)
    if missing_summary_keys:
        raise _materialization_contract_error(
            "missing summary artifacts: " + ", ".join(sorted(missing_summary_keys))
        )


def prepare_civilcomments_runtime_dataset(
    config: dict[str, Any],
    *,
    download: bool = True,
    get_dataset_fn: Callable[..., Any] | None = None,
    materialize_if_missing: bool = True,
) -> RuntimeDatasetResult:
    """Load canonical CivilComments samples through the saved materialization contract."""
    dataset_name = str(config["dataset_name"])
    manifest_path = build_data_manifest_path(dataset_name)
    manifest_payload = read_data_manifest(dataset_name)

    if manifest_payload is None:
        if not materialize_if_missing:
            raise _materialization_contract_error(
                f"manifest missing at {manifest_path}; run `python scripts/download_data.py` first."
            )
        materialization = materialize_civilcomments(
            config,
            download=download,
            get_dataset_fn=get_dataset_fn,
        )
        manifest_payload = materialization.manifest_payload
        manifest_path = materialization.manifest_path

    _validate_manifest_payload(config, manifest_payload)

    dataset = load_civilcomments_dataset(
        config["data"],
        download=download,
        get_dataset_fn=get_dataset_fn,
    )
    source_records = extract_source_records(dataset, config["data"])
    canonical_dataset = build_canonical_dataset(
        source_records,
        config["data"],
        dataset_name=dataset_name,
    )

    summary_artifacts = manifest_payload["summary_artifacts"]
    summary_dir = Path(summary_artifacts["data_validation_json"]).parent
    return RuntimeDatasetResult(
        dataset=canonical_dataset,
        manifest_path=manifest_path,
        manifest_payload=manifest_payload,
        summary_dir=summary_dir,
    )


def load_canonical_civilcomments_dataset(
    config: dict[str, Any],
    *,
    download: bool = True,
    get_dataset_fn: Callable[..., Any] | None = None,
):
    """Compatibility wrapper that returns canonical samples only."""
    return prepare_civilcomments_runtime_dataset(
        config,
        download=download,
        get_dataset_fn=get_dataset_fn,
    ).dataset


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
    source_records = extract_source_records(dataset, config["data"])
    canonical_dataset = build_canonical_dataset(source_records, config["data"])
    validation_summary = write_validation_summaries(
        canonical_dataset.samples,
        build_data_summary_dir(create=True),
        allowed_splits=set(config["data"]["split_role_policy"]),
        subgroup_min_samples_warning=int(
            config["data"]["validation"]["subgroup_min_samples_warning"]
        ),
        preview_limit=int(config["data"]["validation"]["preview_samples"]),
    )
    manifest_payload["sample_count"] = validation_summary["sample_count"]
    manifest_payload["validation_status"] = "completed"
    manifest_payload["validation_summary"] = validation_summary
    manifest_path = write_data_manifest(config["dataset_name"], manifest_payload)
    return MaterializationResult(
        dataset_name=str(config["dataset_name"]),
        manifest_path=manifest_path,
        summary_dir=build_data_summary_dir(create=True),
        manifest_payload=manifest_payload,
        raw_split_names=raw_split_names,
        split_policy=split_policy,
        validation_summary=validation_summary,
    )
