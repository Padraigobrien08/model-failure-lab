"""Dataset contracts and loading helpers for the new failure-analysis engine."""

from pathlib import Path

from .bundled import (
    BundledDatasetSummary,
    UnknownBundledDatasetError,
    available_bundled_dataset_ids,
    available_bundled_datasets,
    describe_bundled_dataset,
    has_bundled_dataset,
    load_bundled_dataset,
)
from .contracts import FailureDataset
from .load import load_dataset, parse_dataset_payload

_DEMO_DATASET_FILENAME = "demo_dataset.json"


def demo_dataset_path() -> Path:
    """Return the bundled deterministic demo dataset path."""

    return Path(__file__).with_name(_DEMO_DATASET_FILENAME)


def load_demo_dataset() -> FailureDataset:
    """Load the bundled deterministic demo dataset."""

    return load_dataset(demo_dataset_path())


__all__ = [
    "BundledDatasetSummary",
    "FailureDataset",
    "UnknownBundledDatasetError",
    "available_bundled_datasets",
    "available_bundled_dataset_ids",
    "demo_dataset_path",
    "describe_bundled_dataset",
    "has_bundled_dataset",
    "load_dataset",
    "load_bundled_dataset",
    "load_demo_dataset",
    "parse_dataset_payload",
]
