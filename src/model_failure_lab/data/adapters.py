"""Lazy adapters from canonical samples to model-family-specific views."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .validation import validate_canonical_dataset


def _normalize_samples(samples: Iterable[Any]) -> list[dict[str, Any]]:
    normalized = []
    for sample in samples:
        if hasattr(sample, "to_dict"):
            normalized.append(sample.to_dict())
        elif isinstance(sample, dict):
            normalized.append(dict(sample))
        else:
            raise TypeError(f"Unsupported canonical sample type: {type(sample)!r}")
    return normalized


def _filter_samples(samples: list[dict[str, Any]], split: str | None) -> list[dict[str, Any]]:
    if split is None:
        return samples
    return [sample for sample in samples if str(sample["split"]) == split]


@dataclass(slots=True)
class TfidfAdapterView:
    """Plain-text view for sparse text feature extraction."""

    texts: list[str]
    labels: list[int]
    sample_ids: list[str]
    splits: list[str]
    group_ids: list[str]


@dataclass(slots=True)
class TransformerAdapterView:
    """Tokenizer-ready view for transformer fine-tuning."""

    records: list[dict[str, Any]]
    preprocessing_config: dict[str, Any]


def prepare_tfidf_adapter(
    samples: Iterable[Any],
    *,
    split: str | None = None,
    subgroup_min_samples_warning: int = 25,
) -> TfidfAdapterView:
    """Prepare a TF-IDF-friendly in-memory view from canonical samples."""
    normalized_samples = _filter_samples(_normalize_samples(samples), split)
    validate_canonical_dataset(
        normalized_samples,
        allowed_splits={split} if split else None,
        subgroup_min_samples_warning=subgroup_min_samples_warning,
    )
    return TfidfAdapterView(
        texts=[str(sample["text"]) for sample in normalized_samples],
        labels=[int(sample["label"]) for sample in normalized_samples],
        sample_ids=[str(sample["sample_id"]) for sample in normalized_samples],
        splits=[str(sample["split"]) for sample in normalized_samples],
        group_ids=[str(sample["group_id"]) for sample in normalized_samples],
    )


def prepare_transformer_adapter(
    samples: Iterable[Any],
    *,
    split: str | None = None,
    tokenizer_name: str = "distilbert-base-uncased",
    max_length: int = 256,
    subgroup_min_samples_warning: int = 25,
) -> TransformerAdapterView:
    """Prepare a tokenizer-ready transformer view from canonical samples."""
    normalized_samples = _filter_samples(_normalize_samples(samples), split)
    validate_canonical_dataset(
        normalized_samples,
        allowed_splits={split} if split else None,
        subgroup_min_samples_warning=subgroup_min_samples_warning,
    )
    records = [
        {
            "text": str(sample["text"]),
            "label": int(sample["label"]),
            "sample_id": str(sample["sample_id"]),
            "split": str(sample["split"]),
            "group_id": str(sample["group_id"]),
            "group_attributes": dict(sample["group_attributes"]),
        }
        for sample in normalized_samples
    ]
    return TransformerAdapterView(
        records=records,
        preprocessing_config={
            "tokenizer_name": tokenizer_name,
            "max_length": max_length,
            "split": split,
        },
    )
