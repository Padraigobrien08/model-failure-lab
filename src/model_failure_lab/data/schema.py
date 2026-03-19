"""Canonical CivilComments sample contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CanonicalSample:
    """Normalized record consumed by every downstream pipeline."""

    sample_id: str
    text: str
    label: int
    split: str
    is_id: bool
    is_ood: bool
    group_id: str
    group_attributes: dict[str, int]
    dataset_name: str
    raw_split: str
    raw_index: int | str | None = None
    source_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return the record as a JSON-serializable dictionary."""
        return asdict(self)


@dataclass(slots=True)
class CanonicalDataset:
    """Collection wrapper for canonical samples."""

    dataset_name: str
    samples: list[CanonicalSample]

    def to_records(self) -> list[dict[str, Any]]:
        """Return all samples as JSON-serializable dictionaries."""
        return [sample.to_dict() for sample in self.samples]
