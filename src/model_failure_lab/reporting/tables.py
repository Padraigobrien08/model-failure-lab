"""Compact report-table builders derived from saved evaluation bundles."""

from __future__ import annotations

import pandas as pd

from .discovery import ReportCandidate
from .figures import build_worst_subgroups_frame
from .selection import report_label


def build_comparison_table(comparison_frame: pd.DataFrame) -> pd.DataFrame:
    """Return the compact comparison table saved with report bundles."""
    if comparison_frame.empty:
        return comparison_frame
    return comparison_frame.loc[
        :,
        [
            "label",
            "id_score",
            "ood_score",
            "robustness_gap",
            "accuracy",
            "macro_f1",
            "auroc",
        ],
    ].copy()


def build_subgroup_table(
    candidates: list[ReportCandidate],
    *,
    top_k: int = 5,
    min_group_support: int | None = None,
) -> pd.DataFrame:
    """Return one compact subgroup table for the report package."""
    frames: list[pd.DataFrame] = []
    for candidate in candidates:
        subgroup_frame = build_worst_subgroups_frame(
            candidate,
            top_k=top_k,
            min_group_support=min_group_support,
        )
        if subgroup_frame.empty:
            continue
        prepared = subgroup_frame.copy()
        prepared.insert(0, "label", report_label(candidate))
        frames.append(prepared)

    if not frames:
        return pd.DataFrame(
            columns=["label", "group_name", "support", "accuracy", "macro_f1", "error_rate"]
        )
    return pd.concat(frames, ignore_index=True)
