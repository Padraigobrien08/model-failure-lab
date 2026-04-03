"""Bundled package-internal dataset registry and loading helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from importlib import resources

from .contracts import FailureDataset
from .load import parse_dataset_payload


@dataclass(slots=True, frozen=True)
class BundledDatasetSpec:
    """Metadata for one bundled dataset asset."""

    dataset_id: str
    resource_name: str


@dataclass(slots=True, frozen=True)
class BundledDatasetSummary:
    """Compact metadata for one bundled dataset."""

    dataset_id: str
    name: str
    target_failure_type: str
    default_scope: str
    core_case_count: int
    full_case_count: int
    description: str


_BUNDLED_DATASETS: dict[str, BundledDatasetSpec] = {
    "reasoning-failures-v1": BundledDatasetSpec(
        dataset_id="reasoning-failures-v1",
        resource_name="reasoning_failures.json",
    ),
    "hallucination-failures-v1": BundledDatasetSpec(
        dataset_id="hallucination-failures-v1",
        resource_name="hallucination_failures.json",
    ),
    "rag-failures-v1": BundledDatasetSpec(
        dataset_id="rag-failures-v1",
        resource_name="rag_failures.json",
    ),
}


class UnknownBundledDatasetError(LookupError):
    """Raised when a bundled dataset ID is not registered."""


def available_bundled_dataset_ids() -> tuple[str, ...]:
    """Return bundled dataset IDs in deterministic order."""

    return tuple(sorted(_BUNDLED_DATASETS))


def available_bundled_datasets() -> tuple[BundledDatasetSummary, ...]:
    """Return bundled dataset summaries in deterministic order."""

    return tuple(
        describe_bundled_dataset(dataset_id)
        for dataset_id in available_bundled_dataset_ids()
    )


def has_bundled_dataset(dataset_id: str) -> bool:
    """Return whether one bundled dataset ID is registered."""

    return dataset_id.strip() in _BUNDLED_DATASETS


def load_bundled_dataset(
    dataset_id: str,
    *,
    include_extended: bool = False,
) -> FailureDataset:
    """Load one bundled dataset, defaulting to the core subset when tagged."""

    spec = _resolve_bundled_dataset(dataset_id)
    dataset = _load_bundled_dataset_payload(spec)
    return _select_case_subset(dataset, include_extended=include_extended)


def describe_bundled_dataset(dataset_id: str) -> BundledDatasetSummary:
    """Return one compact bundled dataset summary."""

    spec = _resolve_bundled_dataset(dataset_id)
    dataset = _load_bundled_dataset_payload(spec)
    metadata = dataset.metadata
    target_failure_type = metadata.get("target_failure_type")
    default_scope = metadata.get("default_scope")
    description = dataset.description or ""
    core_case_count = len([case for case in dataset.cases if "core" in case.tags])
    if core_case_count == 0:
        core_case_count = len(dataset.cases)
    return BundledDatasetSummary(
        dataset_id=dataset.dataset_id,
        name=dataset.name or dataset.dataset_id,
        target_failure_type=(
            target_failure_type if isinstance(target_failure_type, str) else "unknown"
        ),
        default_scope=default_scope if isinstance(default_scope, str) else "full",
        core_case_count=core_case_count,
        full_case_count=len(dataset.cases),
        description=description,
    )


def _resolve_bundled_dataset(dataset_id: str) -> BundledDatasetSpec:
    normalized = dataset_id.strip()
    try:
        return _BUNDLED_DATASETS[normalized]
    except KeyError as exc:
        raise UnknownBundledDatasetError(f"unknown bundled dataset: {normalized}") from exc


def _select_case_subset(
    dataset: FailureDataset,
    *,
    include_extended: bool,
) -> FailureDataset:
    if include_extended:
        return dataset

    core_cases = tuple(case for case in dataset.cases if "core" in case.tags)
    if not core_cases:
        return dataset
    return replace(dataset, cases=core_cases)


def _load_bundled_dataset_payload(spec: BundledDatasetSpec) -> FailureDataset:
    resource = resources.files("model_failure_lab.datasets").joinpath(spec.resource_name)
    try:
        payload = json.loads(resource.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "Bundled dataset asset "
            f"`{spec.resource_name}` for `{spec.dataset_id}` is missing from the installed "
            "`model-failure-lab` package. Reinstall `model-failure-lab` or rebuild the package "
            "so `model_failure_lab/datasets/*.json` is included."
        ) from exc
    return parse_dataset_payload(payload, fallback_dataset_id=spec.dataset_id)
