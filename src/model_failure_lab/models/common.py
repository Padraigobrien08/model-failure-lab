"""Shared baseline-training helpers."""

from __future__ import annotations

import random
from typing import Any

try:
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover - numpy is expected via project deps
    np = None

try:
    import torch
except ModuleNotFoundError:  # pragma: no cover - torch is expected via project deps
    torch = None

from sklearn.metrics import accuracy_score, f1_score, log_loss, roc_auc_score

from model_failure_lab.data import CanonicalDataset, prepare_civilcomments_runtime_dataset


def set_random_seed(seed: int) -> None:
    """Set the project-wide random seed across common ML libraries."""
    random.seed(seed)
    if np is not None:
        np.random.seed(seed)
    if torch is not None:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)


def load_baseline_canonical_dataset(
    config: dict[str, Any],
    *,
    download: bool = True,
    get_dataset_fn: Any | None = None,
) -> CanonicalDataset:
    """Load canonical CivilComments samples for a baseline run."""
    return prepare_civilcomments_runtime_dataset(
        config,
        download=download,
        get_dataset_fn=get_dataset_fn,
    ).dataset


def compute_binary_classification_metrics(
    *,
    true_labels: list[int],
    predicted_labels: list[int],
    probability_positive: list[float],
) -> dict[str, float | None]:
    """Compute the baseline comparison metrics used during training."""
    metrics: dict[str, float | None] = {
        "accuracy": float(accuracy_score(true_labels, predicted_labels)),
        "macro_f1": float(
            f1_score(true_labels, predicted_labels, average="macro", zero_division=0)
        ),
    }

    try:
        metrics["auroc"] = float(roc_auc_score(true_labels, probability_positive))
    except ValueError:
        metrics["auroc"] = None

    probability_rows = [[1.0 - score, score] for score in probability_positive]
    try:
        metrics["loss"] = float(log_loss(true_labels, probability_rows, labels=[0, 1]))
    except ValueError:
        metrics["loss"] = None

    return metrics
