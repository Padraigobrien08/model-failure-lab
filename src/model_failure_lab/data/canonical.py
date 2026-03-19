"""Canonical sample construction for CivilComments rows."""

from __future__ import annotations

import hashlib
from typing import Any, Iterable

from .civilcomments import SplitRole, resolve_split_policy
from .grouping import build_group_attributes, build_group_id
from .schema import CanonicalDataset, CanonicalSample
from .validation import validate_canonical_dataset


def build_sample_id(
    dataset_name: str,
    *,
    raw_split: str,
    raw_index: int | str | None,
    text: str,
    label: int,
) -> str:
    """Build a stable sample identifier from raw source coordinates."""
    basis = f"{dataset_name}|{raw_split}|{raw_index}|{label}|{text}"
    digest = hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]
    return f"{dataset_name}_{digest}"


def _stable_fraction(dataset_name: str, raw_split: str, raw_index: int | str | None) -> float:
    raw_key = f"{dataset_name}|{raw_split}|{raw_index}"
    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]
    numerator = int(digest, 16)
    denominator = float(16**16 - 1)
    return numerator / denominator


def _matches_holdout(
    role: SplitRole,
    *,
    dataset_name: str,
    raw_split: str,
    raw_index: int | str | None,
) -> bool:
    if role.selector != "deterministic_holdout":
        return False
    if raw_split != role.raw_split:
        return False
    holdout_fraction = role.holdout_fraction or 0.0
    return _stable_fraction(dataset_name, raw_split, raw_index) < holdout_fraction


def _resolve_project_split(
    *,
    dataset_name: str,
    raw_split: str,
    raw_index: int | str | None,
    split_policy: dict[str, SplitRole],
) -> SplitRole:
    holdout_roles = [
        role
        for role in split_policy.values()
        if role.selector == "deterministic_holdout" and role.raw_split == raw_split
    ]
    for role in holdout_roles:
        if _matches_holdout(
            role,
            dataset_name=dataset_name,
            raw_split=raw_split,
            raw_index=raw_index,
        ):
            return role

    fallback_order = ("train", "validation", "ood_test", "id_test")
    for role_name in fallback_order:
        role = split_policy.get(role_name)
        if role is None or role.raw_split != raw_split:
            continue
        if role.selector in {"train_remainder", "full_split"}:
            return role
    raise ValueError(f"Unable to resolve project split for raw split {raw_split!r}")


def build_canonical_samples(
    records: Iterable[dict[str, Any]],
    data_config: dict[str, Any],
    *,
    dataset_name: str | None = None,
) -> list[CanonicalSample]:
    """Normalize source records into canonical CivilComments samples."""
    resolved_dataset_name = dataset_name or str(data_config["dataset_name"])
    split_policy = resolve_split_policy(data_config)
    text_field = str(data_config["text_field"])
    label_field = str(data_config["label_field"])
    samples: list[CanonicalSample] = []

    for record in records:
        if "raw_split" not in record:
            raise ValueError("Source record is missing raw_split")
        raw_split = str(record["raw_split"])
        raw_index = record.get("raw_index")
        resolved_split = _resolve_project_split(
            dataset_name=resolved_dataset_name,
            raw_split=raw_split,
            raw_index=raw_index,
            split_policy=split_policy,
        )
        if text_field not in record:
            raise ValueError(f"Source record is missing text field: {text_field}")
        if label_field not in record:
            raise ValueError(f"Source record is missing label field: {label_field}")

        text = str(record[text_field])
        label = int(record[label_field])
        group_attributes = build_group_attributes(record, data_config)
        excluded_fields = set(data_config["group_fields"]) | set(
            data_config.get("auxiliary_fields", [])
        )
        excluded_fields.update({text_field, label_field, "raw_split", "raw_index"})
        source_metadata = {
            str(key): value for key, value in record.items() if str(key) not in excluded_fields
        }
        samples.append(
            CanonicalSample(
                sample_id=build_sample_id(
                    resolved_dataset_name,
                    raw_split=raw_split,
                    raw_index=raw_index,
                    text=text,
                    label=label,
                ),
                text=text,
                label=label,
                split=resolved_split.name,
                is_id=resolved_split.is_id,
                is_ood=resolved_split.is_ood,
                group_id=build_group_id(group_attributes),
                group_attributes=group_attributes,
                dataset_name=resolved_dataset_name,
                raw_split=raw_split,
                raw_index=raw_index,
                source_metadata=source_metadata,
            )
        )
    return samples


def build_canonical_dataset(
    records: Iterable[dict[str, Any]],
    data_config: dict[str, Any],
    *,
    dataset_name: str | None = None,
) -> CanonicalDataset:
    """Build and validate a canonical dataset from source records."""
    resolved_dataset_name = dataset_name or str(data_config["dataset_name"])
    samples = build_canonical_samples(records, data_config, dataset_name=resolved_dataset_name)
    validate_canonical_dataset(
        samples,
        allowed_splits=set(data_config["split_role_policy"]),
        subgroup_min_samples_warning=int(data_config["validation"]["subgroup_min_samples_warning"]),
    )
    return CanonicalDataset(dataset_name=resolved_dataset_name, samples=samples)
