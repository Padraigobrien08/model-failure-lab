"""Manifest builders for the Phase 21 artifact index contract."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from model_failure_lab.tracking.manifest import utc_now_timestamp
from model_failure_lab.utils.paths import (
    artifact_root,
    build_artifact_index_path,
    repository_root,
)

from .schema import (
    ARTIFACT_INDEX_SCHEMA_VERSION,
    DEFAULT_VISIBLE_REPORT_SCOPES,
    METRIC_KEYS,
    OFFICIAL_REPORT_SCOPE_PREFIXES,
    OFFICIAL_RUN_GROUPS,
    PRIMARY_COHORT_DEFINITIONS,
    PRIMARY_COHORT_ORDER,
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _is_completed(metadata: dict[str, Any]) -> bool:
    return metadata.get("status") in {None, "completed"}


def _iter_metadata_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(sorted(artifact_root().glob(pattern)))
    return sorted(path.resolve() for path in paths)


def _iter_run_metadata_paths() -> list[Path]:
    return _iter_metadata_paths(
        [
            "baselines/*/*/metadata.json",
            "mitigations/*/*/*/metadata.json",
        ]
    )


def _iter_evaluation_metadata_paths() -> list[Path]:
    return _iter_metadata_paths(
        [
            "baselines/*/*/evaluations/*/metadata.json",
            "mitigations/*/*/*/evaluations/*/metadata.json",
        ]
    )


def _iter_report_metadata_paths() -> list[Path]:
    return _iter_metadata_paths(["reports/*/*/*/metadata.json"])


def _iter_final_gate_paths() -> list[Path]:
    return _iter_metadata_paths(["reports/closeout/*/final_gate.json"])


def _extract_seed(metadata: dict[str, Any]) -> str | None:
    for tag_source in (
        metadata.get("tags", []),
        metadata.get("resolved_config", {}).get("tags", []),
    ):
        if not isinstance(tag_source, list):
            continue
        for tag in tag_source:
            text = str(tag)
            if text.startswith("seed_"):
                return text.split("_", 1)[1]
    for key in ("random_seed",):
        value = metadata.get(key)
        if value is not None:
            return str(int(value))
    resolved_config = metadata.get("resolved_config", {})
    if isinstance(resolved_config, dict) and resolved_config.get("seed") is not None:
        return str(int(resolved_config["seed"]))
    return None


def _sort_seed(value: str) -> tuple[int, str]:
    if value.isdigit():
        return (0, f"{int(value):08d}")
    return (1, value)


def _canonical_artifact_relative(path: Path) -> str:
    parts = list(path.parts)
    if "artifacts" in parts:
        return str(Path(*parts[parts.index("artifacts") :]))
    try:
        return str(path.resolve().relative_to(repository_root()))
    except ValueError:
        return path.as_posix()


def _resolve_artifact_path(raw_path: str, *, metadata_path: Path) -> tuple[str, bool]:
    raw_candidate = Path(raw_path)
    candidates: list[Path] = []
    if raw_candidate.is_absolute():
        candidates.append(raw_candidate)
        if "artifacts" in raw_candidate.parts:
            relative_artifact = Path(
                *raw_candidate.parts[raw_candidate.parts.index("artifacts") + 1 :]
            )
            candidates.append(artifact_root() / relative_artifact)
            candidates.append(repository_root() / "artifacts" / relative_artifact)
        candidates.append(metadata_path.parent / raw_candidate.name)
    else:
        candidates.append(metadata_path.parent / raw_candidate)
        candidates.append(artifact_root() / raw_candidate)
        candidates.append(metadata_path.parent / raw_candidate.name)

    for candidate in candidates:
        if candidate.exists():
            return _canonical_artifact_relative(candidate), True

    if "artifacts" in raw_candidate.parts:
        relative_artifact = Path(*raw_candidate.parts[raw_candidate.parts.index("artifacts") :])
        return str(relative_artifact), (
            artifact_root() / Path(*relative_artifact.parts[1:])
        ).exists()
    return _canonical_artifact_relative(candidates[0]), False


def _normalize_artifact_refs(value: Any, *, metadata_path: Path) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _normalize_artifact_refs(item, metadata_path=metadata_path)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_normalize_artifact_refs(item, metadata_path=metadata_path) for item in value]
    if isinstance(value, str):
        relative_path, exists = _resolve_artifact_path(value, metadata_path=metadata_path)
        return {"path": relative_path, "exists": exists}
    return value


def _payload_ref(
    metadata_path: Path, artifact_paths: dict[str, Any], key: str
) -> dict[str, Any] | None:
    raw_value = artifact_paths.get(key)
    if not isinstance(raw_value, str):
        return None
    relative_path, exists = _resolve_artifact_path(raw_value, metadata_path=metadata_path)
    return {"path": relative_path, "exists": exists}


def _materialize_relative_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.parts and candidate.parts[0] == "artifacts":
        return artifact_root() / Path(*candidate.parts[1:])
    return repository_root() / candidate


def _load_json_payload(ref: dict[str, Any] | None) -> dict[str, Any] | None:
    if ref is None or not ref.get("exists"):
        return None
    path = _materialize_relative_path(str(ref["path"]))
    if not path.exists():
        return None
    return _read_json(path)


def _build_run_entity(metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    experiment_group = str(metadata.get("experiment_group") or "")
    tags = [str(tag) for tag in metadata.get("tags", [])]
    is_scout = "scout" in tags
    is_official = bool(
        not is_scout
        and ("official" in tags or experiment_group in OFFICIAL_RUN_GROUPS)
    )
    return {
        "id": str(metadata["run_id"]),
        "entity_type": "run",
        "run_id": str(metadata["run_id"]),
        "experiment_type": str(metadata.get("experiment_type", "")),
        "experiment_group": experiment_group or None,
        "model_name": str(metadata.get("model_name", "")),
        "dataset_name": str(metadata.get("dataset_name", "")),
        "status": metadata.get("status"),
        "seed": _extract_seed(metadata),
        "parent_run_id": metadata.get("parent_run_id"),
        "mitigation_method": metadata.get("mitigation_method"),
        "split_details": metadata.get("split_details", {}),
        "metadata_path": _canonical_artifact_relative(metadata_path),
        "artifact_refs": _normalize_artifact_refs(
            metadata.get("artifact_paths", {}), metadata_path=metadata_path
        ),
        "notes": metadata.get("notes", ""),
        "tags": tags,
        "timestamp": metadata.get("timestamp"),
        "started_at": metadata.get("started_at"),
        "completed_at": metadata.get("completed_at"),
        "duration_seconds": metadata.get("duration_seconds"),
        "training_summary": metadata.get("training_summary"),
        "is_official": is_official,
        "default_visible": is_official,
    }


def _headline_metrics_from_ui(
    ui_summary: dict[str, Any] | None, overall_metrics: dict[str, Any] | None
) -> dict[str, Any]:
    if isinstance(ui_summary, dict):
        headline = ui_summary.get("headline_metrics")
        if isinstance(headline, dict):
            return dict(headline)
    if isinstance(overall_metrics, dict):
        headline = overall_metrics.get("headline_metrics")
        if isinstance(headline, dict):
            return dict(headline)
    return {}


def _build_evaluation_entity(metadata_path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    experiment_group = str(metadata.get("experiment_group") or "")
    tags = [str(tag) for tag in metadata.get("tags", [])]
    artifact_paths = dict(metadata.get("artifact_paths", {}))
    ui_summary_ref = _payload_ref(metadata_path, artifact_paths, "ui_summary_json")
    overall_metrics_ref = _payload_ref(metadata_path, artifact_paths, "overall_metrics_json")
    headline_metrics = _headline_metrics_from_ui(
        _load_json_payload(ui_summary_ref),
        _load_json_payload(overall_metrics_ref),
    )
    is_scout = "scout" in tags
    is_official = bool(
        not is_scout
        and ("official" in tags or experiment_group in OFFICIAL_RUN_GROUPS)
    )
    return {
        "id": str(metadata["eval_id"]),
        "entity_type": "evaluation",
        "eval_id": str(metadata["eval_id"]),
        "experiment_group": experiment_group or None,
        "model_name": str(metadata.get("model_name", "")),
        "dataset_name": str(metadata.get("dataset_name", "")),
        "seed": _extract_seed(metadata),
        "source_run_id": metadata.get("source_run_id"),
        "source_parent_run_id": metadata.get("source_parent_run_id"),
        "mitigation_method": metadata.get("mitigation_method"),
        "status": metadata.get("status"),
        "metadata_path": _canonical_artifact_relative(metadata_path),
        "artifact_refs": _normalize_artifact_refs(artifact_paths, metadata_path=metadata_path),
        "payload_refs": {
            "ui_summary_json": ui_summary_ref,
            "overall_metrics_json": overall_metrics_ref,
        },
        "headline_metrics": headline_metrics,
        "tags": tags,
        "is_official": is_official,
        "default_visible": is_official,
    }


def _is_curated_report_scope(report_scope: str) -> bool:
    return any(
        report_scope == prefix or report_scope.startswith(prefix)
        for prefix in OFFICIAL_REPORT_SCOPE_PREFIXES
    )


def _report_default_visible(report_scope: str) -> bool:
    return report_scope in DEFAULT_VISIBLE_REPORT_SCOPES


def _build_report_entity(
    metadata_path: Path,
    metadata: dict[str, Any],
    *,
    official_eval_ids: set[str],
) -> dict[str, Any]:
    report_scope = str(metadata.get("report_scope") or metadata.get("experiment_group") or "")
    artifact_paths = dict(metadata.get("artifact_paths", {}))
    report_data_ref = _payload_ref(metadata_path, artifact_paths, "report_data_json")
    report_summary_ref = _payload_ref(metadata_path, artifact_paths, "report_summary_json")
    stability_summary_ref = _payload_ref(metadata_path, artifact_paths, "stability_summary_json")
    report_data = _load_json_payload(report_data_ref)
    report_summary = _load_json_payload(report_summary_ref)
    stability_summary = _load_json_payload(stability_summary_ref)
    source_eval_ids = [str(item) for item in metadata.get("source_eval_ids", [])]
    source_closure_official = bool(source_eval_ids) and all(
        eval_id in official_eval_ids for eval_id in source_eval_ids
    )
    is_official = _is_curated_report_scope(report_scope) and source_closure_official
    tags = [str(tag) for tag in metadata.get("tags", [])]
    report_summary_payload = None
    if isinstance(report_summary, dict):
        report_summary_payload = report_summary
    elif isinstance(report_data, dict) and isinstance(report_data.get("report_summary"), dict):
        report_summary_payload = dict(report_data["report_summary"])
    return {
        "id": str(metadata["report_id"]),
        "entity_type": "report",
        "report_id": str(metadata["report_id"]),
        "experiment_type": str(metadata.get("experiment_type", "")),
        "experiment_group": str(metadata.get("experiment_group") or "") or None,
        "report_scope": report_scope or None,
        "selection_mode": metadata.get("selection_mode"),
        "source_eval_ids": source_eval_ids,
        "cohort_eval_ids": metadata.get("cohort_eval_ids"),
        "status": metadata.get("status"),
        "metadata_path": _canonical_artifact_relative(metadata_path),
        "artifact_refs": _normalize_artifact_refs(artifact_paths, metadata_path=metadata_path),
        "payload_refs": {
            "report_data_json": report_data_ref,
            "report_summary_json": report_summary_ref,
            "stability_summary_json": stability_summary_ref,
        },
        "summary_snapshot": report_summary_payload,
        "stability_snapshot": stability_summary,
        "tags": tags,
        "is_official": is_official,
        "default_visible": bool(is_official and _report_default_visible(report_scope)),
    }


def _mean_std(records: list[dict[str, Any]]) -> dict[str, dict[str, float | None]]:
    mean_metrics: dict[str, float | None] = {}
    std_metrics: dict[str, float | None] = {}
    for key in METRIC_KEYS:
        values = [float(record[key]) for record in records if record.get(key) is not None]
        if not values:
            mean_metrics[key] = None
            std_metrics[key] = None
            continue
        mean_metrics[key] = float(mean(values))
        std_metrics[key] = float(pstdev(values))
    return {"mean": mean_metrics, "std": std_metrics}


def _build_seeded_cohort_views(
    evaluations: list[dict[str, Any]], reports: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    report_lookup = {
        str(report.get("report_scope")): report for report in reports if report.get("is_official")
    }
    views: list[dict[str, Any]] = []
    for experiment_group, definition in PRIMARY_COHORT_DEFINITIONS.items():
        cohort_evals = [
            entity
            for entity in evaluations
            if entity.get("experiment_group") == experiment_group and entity.get("is_official")
        ]
        if not cohort_evals:
            continue
        per_seed = []
        for entity in sorted(
            cohort_evals,
            key=lambda item: _sort_seed(str(item.get("seed") or "")),
        ):
            headline = dict(entity.get("headline_metrics", {}))
            per_seed.append(
                {
                    "seed": entity.get("seed"),
                    "run_id": entity.get("source_run_id"),
                    "eval_id": entity.get("eval_id"),
                    "id_macro_f1": headline.get("macro_f1")
                    if headline.get("macro_f1") is not None
                    else headline.get("id_macro_f1"),
                    "ood_macro_f1": headline.get("ood_macro_f1"),
                    "robustness_gap_f1": headline.get("robustness_gap_f1"),
                    "worst_group_f1": headline.get("worst_group_f1"),
                    "ece": headline.get("ece"),
                    "brier_score": headline.get("brier_score"),
                }
            )
        aggregates = _mean_std(per_seed)
        linked_report_scope = (
            "phase18_temperature_scaling_seeded"
            if definition["cohort_id"] == "temperature_scaling"
            else "phase19_reweighting_seeded"
            if definition["cohort_id"] == "reweighting"
            else None
        )
        linked_report_id = None
        if linked_report_scope is not None and linked_report_scope in report_lookup:
            linked_report_id = report_lookup[linked_report_scope]["report_id"]
        views.append(
            {
                "cohort_id": definition["cohort_id"],
                "display_name": definition["display_name"],
                "cohort_type": definition["cohort_type"],
                "model_name": definition["model_name"],
                "mitigation_method": definition["mitigation_method"],
                "experiment_group": experiment_group,
                "seed_ids": [row["seed"] for row in per_seed],
                "run_ids": [str(entity.get("source_run_id")) for entity in cohort_evals],
                "evaluation_ids": [str(entity.get("eval_id")) for entity in cohort_evals],
                "per_seed_metrics": per_seed,
                "aggregate_metrics": aggregates,
                "linked_report_id": linked_report_id,
                "is_official": True,
                "default_visible": True,
            }
        )
    return sorted(
        views,
        key=lambda item: PRIMARY_COHORT_ORDER.index(str(item["cohort_id"])),
    )


def _report_ids_for_prefix(
    reports: list[dict[str, Any]],
    *,
    prefix: str,
) -> dict[str, list[str]]:
    seed_report_ids: dict[str, list[str]] = defaultdict(list)
    for report in reports:
        scope = str(report.get("report_scope") or "")
        if not report.get("is_official") or not scope.startswith(prefix):
            continue
        seed = scope.rsplit("_", 1)[-1]
        seed_report_ids[seed].append(str(report["report_id"]))
    return dict(seed_report_ids)


def _build_mitigation_comparison_views(
    evaluations: list[dict[str, Any]],
    reports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    eval_lookup = {str(entity["eval_id"]): entity for entity in evaluations}
    stability_report = next(
        (
            report
            for report in reports
            if report.get("report_scope") == "phase20_stability" and report.get("is_official")
        ),
        None,
    )
    stability_summary = (
        dict(stability_report.get("stability_snapshot", {}))
        if isinstance(stability_report, dict)
        and isinstance(stability_report.get("stability_snapshot"), dict)
        else {}
    )
    cohort_summaries = stability_summary.get("cohort_summaries", {})
    report_by_scope = {
        str(report.get("report_scope")): report for report in reports if report.get("is_official")
    }
    view_specs = [
        {
            "method": "temperature_scaling",
            "report_scope": "phase18_temperature_scaling_seeded",
            "seed_report_prefix": "phase18_temperature_scaling_seed_",
        },
        {
            "method": "reweighting",
            "report_scope": "phase19_reweighting_seeded",
            "seed_report_prefix": "phase19_reweighting_seed_",
            "extra_seed_prefix": "phase19_three_way_seed_",
        },
    ]
    views: list[dict[str, Any]] = []
    for spec in view_specs:
        report = report_by_scope.get(spec["report_scope"])
        if report is None:
            continue
        report_data_ref = report.get("payload_refs", {}).get("report_data_json")
        report_data = (
            _load_json_payload(report_data_ref) if isinstance(report_data_ref, dict) else None
        )
        if not isinstance(report_data, dict):
            continue
        mitigation_rows = [
            dict(row)
            for row in report_data.get("mitigation_comparison_table", [])
            if str(row.get("mitigation_method")) == spec["method"]
        ]
        per_seed_entries = []
        for row in mitigation_rows:
            child_eval = eval_lookup.get(str(row.get("mitigation_eval_id")))
            parent_eval = eval_lookup.get(str(row.get("parent_eval_id")))
            seed = None
            child_run_id = None
            parent_run_id = None
            if child_eval is not None:
                seed = child_eval.get("seed")
                child_run_id = child_eval.get("source_run_id")
            if parent_eval is not None:
                parent_run_id = parent_eval.get("source_run_id")
            seed_text = str(seed) if seed is not None else ""
            related_report_ids = _report_ids_for_prefix(
                reports,
                prefix=spec["seed_report_prefix"],
            ).get(seed_text, [])
            extra_prefix = spec.get("extra_seed_prefix")
            if isinstance(extra_prefix, str):
                related_report_ids.extend(
                    _report_ids_for_prefix(reports, prefix=extra_prefix).get(seed_text, [])
                )
            per_seed_entries.append(
                {
                    "seed": seed,
                    "parent_eval_id": row.get("parent_eval_id"),
                    "child_eval_id": row.get("mitigation_eval_id"),
                    "parent_run_id": parent_run_id,
                    "child_run_id": child_run_id,
                    "verdict": row.get("verdict"),
                    "deltas": {
                        "id_macro_f1_delta": row.get("id_macro_f1_delta"),
                        "ood_macro_f1_delta": row.get("ood_macro_f1_delta"),
                        "robustness_gap_delta": row.get("robustness_gap_delta"),
                        "worst_group_f1_delta": row.get("worst_group_f1_delta"),
                        "ece_delta": row.get("ece_delta"),
                        "brier_score_delta": row.get("brier_score_delta"),
                    },
                    "related_report_ids": related_report_ids,
                }
            )
        method_summaries = report_data.get("mitigation_method_summaries", {})
        method_summary = (
            dict(method_summaries.get(spec["method"], {}))
            if isinstance(method_summaries, dict)
            else {}
        )
        report_summary = report.get("summary_snapshot", {}) or {}
        comparison_summary = {
            "report_id": report["report_id"],
            "report_scope": report.get("report_scope"),
            "report_markdown": report.get("artifact_refs", {}).get("report_markdown"),
            "seeded_interpretation": method_summary.get("seeded_interpretation")
            or report_summary.get("seeded_interpretation"),
            "verdict_counts": method_summary.get("verdict_counts")
            or report_summary.get("mitigation_verdict_counts"),
        }
        stability_assessment = {}
        if isinstance(cohort_summaries, dict) and isinstance(
            cohort_summaries.get(spec["method"]), dict
        ):
            stability_assessment = dict(cohort_summaries[spec["method"]])
        views.append(
            {
                "view_id": spec["method"],
                "mitigation_method": spec["method"],
                "aggregate_report_id": report["report_id"],
                "aggregate_report_scope": report.get("report_scope"),
                "comparison_summary": comparison_summary,
                "per_seed_comparisons": sorted(
                    per_seed_entries,
                    key=lambda item: _sort_seed(str(item.get("seed") or "")),
                ),
                "stability_assessment": stability_assessment,
                "is_official": True,
                "default_visible": True,
            }
        )
    return views


def _normalize_reference_reports(reference_reports: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in reference_reports.items():
        if not value:
            normalized[str(key)] = None
            continue
        relative_path, exists = _resolve_artifact_path(
            str(value), metadata_path=artifact_root() / "reports"
        )
        normalized[str(key)] = {"path": relative_path, "exists": exists}
    return normalized


def _build_stability_package_views(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    views: list[dict[str, Any]] = []
    for report in reports:
        if report.get("experiment_type") != "stability_report" or not report.get("is_official"):
            continue
        stability_snapshot = report.get("stability_snapshot")
        if not isinstance(stability_snapshot, dict):
            continue
        milestone_assessment = dict(stability_snapshot.get("milestone_assessment", {}))
        views.append(
            {
                "package_id": str(report["report_id"]),
                "report_id": str(report["report_id"]),
                "report_scope": report.get("report_scope"),
                "cohort_summaries": stability_snapshot.get("cohort_summaries", {}),
                "baseline_model_comparison": stability_snapshot.get(
                    "baseline_model_comparison", {}
                ),
                "milestone_assessment": milestone_assessment,
                "reference_reports": _normalize_reference_reports(
                    dict(stability_snapshot.get("reference_reports", {}))
                ),
                "is_official": True,
                "default_visible": True,
            }
        )
    return views


def _build_research_closeout_views(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    report_ids_by_scope = {
        str(report.get("report_scope")): str(report.get("report_id"))
        for report in reports
        if report.get("is_official") and report.get("report_scope")
    }
    views: list[dict[str, Any]] = []
    for final_gate_path in _iter_final_gate_paths():
        payload = _read_json(final_gate_path)
        supporting_scopes = [
            str(scope)
            for scope in payload.get("supporting_report_scopes", [])
            if str(scope).strip()
        ]
        supporting_report_ids = [
            report_ids_by_scope[scope]
            for scope in supporting_scopes
            if scope in report_ids_by_scope
        ]
        artifact_refs_payload = dict(payload.get("supporting_artifact_refs", {}))
        artifact_refs_payload.setdefault(
            "final_gate_json",
            _canonical_artifact_relative(final_gate_path),
        )
        views.append(
            {
                "view_id": str(payload.get("gate_id") or final_gate_path.parent.name),
                "final_robustness_verdict": payload.get("final_robustness_verdict"),
                "dataset_expansion_decision": payload.get("dataset_expansion_decision"),
                "recommendation_reason": payload.get("recommendation_reason"),
                "reopen_conditions": list(payload.get("reopen_conditions", [])),
                "summary_bullets": list(payload.get("summary_bullets", [])),
                "next_step": payload.get("next_step"),
                "supporting_report_scopes": supporting_scopes,
                "supporting_report_ids": supporting_report_ids,
                "artifact_refs": _normalize_artifact_refs(
                    artifact_refs_payload,
                    metadata_path=final_gate_path,
                ),
                "promotion_audit": dict(payload.get("promotion_audit", {})),
                "official_methods": list(payload.get("official_methods", [])),
                "exploratory_methods": list(payload.get("exploratory_methods", [])),
                "findings_doc_path": payload.get("findings_doc_path"),
                "ui_entrypoint_path": payload.get("ui_entrypoint_path"),
                "metadata_path": _canonical_artifact_relative(final_gate_path),
                "is_official": bool(payload.get("is_official", False)),
                "default_visible": bool(payload.get("default_visible", False)),
            }
        )
    return views


def build_artifact_index_payload() -> dict[str, Any]:
    """Build the full artifact-index payload from saved artifacts."""
    run_entities = []
    for metadata_path in _iter_run_metadata_paths():
        metadata = _read_json(metadata_path)
        if not _is_completed(metadata):
            continue
        run_entities.append(_build_run_entity(metadata_path, metadata))

    evaluation_entities = []
    for metadata_path in _iter_evaluation_metadata_paths():
        metadata = _read_json(metadata_path)
        if not _is_completed(metadata):
            continue
        evaluation_entities.append(_build_evaluation_entity(metadata_path, metadata))

    official_eval_ids = {
        str(entity["eval_id"]) for entity in evaluation_entities if entity.get("is_official")
    }
    report_entities = []
    for metadata_path in _iter_report_metadata_paths():
        metadata = _read_json(metadata_path)
        if not _is_completed(metadata):
            continue
        if str(metadata.get("experiment_type", "")) not in {
            "report",
            "stability_report",
            "robustness_report",
        }:
            continue
        report_entities.append(
            _build_report_entity(
                metadata_path,
                metadata,
                official_eval_ids=official_eval_ids,
            )
        )

    return {
        "schema_version": ARTIFACT_INDEX_SCHEMA_VERSION,
        "generated_at": utc_now_timestamp(),
        "artifact_root": "artifacts",
        "default_filters": {"official_only": True},
        "entities": {
            "runs": run_entities,
            "evaluations": evaluation_entities,
            "reports": report_entities,
        },
        "views": {
            "seeded_cohorts": _build_seeded_cohort_views(evaluation_entities, report_entities),
            "mitigation_comparisons": _build_mitigation_comparison_views(
                evaluation_entities,
                report_entities,
            ),
            "stability_packages": _build_stability_package_views(report_entities),
            "research_closeout": _build_research_closeout_views(report_entities),
        },
    }


def write_artifact_index(*, version: str = "v1") -> Path:
    """Build and persist the artifact-index payload to the canonical location."""
    output_path = build_artifact_index_path(version=version, create=True)
    _write_json(output_path, build_artifact_index_payload())
    return output_path
