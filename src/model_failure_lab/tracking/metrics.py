"""Metrics payload builders for run bundles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_metrics_payload(
    *,
    primary_metric: dict[str, Any],
    worst_group_metric: dict[str, Any],
    robustness_gap: dict[str, Any],
    calibration_metric: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the metrics payload with stable keys."""
    return {
        "primary_metric": primary_metric,
        "worst_group_metric": worst_group_metric,
        "robustness_gap": robustness_gap,
        "calibration_metric": calibration_metric,
    }


def write_metrics(
    run_dir: Path,
    metrics_payload: dict[str, Any],
    *,
    filename: str = "metrics.json",
) -> Path:
    """Write a metrics-style JSON payload into the run directory."""
    run_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = run_dir / filename
    metrics_path.write_text(json.dumps(metrics_payload, indent=2, sort_keys=True), encoding="utf-8")
    return metrics_path
