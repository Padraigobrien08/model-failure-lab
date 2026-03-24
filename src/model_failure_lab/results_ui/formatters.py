"""Formatting helpers for the read-only results explorer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from model_failure_lab.utils.paths import repository_root

METRIC_LABELS = {
    "id_macro_f1": "ID Macro F1",
    "ood_macro_f1": "OOD Macro F1",
    "robustness_gap_f1": "Robustness Gap",
    "worst_group_f1": "Worst-Group F1",
    "ece": "ECE",
    "brier_score": "Brier",
}

KEY_OVERVIEW_METRICS = (
    "id_macro_f1",
    "robustness_gap_f1",
    "worst_group_f1",
)

DELTA_METRICS = (
    "id_macro_f1_delta",
    "ood_macro_f1_delta",
    "robustness_gap_delta",
    "worst_group_f1_delta",
    "ece_delta",
    "brier_score_delta",
)


def format_label(value: str | None) -> str:
    """Render a human-facing label from an underscore-delimited value."""
    if not value:
        return "Unknown"
    return value.replace("_", " ").strip().title()


def format_metric(value: Any) -> str:
    """Format one metric value for display."""
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)):
        return f"{value:.3f}"
    return str(value)


def format_delta(value: Any) -> str:
    """Format one signed metric delta for display."""
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)):
        return f"{value:+.3f}"
    return str(value)


def format_metric_label(metric_key: str) -> str:
    """Return a display label for a metric or delta key."""
    if metric_key in METRIC_LABELS:
        return METRIC_LABELS[metric_key]
    if metric_key.endswith("_delta"):
        base = metric_key[: -len("_delta")]
        return f"{METRIC_LABELS.get(base, format_label(base))} Delta"
    return format_label(metric_key)


def resolve_artifact_uri(relative_path: str | None) -> str | None:
    """Resolve a repo-relative artifact path into a local file URI."""
    if not relative_path:
        return None
    absolute_path = (repository_root() / relative_path).resolve()
    return absolute_path.as_uri()


def extract_ref_path(ref: Any) -> str | None:
    """Extract the repo-relative path from one manifest artifact ref."""
    if not isinstance(ref, dict):
        return None
    path = ref.get("path")
    if isinstance(path, str):
        return path
    return None


def build_action(
    *,
    label: str,
    path: str | None,
) -> dict[str, str] | None:
    """Build one clickable artifact action payload."""
    if not path:
        return None
    return {
        "label": label,
        "path": path,
        "uri": resolve_artifact_uri(path) or "",
    }


def build_bundle_action(
    entity: dict[str, Any],
    *,
    label: str,
) -> dict[str, str] | None:
    """Build one action that opens an entity bundle directory."""
    metadata_path = entity.get("metadata_path")
    if not isinstance(metadata_path, str):
        return None
    return build_action(label=label, path=str(Path(metadata_path).parent))


def build_artifact_ref_action(
    entity: dict[str, Any],
    *,
    label: str,
    ref_key: str,
    source: str = "artifact_refs",
) -> dict[str, str] | None:
    """Build one action from an entity artifact or payload ref key."""
    refs = entity.get(source, {})
    if not isinstance(refs, dict):
        return None
    return build_action(label=label, path=extract_ref_path(refs.get(ref_key)))


def build_metadata_actions(entity: dict[str, Any]) -> list[dict[str, str]]:
    """Build the standard raw-artifact actions for one entity."""
    actions: list[dict[str, str]] = []
    metadata_path = entity.get("metadata_path")
    if isinstance(metadata_path, str):
        bundle_label = "Open Bundle"
        entity_type = entity.get("entity_type")
        if entity_type == "run":
            bundle_label = "Open Run Bundle"
        elif entity_type == "evaluation":
            bundle_label = "Open Eval Bundle"
        elif entity_type == "report":
            bundle_label = "Open Report Bundle"

        bundle_action = build_bundle_action(entity, label=bundle_label)
        metadata_action = build_action(label="View Metadata", path=metadata_path)
        if bundle_action is not None:
            actions.append(bundle_action)
        if metadata_action is not None:
            actions.append(metadata_action)

    artifact_refs = entity.get("artifact_refs", {})
    report_action = build_action(
        label="View Report",
        path=extract_ref_path(artifact_refs.get("report_markdown")),
    )
    if report_action is not None:
        actions.insert(0, report_action)
    return actions
