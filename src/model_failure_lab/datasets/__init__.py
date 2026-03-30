"""Dataset contracts and loading helpers for the new failure-analysis engine."""

from .contracts import FailureDataset
from .load import load_dataset, parse_dataset_payload

__all__ = ["FailureDataset", "load_dataset", "parse_dataset_payload"]
