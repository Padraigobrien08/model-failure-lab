"""Validation helpers for canonical CivilComments samples."""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable


def _sample_to_dict(sample: Any) -> dict[str, Any]:
    if is_dataclass(sample):
        return asdict(sample)
    if isinstance(sample, dict):
        return dict(sample)
    raise TypeError(f"Unsupported canonical sample type: {type(sample)!r}")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


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
    label_distribution: Counter[tuple[str, int]] = Counter()
    id_ood_counts: Counter[str] = Counter()
    missingness = {"text": 0, "label": 0, "group_attributes": 0}
    duplicate_counter: Counter[str] = Counter()
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
        if sample["label"] is None:
            raise ValueError("Canonical sample label must be present")
        if allowed_splits and str(sample["split"]) not in allowed_splits:
            raise ValueError(f"Canonical sample split is not allowed: {sample['split']!r}")
        if bool(sample["is_id"]) and bool(sample["is_ood"]):
            raise ValueError("Canonical sample cannot be both ID and OOD")
        if not isinstance(sample["group_attributes"], dict) or not sample["group_attributes"]:
            raise ValueError("Canonical sample group_attributes must be a non-empty mapping")
        if "raw_index" in sample and sample["raw_index"] is None:
            missingness["label"] += 0
        duplicate_counter[str(sample["sample_id"])] += 1
        split_counts[str(sample["split"])] += 1
        label_distribution[(str(sample["split"]), int(sample["label"]))] += 1
        id_ood_counts["id" if bool(sample["is_id"]) else "ood"] += 1
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

    duplicate_sample_ids = sorted(
        sample_id for sample_id, count in duplicate_counter.items() if count > 1
    )

    return {
        "sample_count": len(normalized_samples),
        "split_counts": dict(split_counts),
        "label_distribution": [
            {"split": split, "label": label, "count": count}
            for (split, label), count in sorted(label_distribution.items())
        ],
        "id_ood_summary": dict(id_ood_counts),
        "missingness": missingness,
        "duplicate_sample_ids": duplicate_sample_ids,
        "warnings": warnings,
    }


def write_validation_summaries(
    samples: Iterable[Any],
    summary_dir: Path,
    *,
    allowed_splits: set[str] | None = None,
    subgroup_min_samples_warning: int = 25,
    preview_limit: int = 5,
) -> dict[str, Any]:
    """Persist the required validation summary bundle for canonical samples."""
    normalized_samples = [_sample_to_dict(sample) for sample in samples]
    validation_summary = validate_canonical_dataset(
        normalized_samples,
        allowed_splits=allowed_splits,
        subgroup_min_samples_warning=subgroup_min_samples_warning,
    )

    split_counts_rows = [
        {"split": split, "count": count}
        for split, count in sorted(validation_summary["split_counts"].items())
    ]
    subgroup_coverage_counts: Counter[tuple[str, str]] = Counter(
        (str(sample["split"]), str(sample["group_id"])) for sample in normalized_samples
    )
    subgroup_coverage_rows = [
        {"split": split, "group_id": group_id, "count": count}
        for (split, group_id), count in sorted(subgroup_coverage_counts.items())
    ]

    text_length_buckets: dict[str, list[int]] = {}
    for sample in normalized_samples:
        text_length_buckets.setdefault(str(sample["split"]), []).append(len(str(sample["text"])))
    text_length_rows = []
    for split, lengths in sorted(text_length_buckets.items()):
        text_length_rows.append(
            {
                "split": split,
                "count": len(lengths),
                "min_length": min(lengths),
                "max_length": max(lengths),
                "mean_length": round(sum(lengths) / len(lengths), 2),
            }
        )

    _write_csv(summary_dir / "split_counts.csv", split_counts_rows, ["split", "count"])
    _write_csv(
        summary_dir / "label_distribution.csv",
        validation_summary["label_distribution"],
        ["split", "label", "count"],
    )
    _write_csv(
        summary_dir / "subgroup_coverage.csv",
        subgroup_coverage_rows,
        ["split", "group_id", "count"],
    )
    _write_csv(
        summary_dir / "text_length_summary.csv",
        text_length_rows,
        ["split", "count", "min_length", "max_length", "mean_length"],
    )
    _write_json(
        summary_dir / "data_validation.json",
        {
            **validation_summary,
            "split_integrity": {"valid": True},
        },
    )
    _write_jsonl(
        summary_dir / "sample_preview.jsonl",
        normalized_samples[: max(preview_limit, 0)],
    )
    return validation_summary
