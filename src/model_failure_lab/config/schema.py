"""Typed configuration contracts for experiment execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

REQUIRED_SPLIT_DETAIL_KEYS = {"train", "validation", "id_test", "ood_test"}
REQUIRED_RAW_SPLIT_KEYS = {"train", "val", "test"}
REQUIRED_SPLIT_ROLE_KEYS = {"train", "validation", "id_test", "ood_test"}
REQUIRED_POLICY_FIELDS = {"raw_split", "selector", "is_id", "is_ood"}
REQUIRED_REWEIGHTING_FIELDS = {
    "grouping_field",
    "strategy",
    "max_weight",
    "normalize_mean",
}
REQUIRED_GROUP_DRO_FIELDS = {
    "grouping_field",
    "adversary_step_size",
    "loss_ema",
}
REQUIRED_GROUP_BALANCED_SAMPLING_FIELDS = {
    "grouping_field",
    "strategy",
    "blend_alpha",
    "max_sampling_multiplier",
}
REQUIRED_TEMPERATURE_SCALING_FIELDS = {
    "fitting_split",
    "objective",
    "apply_to_splits",
    "allow_checkpoint_regeneration",
}
REQUIRED_PERTURBATION_FIELDS = {
    "source_split",
    "max_source_samples",
    "families",
    "severities",
    "selection_seed",
    "perturbation_seed",
}
REQUIRED_COMPARISON_TOLERANCE_FIELDS = {
    "id_macro_f1_max_drop",
    "overall_macro_f1_max_drop",
    "ece_neutral_tolerance",
}
SUPPORTED_MITIGATION_METHODS = {
    "group_balanced_sampling",
    "group_dro",
    "reweighting",
    "temperature_scaling",
}
SUPPORTED_PERTURBATION_FAMILIES = {
    "typo_noise",
    "format_degradation",
    "slang_rewrite",
}
SUPPORTED_PERTURBATION_SEVERITIES = {"low", "medium", "high"}
DEFAULT_TRACKED_METRICS = ["accuracy", "macro_f1", "auroc", "loss"]


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


def _coerce_float_mapping(
    payload: object,
    *,
    name: str,
    required_keys: set[str] | None = None,
) -> dict[str, float]:
    if not isinstance(payload, dict) or not payload:
        raise ValueError(f"{name} must be a non-empty mapping")

    normalized = {str(key): float(value) for key, value in payload.items()}
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


def _validate_eval_config(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or not payload:
        raise ValueError("eval must be a non-empty mapping")

    tracked_metrics = payload.get("tracked_metrics", DEFAULT_TRACKED_METRICS)
    if not isinstance(tracked_metrics, list) or not tracked_metrics:
        raise ValueError("eval.tracked_metrics must be a non-empty list")

    calibration_bins = int(payload.get("calibration_bins", 10))
    if calibration_bins <= 0:
        raise ValueError("eval.calibration_bins must be a positive integer")

    min_group_support = int(payload.get("min_group_support", 100))
    if min_group_support < 0:
        raise ValueError("eval.min_group_support must be zero or greater")

    requested_splits = payload.get("requested_splits")
    if requested_splits is not None:
        if not isinstance(requested_splits, list):
            raise ValueError("eval.requested_splits must be a list when provided")
        normalized_requested_splits = [str(split) for split in requested_splits]
    else:
        normalized_requested_splits = None

    return {
        **dict(payload),
        "primary_metric": str(payload.get("primary_metric", "macro_f1")),
        "worst_group_metric": str(payload.get("worst_group_metric", "accuracy")),
        "robustness_gap_metric": str(payload.get("robustness_gap_metric", "accuracy_delta")),
        "calibration_metric": str(payload.get("calibration_metric", "ece")),
        "prediction_filename": str(payload.get("prediction_filename", "predictions.parquet")),
        "tracked_metrics": [str(metric) for metric in tracked_metrics],
        "min_group_support": min_group_support,
        "calibration_bins": calibration_bins,
        "calibration_strategy": str(payload.get("calibration_strategy", "uniform")),
        "requested_splits": normalized_requested_splits,
        "output_tag": str(payload["output_tag"]) if payload.get("output_tag") is not None else None,
    }


def _validate_report_config(payload: object) -> dict[str, Any]:
    if payload in (None, {}):
        return {
            "report_name": None,
            "output_format": "markdown",
            "top_k_subgroups": 5,
            "eval_ids": None,
        }

    if not isinstance(payload, dict):
        raise ValueError("report must be a mapping when provided")

    output_format = str(payload.get("output_format", "markdown"))
    if output_format != "markdown":
        raise ValueError("report.output_format must currently be 'markdown'")

    top_k_subgroups = int(payload.get("top_k_subgroups", 5))
    if top_k_subgroups <= 0:
        raise ValueError("report.top_k_subgroups must be a positive integer")

    eval_ids = payload.get("eval_ids")
    if eval_ids is not None:
        if not isinstance(eval_ids, list):
            raise ValueError("report.eval_ids must be a list when provided")
        normalized_eval_ids = [str(item) for item in eval_ids]
    else:
        normalized_eval_ids = None

    return {
        **dict(payload),
        "report_name": (
            str(payload["report_name"]) if payload.get("report_name") is not None else None
        ),
        "output_format": output_format,
        "top_k_subgroups": top_k_subgroups,
        "eval_ids": normalized_eval_ids,
    }


def _validate_reweighting_config(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or not payload:
        raise ValueError("mitigation.reweighting must be a non-empty mapping")

    missing_fields = sorted(REQUIRED_REWEIGHTING_FIELDS - set(map(str, payload.keys())))
    if missing_fields:
        missing_text = ", ".join(missing_fields)
        raise ValueError(f"mitigation.reweighting is missing required fields: {missing_text}")

    max_weight = float(payload["max_weight"])
    if max_weight <= 0:
        raise ValueError("mitigation.reweighting.max_weight must be positive")

    normalize_mean = float(payload["normalize_mean"])
    if normalize_mean <= 0:
        raise ValueError("mitigation.reweighting.normalize_mean must be positive")

    return {
        **dict(payload),
        "grouping_field": str(payload["grouping_field"]),
        "strategy": str(payload["strategy"]),
        "max_weight": max_weight,
        "normalize_mean": normalize_mean,
    }


def _validate_group_dro_config(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or not payload:
        raise ValueError("mitigation.group_dro must be a non-empty mapping")

    missing_fields = sorted(REQUIRED_GROUP_DRO_FIELDS - set(map(str, payload.keys())))
    if missing_fields:
        missing_text = ", ".join(missing_fields)
        raise ValueError(f"mitigation.group_dro is missing required fields: {missing_text}")

    adversary_step_size = float(payload["adversary_step_size"])
    if adversary_step_size <= 0:
        raise ValueError("mitigation.group_dro.adversary_step_size must be positive")

    loss_ema = float(payload["loss_ema"])
    if not 0.0 < loss_ema <= 1.0:
        raise ValueError("mitigation.group_dro.loss_ema must be in the interval (0, 1]")

    return {
        **dict(payload),
        "grouping_field": str(payload["grouping_field"]),
        "adversary_step_size": adversary_step_size,
        "loss_ema": loss_ema,
    }


def _validate_group_balanced_sampling_config(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or not payload:
        raise ValueError("mitigation.group_balanced_sampling must be a non-empty mapping")

    missing_fields = sorted(
        REQUIRED_GROUP_BALANCED_SAMPLING_FIELDS - set(map(str, payload.keys()))
    )
    if missing_fields:
        missing_text = ", ".join(missing_fields)
        raise ValueError(
            "mitigation.group_balanced_sampling is missing required fields: "
            f"{missing_text}"
        )

    strategy = str(payload["strategy"])
    if strategy != "inverse_sqrt_frequency":
        raise ValueError(
            "mitigation.group_balanced_sampling.strategy must be "
            "'inverse_sqrt_frequency'"
        )

    blend_alpha = float(payload["blend_alpha"])
    if not 0.0 <= blend_alpha <= 1.0:
        raise ValueError(
            "mitigation.group_balanced_sampling.blend_alpha must be in the interval [0, 1]"
        )

    max_sampling_multiplier = float(payload["max_sampling_multiplier"])
    if max_sampling_multiplier < 1.0:
        raise ValueError(
            "mitigation.group_balanced_sampling.max_sampling_multiplier must be at least 1.0"
        )

    return {
        **dict(payload),
        "grouping_field": str(payload["grouping_field"]),
        "strategy": strategy,
        "blend_alpha": blend_alpha,
        "max_sampling_multiplier": max_sampling_multiplier,
    }


def _validate_temperature_scaling_config(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or not payload:
        raise ValueError("mitigation.temperature_scaling must be a non-empty mapping")

    missing_fields = sorted(
        REQUIRED_TEMPERATURE_SCALING_FIELDS - set(map(str, payload.keys()))
    )
    if missing_fields:
        missing_text = ", ".join(missing_fields)
        raise ValueError(
            "mitigation.temperature_scaling is missing required fields: "
            f"{missing_text}"
        )

    apply_to_splits = payload["apply_to_splits"]
    if not isinstance(apply_to_splits, list) or not apply_to_splits:
        raise ValueError(
            "mitigation.temperature_scaling.apply_to_splits must be a non-empty list"
        )

    objective = str(payload["objective"])
    if objective != "nll":
        raise ValueError(
            "mitigation.temperature_scaling.objective must be 'nll' for MVP"
        )

    return {
        **dict(payload),
        "fitting_split": str(payload["fitting_split"]),
        "objective": objective,
        "apply_to_splits": [str(split) for split in apply_to_splits],
        "allow_checkpoint_regeneration": bool(payload["allow_checkpoint_regeneration"]),
    }


def _validate_mitigation_config(payload: object) -> dict[str, Any] | None:
    if payload in (None, {}):
        return None
    if not isinstance(payload, dict):
        raise ValueError("mitigation must be a mapping when provided")

    method = payload.get("method")
    if method is None:
        raise ValueError("mitigation.method is required when mitigation is provided")

    parent_model_name = payload.get("parent_model_name")
    if parent_model_name is None:
        raise ValueError(
            "mitigation.parent_model_name is required when mitigation is provided"
        )

    comparison_tolerances = _coerce_float_mapping(
        payload.get("comparison_tolerances"),
        name="mitigation.comparison_tolerances",
        required_keys=REQUIRED_COMPARISON_TOLERANCE_FIELDS,
    )

    normalized = {
        "method": str(method),
        "parent_model_name": str(parent_model_name),
        "comparison_tolerances": comparison_tolerances,
    }

    if normalized["method"] not in SUPPORTED_MITIGATION_METHODS:
        supported = ", ".join(sorted(SUPPORTED_MITIGATION_METHODS))
        raise ValueError(
            f"Unsupported mitigation.method {normalized['method']!r}; expected one of: "
            f"{supported}"
        )

    if normalized["method"] == "reweighting":
        normalized["reweighting"] = _validate_reweighting_config(payload.get("reweighting"))
    elif payload.get("reweighting") is not None:
        normalized["reweighting"] = _validate_reweighting_config(payload.get("reweighting"))

    if normalized["method"] == "group_dro":
        normalized["group_dro"] = _validate_group_dro_config(payload.get("group_dro"))
    elif payload.get("group_dro") is not None:
        normalized["group_dro"] = _validate_group_dro_config(payload.get("group_dro"))

    if normalized["method"] == "group_balanced_sampling":
        normalized["group_balanced_sampling"] = _validate_group_balanced_sampling_config(
            payload.get("group_balanced_sampling")
        )
    elif payload.get("group_balanced_sampling") is not None:
        normalized["group_balanced_sampling"] = _validate_group_balanced_sampling_config(
            payload.get("group_balanced_sampling")
        )

    if normalized["method"] == "temperature_scaling":
        normalized["temperature_scaling"] = _validate_temperature_scaling_config(
            payload.get("temperature_scaling")
        )
    elif payload.get("temperature_scaling") is not None:
        normalized["temperature_scaling"] = _validate_temperature_scaling_config(
            payload.get("temperature_scaling")
        )

    for key, value in payload.items():
        normalized.setdefault(str(key), value)

    return normalized


def _validate_perturbation_config(payload: object) -> dict[str, Any] | None:
    if payload in (None, {}):
        return None
    if not isinstance(payload, dict):
        raise ValueError("perturbation must be a mapping when provided")

    missing_fields = sorted(REQUIRED_PERTURBATION_FIELDS - set(map(str, payload.keys())))
    if missing_fields:
        missing_text = ", ".join(missing_fields)
        raise ValueError(f"perturbation is missing required fields: {missing_text}")

    max_source_samples = int(payload["max_source_samples"])
    if max_source_samples <= 0:
        raise ValueError("perturbation.max_source_samples must be positive")

    selection_seed = int(payload["selection_seed"])
    perturbation_seed = int(payload["perturbation_seed"])

    families_payload = payload["families"]
    if not isinstance(families_payload, list) or not families_payload:
        raise ValueError("perturbation.families must be a non-empty list")
    families = [str(item) for item in families_payload]
    unsupported_families = sorted(set(families) - SUPPORTED_PERTURBATION_FAMILIES)
    if unsupported_families:
        unsupported_text = ", ".join(unsupported_families)
        raise ValueError(
            "Unsupported perturbation families: "
            f"{unsupported_text}"
        )

    severities_payload = payload["severities"]
    if not isinstance(severities_payload, list) or not severities_payload:
        raise ValueError("perturbation.severities must be a non-empty list")
    severities = [str(item) for item in severities_payload]
    unsupported_severities = sorted(set(severities) - SUPPORTED_PERTURBATION_SEVERITIES)
    if unsupported_severities:
        unsupported_text = ", ".join(unsupported_severities)
        raise ValueError(
            "Unsupported perturbation severities: "
            f"{unsupported_text}"
        )

    default_family_order_payload = payload.get("default_family_order", families)
    if not isinstance(default_family_order_payload, list) or not default_family_order_payload:
        raise ValueError("perturbation.default_family_order must be a non-empty list")
    default_family_order = [str(item) for item in default_family_order_payload]
    order_set = set(default_family_order)
    family_set = set(families)
    if order_set != family_set:
        raise ValueError(
            "perturbation.default_family_order must contain the same families as "
            "perturbation.families"
        )

    slang_mapping = payload.get("slang_mapping")
    normalized_mapping: dict[str, str] | None = None
    if slang_mapping is not None:
        normalized_mapping = _coerce_string_mapping(
            slang_mapping,
            name="perturbation.slang_mapping",
        )

    return {
        **dict(payload),
        "source_split": str(payload["source_split"]),
        "max_source_samples": max_source_samples,
        "families": families,
        "severities": severities,
        "selection_seed": selection_seed,
        "perturbation_seed": perturbation_seed,
        "default_family_order": default_family_order,
        "output_tag": (
            str(payload["output_tag"]) if payload.get("output_tag") is not None else None
        ),
        "slang_mapping_name": str(payload.get("slang_mapping_name", "default")),
        "slang_mapping": normalized_mapping,
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
    preset_path: str | None = None
    parent_run_id: str | None = None
    parent_model_name: str | None = None
    mitigation_method: str | None = None
    mitigation_config: dict[str, Any] | None = None
    mitigation: dict[str, Any] | None = None
    perturbation: dict[str, Any] | None = None
    data: dict[str, Any] = field(default_factory=dict)
    model: dict[str, Any] = field(default_factory=dict)
    train: dict[str, Any] = field(default_factory=dict)
    eval: dict[str, Any] = field(default_factory=dict)
    report: dict[str, Any] = field(default_factory=dict)

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
        mitigation = _validate_mitigation_config(payload.get("mitigation"))
        perturbation = _validate_perturbation_config(payload.get("perturbation"))
        mitigation_config_payload = payload.get("mitigation_config", mitigation)
        mitigation_config = (
            _validate_mitigation_config(mitigation_config_payload)
            if mitigation_config_payload is not None
            else mitigation
        )
        mitigation_method = payload.get("mitigation_method")
        if mitigation_method is None and mitigation is not None:
            mitigation_method = mitigation["method"]
        parent_model_name = payload.get("parent_model_name")
        if parent_model_name is None and mitigation is not None:
            parent_model_name = mitigation["parent_model_name"]

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
            preset_path=(
                str(payload["preset_path"]) if payload.get("preset_path") is not None else None
            ),
            parent_run_id=payload.get("parent_run_id"),
            parent_model_name=(
                str(parent_model_name) if parent_model_name is not None else None
            ),
            mitigation_method=(
                str(mitigation_method) if mitigation_method is not None else None
            ),
            mitigation_config=mitigation_config,
            mitigation=mitigation,
            perturbation=perturbation,
            data=data,
            model=dict(payload["model"]),
            train=dict(payload["train"]),
            eval=_validate_eval_config(payload["eval"]),
            report=_validate_report_config(payload.get("report")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary representation."""
        return asdict(self)
