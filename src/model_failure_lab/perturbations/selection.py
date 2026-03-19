"""Deterministic source-sample selection for perturbation suites."""

from __future__ import annotations

import hashlib
from typing import Any, Iterable


def _normalize_source_samples(samples: Iterable[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for sample in samples:
        if hasattr(sample, "to_dict"):
            normalized.append(sample.to_dict())
        elif isinstance(sample, dict):
            normalized.append(dict(sample))
        else:
            raise TypeError(f"Unsupported source sample type: {type(sample)!r}")
    return normalized


def _selection_rank(sample_id: str, selection_seed: int) -> str:
    digest = hashlib.sha256(f"{selection_seed}|{sample_id}".encode("utf-8")).hexdigest()
    return digest


def select_source_samples(
    samples: Iterable[Any],
    *,
    split: str,
    max_samples: int,
    selection_seed: int,
) -> list[dict[str, Any]]:
    """Select a reproducible capped subset of source samples from one split."""
    if max_samples <= 0:
        raise ValueError("max_samples must be positive")

    normalized = _normalize_source_samples(samples)
    matching = [
        sample
        for sample in normalized
        if str(sample.get("split")) == str(split)
    ]
    if not matching:
        raise ValueError(f"No source samples were available for split {split!r}")

    ordered = sorted(
        matching,
        key=lambda sample: (
            _selection_rank(str(sample["sample_id"]), selection_seed),
            str(sample["sample_id"]),
        ),
    )
    return ordered[:max_samples]

