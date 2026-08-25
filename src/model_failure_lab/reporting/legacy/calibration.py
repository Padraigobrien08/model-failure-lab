# ruff: noqa: E402

"""Calibration reporting helpers for saved evaluation bundles."""

from __future__ import annotations

from model_failure_lab.utils.runtime import ensure_matplotlib_runtime_dir

ensure_matplotlib_runtime_dir()

import matplotlib

matplotlib.use("Agg")

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from .discovery import ReportCandidate
from .selection import report_label

_SLICE_ORDER = ["overall", "id", "ood"]


def build_calibration_table(candidates: list[ReportCandidate]) -> pd.DataFrame:
    """Build the compact calibration summary table for report packages."""
    rows: list[dict[str, object]] = []
    for candidate in candidates:
        calibration_summary = candidate.calibration_summary.copy()
        if calibration_summary.empty:
            continue
        for _, row in calibration_summary.iterrows():
            rows.append(
                {
                    "eval_id": candidate.eval_id,
                    "label": report_label(candidate),
                    "slice_name": row.get("slice_name"),
                    "ece": row.get("ece"),
                    "brier_score": row.get("brier_score"),
                    "sample_count": row.get("sample_count"),
                }
            )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["slice_name"] = pd.Categorical(frame["slice_name"], categories=_SLICE_ORDER, ordered=True)
    return frame.sort_values(by=["slice_name", "label"]).reset_index(drop=True)


def build_calibration_curve_figure(candidates: list[ReportCandidate]) -> Figure:
    """Build the Phase 5 calibration curve figure from saved bin rows."""
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharex=True, sharey=True)
    reference_line = [0.0, 1.0]

    for axis, slice_name in zip(axes, _SLICE_ORDER, strict=True):
        axis.plot(reference_line, reference_line, linestyle="--", color="gray", linewidth=1)
        for candidate in candidates:
            calibration_bins = candidate.calibration_bins.copy()
            if calibration_bins.empty:
                continue
            slice_frame = calibration_bins.loc[
                (calibration_bins["slice_name"] == slice_name)
                & (calibration_bins["count"].fillna(0).astype(float) > 0)
            ].copy()
            if slice_frame.empty:
                continue
            axis.plot(
                slice_frame["avg_confidence"].astype(float),
                slice_frame["empirical_accuracy"].astype(float),
                marker="o",
                label=report_label(candidate),
            )
        axis.set_title(slice_name.upper())
        axis.set_xlabel("Confidence")
        axis.set_xlim(0.0, 1.0)
        axis.set_ylim(0.0, 1.0)

    axes[0].set_ylabel("Empirical Accuracy")
    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="lower center", ncol=max(1, len(labels)))
    fig.suptitle("Calibration Curves")
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    return fig
