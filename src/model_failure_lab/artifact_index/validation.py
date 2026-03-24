"""Validation helpers for the generated artifact-index contract."""

from __future__ import annotations

from typing import Any

from .schema import ARTIFACT_INDEX_SCHEMA_VERSION


def _iter_ref_paths(value: Any) -> list[tuple[str, bool]]:
    refs: list[tuple[str, bool]] = []
    if isinstance(value, dict):
        if "path" in value and isinstance(value["path"], str):
            refs.append((value["path"], bool(value.get("exists", False))))
        else:
            for item in value.values():
                refs.extend(_iter_ref_paths(item))
    elif isinstance(value, list):
        for item in value:
            refs.extend(_iter_ref_paths(item))
    return refs


def validate_artifact_index_payload(payload: dict[str, Any]) -> list[str]:
    """Return validation errors for one artifact-index payload."""
    errors: list[str] = []
    if payload.get("schema_version") != ARTIFACT_INDEX_SCHEMA_VERSION:
        errors.append("schema_version must be artifact_index_v1")
    if payload.get("default_filters", {}).get("official_only") is not True:
        errors.append("default_filters.official_only must be true")

    entities = payload.get("entities")
    views = payload.get("views")
    if not isinstance(entities, dict):
        errors.append("entities section is missing")
        return errors
    if not isinstance(views, dict):
        errors.append("views section is missing")
        return errors

    for key in ("runs", "evaluations", "reports"):
        if not isinstance(entities.get(key), list):
            errors.append(f"entities.{key} must be a list")
    for key in (
        "seeded_cohorts",
        "mitigation_comparisons",
        "stability_packages",
        "research_closeout",
    ):
        if not isinstance(views.get(key), list):
            errors.append(f"views.{key} must be a list")

    runs = entities.get("runs", [])
    evaluations = entities.get("evaluations", [])
    reports = entities.get("reports", [])

    run_ids = {str(entity.get("run_id")) for entity in runs}
    eval_ids = {str(entity.get("eval_id")) for entity in evaluations}
    report_ids = {str(entity.get("report_id")) for entity in reports}
    official_eval_ids = {
        str(entity.get("eval_id")) for entity in evaluations if entity.get("is_official")
    }

    seen_ids: set[tuple[str, str]] = set()
    for collection_name, rows, id_key in (
        ("runs", runs, "run_id"),
        ("evaluations", evaluations, "eval_id"),
        ("reports", reports, "report_id"),
    ):
        for row in rows:
            item_id = str(row.get(id_key))
            if not item_id:
                errors.append(f"{collection_name} entity missing {id_key}")
                continue
            composite = (collection_name, item_id)
            if composite in seen_ids:
                errors.append(f"duplicate {collection_name} entity id: {item_id}")
            seen_ids.add(composite)
            if row.get("default_visible") and not row.get("is_official"):
                errors.append(
                    f"{collection_name} entity {item_id} is default_visible without is_official"
                )
            for path, exists in _iter_ref_paths(row.get("artifact_refs", {})):
                if path.startswith("/Users/") or path.startswith("/workspace/"):
                    errors.append(
                        f"{collection_name} entity {item_id} contains absolute artifact "
                        f"path: {path}"
                    )
                if row.get("is_official") and not exists:
                    errors.append(
                        f"{collection_name} entity {item_id} references missing artifact "
                        f"path: {path}"
                    )
            metadata_path = row.get("metadata_path")
            if isinstance(metadata_path, str) and (
                metadata_path.startswith("/Users/") or metadata_path.startswith("/workspace/")
            ):
                errors.append(
                    f"{collection_name} entity {item_id} has absolute metadata_path: "
                    f"{metadata_path}"
                )

    for row in evaluations:
        eval_id = str(row.get("eval_id"))
        source_run_id = row.get("source_run_id")
        if source_run_id not in run_ids:
            errors.append(f"evaluation {eval_id} references unknown source_run_id: {source_run_id}")
        source_parent_run_id = row.get("source_parent_run_id")
        if source_parent_run_id is not None and source_parent_run_id not in run_ids:
            errors.append(
                f"evaluation {eval_id} references unknown source_parent_run_id: "
                f"{source_parent_run_id}"
            )

    for row in reports:
        report_id = str(row.get("report_id"))
        source_eval_ids_list = [str(item) for item in row.get("source_eval_ids", [])]
        missing_eval_ids = sorted(set(source_eval_ids_list) - eval_ids)
        if missing_eval_ids:
            errors.append(
                f"report {report_id} references unknown source_eval_ids: "
                f"{', '.join(missing_eval_ids)}"
            )
        if row.get("is_official") and not set(source_eval_ids_list).issubset(official_eval_ids):
            errors.append(
                f"report {report_id} is marked official without official source-eval closure"
            )

    for view in views.get("seeded_cohorts", []):
        cohort_id = str(view.get("cohort_id"))
        for eval_id in view.get("evaluation_ids", []):
            if str(eval_id) not in eval_ids:
                errors.append(
                    f"seeded cohort {cohort_id} references unknown evaluation id: {eval_id}"
                )
        if view.get("default_visible") and not view.get("is_official"):
            errors.append(f"seeded cohort {cohort_id} is default_visible without is_official")

    for view in views.get("mitigation_comparisons", []):
        view_id = str(view.get("view_id"))
        aggregate_report_id = str(view.get("aggregate_report_id"))
        if aggregate_report_id not in report_ids:
            errors.append(
                f"mitigation comparison {view_id} references unknown aggregate_report_id: "
                f"{aggregate_report_id}"
            )
        comparison_summary = view.get("comparison_summary", {})
        if (
            not isinstance(comparison_summary, dict)
            or comparison_summary.get("seeded_interpretation") is None
        ):
            errors.append(
                f"mitigation comparison {view_id} is missing "
                f"comparison_summary.seeded_interpretation"
            )
        stability_assessment = view.get("stability_assessment", {})
        if not isinstance(stability_assessment, dict) or stability_assessment.get("label") is None:
            errors.append(f"mitigation comparison {view_id} is missing stability_assessment.label")
        for row in view.get("per_seed_comparisons", []):
            parent_eval_id = str(row.get("parent_eval_id"))
            child_eval_id = str(row.get("child_eval_id"))
            if parent_eval_id not in eval_ids:
                errors.append(
                    f"mitigation comparison {view_id} references unknown parent_eval_id: "
                    f"{parent_eval_id}"
                )
            if child_eval_id not in eval_ids:
                errors.append(
                    f"mitigation comparison {view_id} references unknown child_eval_id: "
                    f"{child_eval_id}"
                )

    for view in views.get("stability_packages", []):
        package_id = str(view.get("package_id"))
        report_id = str(view.get("report_id"))
        if report_id not in report_ids:
            errors.append(
                f"stability package {package_id} references unknown report_id: {report_id}"
            )
        milestone_assessment = view.get("milestone_assessment", {})
        if not isinstance(milestone_assessment, dict):
            errors.append(f"stability package {package_id} missing milestone_assessment")
            continue
        if milestone_assessment.get("dataset_expansion_recommendation") is None:
            errors.append(
                f"stability package {package_id} missing milestone_assessment."
                f"dataset_expansion_recommendation"
            )
        for path, exists in _iter_ref_paths(view.get("reference_reports", {})):
            if path.startswith("/Users/") or path.startswith("/workspace/"):
                errors.append(
                    f"stability package {package_id} contains absolute reference "
                    f"report path: {path}"
                )
            if not exists:
                errors.append(
                    f"stability package {package_id} references missing report path: {path}"
                )

    for view in views.get("research_closeout", []):
        view_id = str(view.get("view_id"))
        if view.get("default_visible") and not view.get("is_official"):
            errors.append(f"research closeout {view_id} is default_visible without is_official")
        if view.get("final_robustness_verdict") is None:
            errors.append(f"research closeout {view_id} missing final_robustness_verdict")
        if view.get("dataset_expansion_decision") is None:
            errors.append(f"research closeout {view_id} missing dataset_expansion_decision")
        for report_id in view.get("supporting_report_ids", []):
            report_id_text = str(report_id)
            if report_id_text not in report_ids:
                errors.append(
                    f"research closeout {view_id} references unknown supporting_report_id: "
                    f"{report_id_text}"
                )
        metadata_path = view.get("metadata_path")
        if isinstance(metadata_path, str) and (
            metadata_path.startswith("/Users/") or metadata_path.startswith("/workspace/")
        ):
            errors.append(
                f"research closeout {view_id} has absolute metadata_path: {metadata_path}"
            )
        for path, exists in _iter_ref_paths(view.get("artifact_refs", {})):
            if path.startswith("/Users/") or path.startswith("/workspace/"):
                errors.append(
                    f"research closeout {view_id} contains absolute artifact path: {path}"
                )
            if view.get("is_official") and not exists:
                errors.append(
                    f"research closeout {view_id} references missing artifact path: {path}"
                )

    return errors


def assert_valid_artifact_index_payload(payload: dict[str, Any]) -> None:
    """Raise a ValueError when the payload is not a valid artifact-index contract."""
    errors = validate_artifact_index_payload(payload)
    if errors:
        raise ValueError("Artifact index validation failed:\n- " + "\n- ".join(errors))
