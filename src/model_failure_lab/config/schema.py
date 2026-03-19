"""Typed configuration contracts for experiment execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

REQUIRED_SPLIT_DETAIL_KEYS = {"train", "validation", "id_test", "ood_test"}
REQUIRED_RAW_SPLIT_KEYS = {"train", "val", "test"}
REQUIRED_SPLIT_ROLE_KEYS = {"train", "validation", "id_test", "ood_test"}
REQUIRED_POLICY_FIELDS = {"raw_split", "selector", "is_id", "is_ood"}


def _coerce_string_mapping(
    payload: object,
    *,
    name: str,
    required_keys: set[str] | None = None,
) -> dict[str, str]:
    if not isinstance(payload, dict) or not payload:
        raise ValueError(f"{name} must be a non-empty mapping")

    normalized = {str(key): str(value) for key, value in payload.items()}
    if required_keys:
        missing_keys = sorted(required_keys - set(normalized))
        if missing_keys:
            missing_text = ", ".join(missing_keys)
            raise ValueError(f"{name} is missing required keys: {missing_text}")
    return normalized


def _validate_split_role_policy(payload: object) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, dict) or not payload:
        raise ValueError("data.split_role_policy must be a non-empty mapping")

    normalized: dict[str, dict[str, Any]] = {}
    missing_roles = sorted(REQUIRED_SPLIT_ROLE_KEYS - set(map(str, payload.keys())))
    if missing_roles:
        missing_text = ", ".join(missing_roles)
        raise ValueError(f"data.split_role_policy is missing required roles: {missing_text}")

    for role_name, role_payload in payload.items():
        if not isinstance(role_payload, dict):
            raise ValueError(f"data.split_role_policy[{role_name!r}] must be a mapping")
        missing_fields = sorted(REQUIRED_POLICY_FIELDS - set(map(str, role_payload.keys())))
        if missing_fields:
            missing_text = ", ".join(missing_fields)
            raise ValueError(
                f"data.split_role_policy[{role_name!r}] is missing required fields: {missing_text}"
            )
        normalized_role = dict(role_payload)
        normalized_role["raw_split"] = str(role_payload["raw_split"])
        normalized_role["selector"] = str(role_payload["selector"])
        normalized_role["is_id"] = bool(role_payload["is_id"])
        normalized_role["is_ood"] = bool(role_payload["is_ood"])
        if "holdout_fraction" in role_payload:
            normalized_role["holdout_fraction"] = float(role_payload["holdout_fraction"])
        if "holdout_seed" in role_payload:
            normalized_role["holdout_seed"] = int(role_payload["holdout_seed"])
        normalized[str(role_name)] = normalized_role
    return normalized


def _validate_data_config(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or not payload:
        raise ValueError("data must be a non-empty mapping")

    required_fields = {
        "dataset_name",
        "text_field",
        "label_field",
        "raw_splits",
        "split_details",
        "split_role_policy",
        "validation",
    }
    missing_fields = sorted(required_fields - set(map(str, payload.keys())))
    if missing_fields:
        missing_text = ", ".join(missing_fields)
        raise ValueError(f"data is missing required fields: {missing_text}")

    if "group_fields" not in payload or not isinstance(payload["group_fields"], list):
        raise ValueError("data.group_fields must be a non-empty list")
    if not payload["group_fields"]:
        raise ValueError("data.group_fields must be a non-empty list")

    validation_payload = payload["validation"]
    if not isinstance(validation_payload, dict) or not validation_payload:
        raise ValueError("data.validation must be a non-empty mapping")

    return {
        **dict(payload),
        "dataset_name": str(payload["dataset_name"]),
        "wilds_dataset_name": str(payload.get("wilds_dataset_name", payload["dataset_name"])),
        "wilds_root_dir": str(payload.get("wilds_root_dir", "data/wilds")),
        "split_scheme": str(payload.get("split_scheme", "official")),
        "text_field": str(payload["text_field"]),
        "label_field": str(payload["label_field"]),
        "group_fields": [str(item) for item in payload["group_fields"]],
        "auxiliary_fields": [str(item) for item in payload.get("auxiliary_fields", [])],
        "raw_splits": _coerce_string_mapping(
            payload["raw_splits"],
            name="data.raw_splits",
            required_keys=REQUIRED_RAW_SPLIT_KEYS,
        ),
        "split_details": _coerce_string_mapping(
            payload["split_details"],
            name="data.split_details",
            required_keys=REQUIRED_SPLIT_DETAIL_KEYS,
        ),
        "split_role_policy": _validate_split_role_policy(payload["split_role_policy"]),
        "validation": {
            "subgroup_min_samples_warning": int(
                validation_payload.get("subgroup_min_samples_warning", 25)
            ),
            "preview_samples": int(validation_payload.get("preview_samples", 5)),
        },
    }


@dataclass(slots=True)
class RunConfig:
    """Resolved experiment configuration used by scripts and tracking."""

    run_id: str | None
    experiment_name: str
    experiment_group: str
    experiment_type: str
    model_name: str
    dataset_name: str
    split_details: dict[str, str]
    seed: int
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    parent_run_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    model: dict[str, Any] = field(default_factory=dict)
    train: dict[str, Any] = field(default_factory=dict)
    eval: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RunConfig":
        required_fields = {
            "experiment_name",
            "experiment_type",
            "model_name",
            "dataset_name",
            "split_details",
            "seed",
            "data",
            "model",
            "train",
            "eval",
        }
        missing_fields = sorted(
            field_name for field_name in required_fields if field_name not in payload
        )
        if missing_fields:
            missing_text = ", ".join(missing_fields)
            raise ValueError(f"Missing required run config fields: {missing_text}")

        split_details = payload["split_details"]
        split_details = _coerce_string_mapping(
            split_details,
            name="split_details",
            required_keys=REQUIRED_SPLIT_DETAIL_KEYS,
        )

        seed = payload["seed"]
        if not isinstance(seed, int):
            raise ValueError("seed must be an integer")

        data = _validate_data_config(payload["data"])

        return cls(
            run_id=payload.get("run_id"),
            experiment_name=str(payload["experiment_name"]),
            experiment_group=str(payload.get("experiment_group", payload["experiment_name"])),
            experiment_type=str(payload["experiment_type"]),
            model_name=str(payload["model_name"]),
            dataset_name=str(payload["dataset_name"]),
            split_details=split_details,
            seed=seed,
            tags=[str(tag) for tag in payload.get("tags", [])],
            notes=str(payload.get("notes", "")),
            parent_run_id=payload.get("parent_run_id"),
            data=data,
            model=dict(payload["model"]),
            train=dict(payload["train"]),
            eval=dict(payload["eval"]),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary representation."""
        return asdict(self)
