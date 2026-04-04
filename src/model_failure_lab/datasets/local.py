"""Discover local dataset packs stored under the active artifact root."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from model_failure_lab.storage.layout import datasets_root

from .load import load_dataset


@dataclass(slots=True, frozen=True)
class LocalDatasetSummary:
    dataset_id: str
    name: str
    lifecycle: str
    case_count: int
    description: str
    path: Path


def available_local_datasets(*, root: str | Path | None = None) -> tuple[LocalDatasetSummary, ...]:
    dataset_dir = datasets_root(root=root, create=False)
    if not dataset_dir.exists():
        return ()

    summaries: list[LocalDatasetSummary] = []
    for candidate in sorted(dataset_dir.glob("*.json")):
        dataset = load_dataset(candidate)
        summaries.append(
            LocalDatasetSummary(
                dataset_id=dataset.dataset_id,
                name=dataset.name or dataset.dataset_id,
                lifecycle=dataset.lifecycle or "standard",
                case_count=len(dataset.cases),
                description=dataset.description or "",
                path=candidate,
            )
        )
    return tuple(summaries)
