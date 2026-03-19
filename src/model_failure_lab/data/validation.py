"""Validation helpers for canonical CivilComments samples."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, is_dataclass
from typing import Any, Iterable


def _sample_to_dict(sample: Any) -> dict[str, Any]:
    if is_dataclass(sample):
        return asdict(sample)
    if isinstance(sample, dict):
        return dict(sample)
    raise TypeError(f"Unsupported canonical sample type: {type(sample)!r}")


def validate_canonical_dataset(
    samples: Iterable[Any],
    *,
    allowed_splits: set[str] | None = None,
    subgroup_min_samples_warning: int = 25,
) -> dict[str, Any]:
    """Validate canonical sample structure and compute lightweight warnings."""
    normalized_samples = [_sample_to_dict(sample) for sample in samples]
    if not normalized_samples:
        raise ValueError("Canonical dataset must contain at least one sample")

    sparse_group_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()
    warnings: list[dict[str, Any]] = []

    for sample in normalized_samples:
        required_fields = {
            "sample_id",
            "text",
            "label",
            "split",
            "is_id",
            "is_ood",
            "group_id",
            "group_attributes",
            "dataset_name",
            "raw_split",
        }
        missing_fields = sorted(required_fields - set(sample))
        if missing_fields:
            missing_text = ", ".join(missing_fields)
            raise ValueError(f"Canonical sample is missing required fields: {missing_text}")
        if not str(sample["text"]).strip():
            raise ValueError("Canonical sample text must be non-empty")
        if allowed_splits and str(sample["split"]) not in allowed_splits:
            raise ValueError(f"Canonical sample split is not allowed: {sample['split']!r}")
        if bool(sample["is_id"]) and bool(sample["is_ood"]):
            raise ValueError("Canonical sample cannot be both ID and OOD")
        if not isinstance(sample["group_attributes"], dict) or not sample["group_attributes"]:
            raise ValueError("Canonical sample group_attributes must be a non-empty mapping")
        split_counts[str(sample["split"])] += 1
        sparse_group_counts[str(sample["group_id"])] += 1

    for group_id, count in sorted(sparse_group_counts.items()):
        if count < subgroup_min_samples_warning:
            warnings.append(
                {
                    "type": "sparse_group_coverage",
                    "group_id": group_id,
                    "count": count,
                    "threshold": subgroup_min_samples_warning,
                }
            )

    return {
        "sample_count": len(normalized_samples),
        "split_counts": dict(split_counts),
        "warnings": warnings,
    }
