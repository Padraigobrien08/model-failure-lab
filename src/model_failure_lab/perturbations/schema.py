"""Perturbation suite contracts and deterministic lineage helpers."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import Any

SCHEMA_VERSION = "perturbation-suite-v1"


def build_perturbed_sample_id(
    source_sample_id: str,
    family: str,
    severity: str,
    perturbation_seed: int,
    text: str,
) -> str:
    """Build a stable perturbation identifier from source lineage and text."""
    basis = f"{source_sample_id}|{family}|{severity}|{perturbation_seed}|{text}"
    digest = hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]
    return f"perturbed_{digest}"


@dataclass(frozen=True, slots=True)
class PerturbedSample:
    """Synthetic stress-test sample with explicit source lineage."""

    perturbed_sample_id: str
    source_sample_id: str
    perturbation_family: str
    severity: str
    perturbation_seed: int
    text: str
    true_label: int
    source_split: str
    source_group_id: str
    source_is_id: bool
    source_is_ood: bool
    dataset_name: str
    applied_operations: list[dict[str, Any]] = field(default_factory=list)
    source_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return the perturbation sample as a JSON-serializable dictionary."""
        return asdict(self)


@dataclass(slots=True)
class PerturbationSuite:
    """Collection wrapper for one saved run's perturbation expansion."""

    source_run_id: str
    model_name: str
    dataset_name: str
    source_split: str
    selection_seed: int
    perturbation_seed: int
    families: list[str]
    severities: list[str]
    source_sample_count: int
    samples: list[PerturbedSample]
    schema_version: str = SCHEMA_VERSION

    @property
    def perturbed_sample_count(self) -> int:
        return len(self.samples)

    def to_records(self) -> list[dict[str, Any]]:
        """Return all perturbation samples as JSON-serializable dictionaries."""
        return [sample.to_dict() for sample in self.samples]

