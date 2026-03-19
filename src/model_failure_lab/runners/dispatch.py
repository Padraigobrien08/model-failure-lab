"""Thin dispatch layer behind the public scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from model_failure_lab.data import load_canonical_civilcomments_dataset
from model_failure_lab.evaluation import (
    build_confidence_summary,
    build_diagnostics_payload,
    build_id_ood_comparison,
    build_split_metrics_rows,
    build_worst_group_summary,
    compute_calibration_summary,
    compute_robustness_gaps,
    compute_subgroup_metrics,
    load_saved_predictions,
)
from model_failure_lab.evaluation.bundle import (
    build_evaluation_metadata,
    write_evaluation_bundle,
)
from model_failure_lab.mitigations import (
    run_temperature_scaling,
    train_distilbert_reweighting,
)
from model_failure_lab.models import train_distilbert_baseline, train_logistic_baseline
from model_failure_lab.perturbations import (
    build_family_severity_matrix,
    build_family_summary,
    build_severity_summary,
    build_source_delta_summary,
    build_suite_summary,
    generate_perturbation_suite,
    load_clean_source_predictions,
    load_saved_run_scorer,
    score_perturbation_suite,
    select_source_samples,
    write_perturbation_bundle,
)
from model_failure_lab.reporting import (
    build_calibration_curve_figure,
    build_calibration_table,
    build_clean_vs_perturbed_figure,
    build_comparison_table,
    build_id_ood_comparison_frame,
    build_id_ood_figure,
    build_mitigation_comparison_table,
    build_perturbation_family_drop_figure,
    build_perturbation_report_metadata,
    build_perturbation_report_summary,
    build_perturbation_report_tables,
    build_report_metadata,
    build_report_summary,
    build_severity_ladder_figure,
    build_subgroup_table,
    build_worst_group_vs_average_figure,
    build_worst_group_vs_average_frame,
    build_worst_subgroups_figure,
    load_perturbation_report_inputs,
    load_report_inputs,
    render_perturbation_report_markdown,
    render_report_markdown,
    select_report_candidates,
    write_perturbation_report_bundle,
    write_report_bundle,
)
from model_failure_lab.tracking import (
    build_artifact_paths,
    build_run_metadata,
    write_metadata,
    write_metrics,
)
from model_failure_lab.tracking.metrics import build_metrics_payload

from .contracts import DispatchResult


def _apply_mitigation_metadata_fields(
    metadata_payload: dict[str, Any],
    *,
    config: dict[str, Any],
    method_name: str,
) -> dict[str, Any]:
    metadata_payload["mitigation_method"] = str(
        config.get("mitigation_method") or method_name
    )
    mitigation_config = config.get("mitigation_config") or config.get("mitigation")
    if mitigation_config is not None:
        metadata_payload["mitigation_config"] = mitigation_config
    if config.get("parent_model_name") is not None:
        metadata_payload["parent_model_name"] = str(config["parent_model_name"])
    return metadata_payload


def build_scaffold_metrics(config: dict[str, Any]) -> dict[str, Any]:
    """Build placeholder metrics for scaffold-mode runs."""
    eval_config = config.get("eval", {})
    return build_metrics_payload(
        primary_metric={"name": eval_config.get("primary_metric", "accuracy"), "value": None},
        worst_group_metric={
            "name": eval_config.get("worst_group_metric", "accuracy"),
            "value": None,
        },
        robustness_gap={
            "name": eval_config.get("robustness_gap_metric", "accuracy_delta"),
            "value": None,
        },
        calibration_metric={
            "name": eval_config.get("calibration_metric", "ece"),
            "value": None,
        },
    )


def dispatch_baseline(
    *,
    config: dict[str, Any],
    run_dir: Path,
    metadata_path: Path,
    metrics_path: Path,
    preset_name: str,
) -> DispatchResult:
    if config["model_name"] == "logistic_tfidf":
        artifacts = train_logistic_baseline(config, run_dir)
        metrics_path = write_metrics(run_dir, artifacts.metrics_payload)

        existing_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        artifact_paths = build_artifact_paths(run_dir, prediction_splits=["train", "validation"])
        artifact_paths["checkpoint"] = str(artifacts.checkpoint_dir)
        artifact_paths["predictions"] = {
            split: str(path) for split, path in artifacts.prediction_paths.items()
        }
        artifact_paths["selected_checkpoint"] = str(artifacts.model_path)
        metadata_payload = build_run_metadata(
            run_id=str(config["run_id"]),
            experiment_type="baseline",
            model_name=str(config["model_name"]),
            dataset_name=str(config["dataset_name"]),
            split_details=dict(config["split_details"]),
            random_seed=int(config["seed"]),
            resolved_config=config,
            command=str(existing_metadata.get("command", "")),
            run_dir=run_dir,
            git_commit_hash=existing_metadata.get("git_commit_hash"),
            library_versions=existing_metadata.get("library_versions"),
            artifact_paths=artifact_paths,
            parent_run_id=existing_metadata.get("parent_run_id"),
            notes=str(config.get("notes", "")),
            tags=list(config.get("tags", [])),
            timestamp=existing_metadata.get("timestamp"),
            status="completed",
        )
        metadata_path = write_metadata(run_dir, metadata_payload)
        return DispatchResult(
            status="completed",
            message=f"Baseline completed for {config['model_name']}",
            run_dir=run_dir,
            metadata_path=metadata_path,
            metrics_path=metrics_path,
            preset_name=preset_name,
        )

    if config["model_name"] == "distilbert":
        artifacts = train_distilbert_baseline(config, run_dir)
        metrics_path = write_metrics(run_dir, artifacts.metrics_payload)

        existing_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        artifact_paths = build_artifact_paths(run_dir, prediction_splits=["train", "validation"])
        artifact_paths["checkpoint"] = str(artifacts.checkpoint_dir)
        artifact_paths["predictions"] = {
            split: str(path) for split, path in artifacts.prediction_paths.items()
        }
        artifact_paths["selected_checkpoint"] = str(artifacts.checkpoint_path)
        artifact_paths["training_history_json"] = str(artifacts.history_path)
        metadata_payload = build_run_metadata(
            run_id=str(config["run_id"]),
            experiment_type="baseline",
            model_name=str(config["model_name"]),
            dataset_name=str(config["dataset_name"]),
            split_details=dict(config["split_details"]),
            random_seed=int(config["seed"]),
            resolved_config=config,
            command=str(existing_metadata.get("command", "")),
            run_dir=run_dir,
            git_commit_hash=existing_metadata.get("git_commit_hash"),
            library_versions=existing_metadata.get("library_versions"),
            artifact_paths=artifact_paths,
            parent_run_id=existing_metadata.get("parent_run_id"),
            notes=str(config.get("notes", "")),
            tags=list(config.get("tags", [])),
            timestamp=existing_metadata.get("timestamp"),
            status="completed",
        )
        metadata_path = write_metadata(run_dir, metadata_payload)
        return DispatchResult(
            status="completed",
            message=f"Baseline completed for {config['model_name']}",
            run_dir=run_dir,
            metadata_path=metadata_path,
            metrics_path=metrics_path,
            preset_name=preset_name,
        )

    return DispatchResult(
        status="scaffold_ready",
        message=f"Baseline scaffold ready for {config['model_name']}",
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=metrics_path,
        preset_name=preset_name,
    )


def dispatch_mitigation(
    *,
    config: dict[str, Any],
    method_name: str,
    parent_run_id: str,
    run_dir: Path,
    metadata_path: Path,
    metrics_path: Path,
    preset_name: str,
) -> DispatchResult:
    if method_name == "reweighting":
        if config["model_name"] != "distilbert":
            raise ValueError("Group reweighting only supports DistilBERT parent baselines.")

        artifacts = train_distilbert_reweighting(config, run_dir)
        metrics_path = write_metrics(run_dir, artifacts.metrics_payload)

        existing_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        artifact_paths = build_artifact_paths(run_dir, prediction_splits=["train", "validation"])
        artifact_paths["checkpoint"] = str(artifacts.checkpoint_dir)
        artifact_paths["predictions"] = {
            split: str(path) for split, path in artifacts.prediction_paths.items()
        }
        artifact_paths["selected_checkpoint"] = str(artifacts.checkpoint_path)
        artifact_paths["training_history_json"] = str(artifacts.history_path)
        artifact_paths["group_weights_csv"] = str(artifacts.group_weights_path)
        metadata_payload = build_run_metadata(
            run_id=str(config["run_id"]),
            experiment_type="mitigation",
            model_name=str(config["model_name"]),
            dataset_name=str(config["dataset_name"]),
            split_details=dict(config["split_details"]),
            random_seed=int(config["seed"]),
            resolved_config=config,
            command=str(existing_metadata.get("command", "")),
            run_dir=run_dir,
            git_commit_hash=existing_metadata.get("git_commit_hash"),
            library_versions=existing_metadata.get("library_versions"),
            artifact_paths=artifact_paths,
            parent_run_id=existing_metadata.get("parent_run_id", parent_run_id),
            notes=str(config.get("notes", "")),
            tags=list(config.get("tags", [])),
            timestamp=existing_metadata.get("timestamp"),
            status="completed",
        )
        metadata_payload = _apply_mitigation_metadata_fields(
            metadata_payload,
            config=config,
            method_name=method_name,
        )
        metadata_path = write_metadata(run_dir, metadata_payload)
        return DispatchResult(
            status="completed",
            message=f"Mitigation completed for {method_name} on {config['model_name']}",
            run_dir=run_dir,
            metadata_path=metadata_path,
            metrics_path=metrics_path,
            preset_name=preset_name,
            extras={"method_name": method_name, "parent_run_id": parent_run_id},
        )

    if method_name == "temperature_scaling":
        if config["model_name"] != "distilbert":
            raise ValueError("Temperature scaling only supports DistilBERT parent baselines.")

        artifacts = run_temperature_scaling(config, run_dir)
        metrics_path = write_metrics(run_dir, artifacts.metrics_payload)

        existing_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        prediction_splits = list(artifacts.prediction_paths)
        artifact_paths = build_artifact_paths(run_dir, prediction_splits=prediction_splits)
        artifact_paths["checkpoint"] = str(artifacts.checkpoint_dir)
        artifact_paths["predictions"] = {
            split: str(path) for split, path in artifacts.prediction_paths.items()
        }
        artifact_paths["selected_checkpoint"] = str(artifacts.selected_checkpoint_path)
        artifact_paths["temperature_scaler_json"] = str(artifacts.temperature_scaler_path)
        metadata_payload = build_run_metadata(
            run_id=str(config["run_id"]),
            experiment_type="mitigation",
            model_name=str(config["model_name"]),
            dataset_name=str(config["dataset_name"]),
            split_details=dict(config["split_details"]),
            random_seed=int(config["seed"]),
            resolved_config=config,
            command=str(existing_metadata.get("command", "")),
            run_dir=run_dir,
            git_commit_hash=existing_metadata.get("git_commit_hash"),
            library_versions=existing_metadata.get("library_versions"),
            artifact_paths=artifact_paths,
            parent_run_id=existing_metadata.get("parent_run_id", parent_run_id),
            notes=str(config.get("notes", "")),
            tags=list(config.get("tags", [])),
            timestamp=existing_metadata.get("timestamp"),
            status="completed",
        )
        metadata_payload = _apply_mitigation_metadata_fields(
            metadata_payload,
            config=config,
            method_name=method_name,
        )
        metadata_payload["learned_temperature"] = artifacts.learned_temperature
        metadata_payload["calibration_fitting_split"] = artifacts.calibration_fitting_split
        metadata_payload["logit_provenance"] = dict(artifacts.logit_provenance)
        metadata_path = write_metadata(run_dir, metadata_payload)
        return DispatchResult(
            status="completed",
            message=f"Mitigation completed for {method_name} on {config['model_name']}",
            run_dir=run_dir,
            metadata_path=metadata_path,
            metrics_path=metrics_path,
            preset_name=preset_name,
            extras={"method_name": method_name, "parent_run_id": parent_run_id},
        )

    return DispatchResult(
        status="scaffold_ready",
        message=f"Mitigation scaffold ready for {method_name} on {config['model_name']}",
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=metrics_path,
        preset_name=preset_name,
        extras={"method_name": method_name, "parent_run_id": parent_run_id},
    )


def dispatch_shift_eval(
    *,
    config: dict[str, Any],
    target_run_id: str,
    source_metadata_path: Path,
    run_dir: Path,
    metadata_path: Path,
    metrics_path: Path,
    preset_name: str,
) -> DispatchResult:
    source_metadata = json.loads(source_metadata_path.read_text(encoding="utf-8"))
    _, prediction_frame = load_saved_predictions(
        source_metadata,
        splits=config.get("eval", {}).get("requested_splits"),
    )
    split_metric_rows = build_split_metrics_rows(prediction_frame)
    group_fields = (
        source_metadata.get("resolved_config", {}).get("data", {}).get("group_fields", [])
    )
    attribute_columns = [
        str(field) for field in group_fields if str(field) in prediction_frame.columns
    ]
    subgroup_rows = compute_subgroup_metrics(
        prediction_frame,
        min_support=int(config["eval"]["min_group_support"]),
        attribute_columns=attribute_columns or None,
    )
    worst_group_summary = build_worst_group_summary(
        subgroup_rows,
        min_support=int(config["eval"]["min_group_support"]),
    )
    id_ood_comparison_rows = build_id_ood_comparison(split_metric_rows)
    robustness_gaps = compute_robustness_gaps(split_metric_rows)
    calibration = compute_calibration_summary(
        prediction_frame,
        n_bins=int(config["eval"]["calibration_bins"]),
        strategy=str(config["eval"].get("calibration_strategy", "uniform")),
    )
    confidence_summary = build_confidence_summary(
        prediction_frame,
        bins=int(config["eval"]["calibration_bins"]),
    )
    diagnostics_payload = build_diagnostics_payload(prediction_frame)
    artifact_paths = write_evaluation_bundle(
        run_dir,
        split_metric_rows=split_metric_rows,
        id_ood_comparison_rows=id_ood_comparison_rows,
        subgroup_rows=subgroup_rows,
        worst_group_summary=worst_group_summary,
        robustness_gaps=robustness_gaps,
        calibration_summary_rows=calibration["summary_rows"],
        calibration_bin_rows=calibration["bin_rows"],
        confidence_summary=confidence_summary,
        diagnostics_payload=diagnostics_payload,
    )
    existing_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    evaluated_splits = [
        str(split) for split in prediction_frame["split"].dropna().astype(str).unique()
    ]
    metadata_payload = build_evaluation_metadata(
        eval_id=str(config["run_id"]),
        source_run_metadata=source_metadata,
        source_metadata_path=source_metadata_path,
        resolved_config=config,
        command=str(existing_metadata.get("command", "")),
        eval_dir=run_dir,
        evaluated_splits=evaluated_splits,
        min_group_support=int(config["eval"]["min_group_support"]),
        calibration_bins=int(config["eval"]["calibration_bins"]),
        output_tag=config["eval"].get("output_tag"),
        artifact_paths=artifact_paths,
        git_commit_hash=existing_metadata.get("git_commit_hash"),
        library_versions=existing_metadata.get("library_versions"),
        timestamp=existing_metadata.get("timestamp"),
        status="completed",
    )
    metadata_path = write_metadata(run_dir, metadata_payload, create_checkpoint_dir=False)
    return DispatchResult(
        status="completed",
        message=f"Shift evaluation completed for {target_run_id}",
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=Path(artifact_paths["overall_metrics_json"]),
        preset_name=preset_name,
        extras={"target_run_id": target_run_id, "model_name": config["model_name"]},
    )


def dispatch_perturbation_eval(
    *,
    config: dict[str, Any],
    target_run_id: str,
    source_metadata_path: Path,
    run_dir: Path,
    metadata_path: Path,
    metrics_path: Path,
    preset_name: str,
    dataset_loader: Any | None = None,
    scorer_loader: Any | None = None,
) -> DispatchResult:
    source_metadata = json.loads(source_metadata_path.read_text(encoding="utf-8"))
    resolved_dataset_loader = dataset_loader or load_canonical_civilcomments_dataset
    resolved_scorer_loader = scorer_loader or load_saved_run_scorer

    dataset = resolved_dataset_loader(config, download=True)
    perturbation_config = dict(config["perturbation"])
    selected_source_samples = select_source_samples(
        dataset.samples,
        split=str(perturbation_config["source_split"]),
        max_samples=int(perturbation_config["max_source_samples"]),
        selection_seed=int(perturbation_config["selection_seed"]),
    )
    suite = generate_perturbation_suite(
        selected_source_samples,
        source_run_id=str(source_metadata["run_id"]),
        model_name=str(config["model_name"]),
        families=list(perturbation_config["default_family_order"]),
        severities=list(perturbation_config["severities"]),
        selection_seed=int(perturbation_config["selection_seed"]),
        perturbation_seed=int(perturbation_config["perturbation_seed"]),
        slang_mapping=perturbation_config.get("slang_mapping"),
    )
    clean_prediction_frame = load_clean_source_predictions(
        source_metadata,
        split=str(perturbation_config["source_split"]),
        source_sample_ids=[sample["sample_id"] for sample in selected_source_samples],
    )
    scorer = resolved_scorer_loader(source_metadata)
    perturbed_prediction_frame = score_perturbation_suite(
        suite.to_records(),
        run_id=str(config["run_id"]),
        scorer=scorer,
    )
    suite_summary = build_suite_summary(clean_prediction_frame, perturbed_prediction_frame)
    family_summary = build_family_summary(clean_prediction_frame, perturbed_prediction_frame)
    severity_summary = build_severity_summary(clean_prediction_frame, perturbed_prediction_frame)
    family_severity_matrix = build_family_severity_matrix(
        clean_prediction_frame,
        perturbed_prediction_frame,
    )
    source_delta_summary = build_source_delta_summary(
        clean_prediction_frame,
        perturbed_prediction_frame,
    )
    artifact_paths = write_perturbation_bundle(
        run_dir,
        suite=suite,
        source_run_metadata=source_metadata,
        resolved_config=config,
        perturbed_predictions=perturbed_prediction_frame,
        suite_summary=suite_summary,
        family_summary=family_summary,
        severity_summary=severity_summary,
        family_severity_matrix=family_severity_matrix,
        source_delta_summary=source_delta_summary,
        preview_limit=5,
    )

    existing_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata_payload = build_run_metadata(
        run_id=str(config["run_id"]),
        experiment_type="perturbation_eval",
        model_name=str(config["model_name"]),
        dataset_name=str(config["dataset_name"]),
        split_details=dict(config["split_details"]),
        random_seed=int(config["seed"]),
        resolved_config=config,
        command=str(existing_metadata.get("command", "")),
        run_dir=run_dir,
        git_commit_hash=existing_metadata.get("git_commit_hash"),
        library_versions=existing_metadata.get("library_versions"),
        artifact_paths=artifact_paths,
        parent_run_id=str(source_metadata["run_id"]),
        notes=str(config.get("notes", "")),
        tags=list(config.get("tags", [])),
        timestamp=existing_metadata.get("timestamp"),
        status="completed",
    )
    metadata_payload["source_run_id"] = str(source_metadata["run_id"])
    metadata_payload["source_metadata_path"] = str(source_metadata_path)
    metadata_payload["selected_source_count"] = suite.source_sample_count
    metadata_payload["perturbed_sample_count"] = suite.perturbed_sample_count
    metadata_payload["perturbation_schema_version"] = suite.schema_version
    metadata_payload["source_split"] = str(perturbation_config["source_split"])
    metadata_payload["output_tag"] = perturbation_config.get("output_tag")
    metadata_path = write_metadata(run_dir, metadata_payload, create_checkpoint_dir=False)
    return DispatchResult(
        status="completed",
        message=(
            "Perturbation evaluation completed for "
            f"{config['model_name']} with {suite.perturbed_sample_count} samples"
        ),
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=metrics_path,
        preset_name=preset_name,
        extras={
            "source_run_id": target_run_id,
            "selected_source_count": suite.source_sample_count,
            "perturbed_sample_count": suite.perturbed_sample_count,
        },
    )


def dispatch_report(
    *,
    config: dict[str, Any],
    experiment_group: str | None,
    run_dir: Path,
    metadata_path: Path,
    metrics_path: Path,
    preset_name: str,
) -> DispatchResult:
    report_config = config.get("report", {})
    eval_ids = report_config.get("eval_ids")
    selected_candidates = select_report_candidates(
        load_report_inputs(
            experiment_group=experiment_group if not eval_ids else None,
            eval_ids=eval_ids,
        )
    )
    comparison_frame = build_id_ood_comparison_frame(selected_candidates)
    comparison_table = build_comparison_table(comparison_frame)
    worst_group_frame = build_worst_group_vs_average_frame(selected_candidates)
    subgroup_table = build_subgroup_table(
        selected_candidates,
        top_k=int(report_config.get("top_k_subgroups", 5)),
        min_group_support=int(config.get("eval", {}).get("min_group_support", 100)),
    )
    calibration_table = build_calibration_table(selected_candidates)
    mitigation_comparison_table = build_mitigation_comparison_table(selected_candidates)
    report_title = str(
        report_config.get("report_name")
        or experiment_group
        or "Explicit Evaluation Report"
    )
    report_summary = build_report_summary(
        selected_candidates,
        comparison_table=comparison_table,
        subgroup_table=subgroup_table,
        calibration_table=calibration_table,
        mitigation_comparison_table=mitigation_comparison_table,
        report_title=report_title,
    )
    markdown = render_report_markdown(
        report_title=report_title,
        report_summary=report_summary,
        figure_paths={
            "id_vs_ood_primary_metric": "figures/id_vs_ood_primary_metric.png",
            "worst_group_vs_average": "figures/worst_group_vs_average.png",
            "worst_subgroups": "figures/worst_subgroups.png",
            "calibration_curve": "figures/calibration_curve.png",
        },
        table_paths={
            "comparison_table": "tables/comparison_table.csv",
            "mitigation_comparison_table": "tables/mitigation_comparison_table.csv",
            "subgroup_table": "tables/subgroup_table.csv",
            "calibration_table": "tables/calibration_table.csv",
        },
    )
    artifact_paths = write_report_bundle(
        run_dir,
        markdown=markdown,
        report_summary=report_summary,
        figures={
            "id_vs_ood_primary_metric": build_id_ood_figure(comparison_frame),
            "worst_group_vs_average": build_worst_group_vs_average_figure(worst_group_frame),
            "worst_subgroups": build_worst_subgroups_figure(subgroup_table),
            "calibration_curve": build_calibration_curve_figure(selected_candidates),
        },
        comparison_table=comparison_table,
        mitigation_comparison_table=mitigation_comparison_table,
        subgroup_table=subgroup_table,
        calibration_table=calibration_table,
    )
    existing_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    first_candidate = selected_candidates[0]
    metadata_payload = build_report_metadata(
        report_id=str(config["run_id"]),
        report_scope=str(experiment_group or report_title),
        selection_mode="eval_ids" if eval_ids else "experiment_group",
        source_eval_ids=[candidate.eval_id for candidate in selected_candidates],
        resolved_config=config,
        command=str(existing_metadata.get("command", "")),
        run_dir=run_dir,
        dataset_name=str(first_candidate.metadata.get("dataset_name", config["dataset_name"])),
        split_details=dict(first_candidate.metadata.get("split_details", config["split_details"])),
        artifact_paths=artifact_paths,
        git_commit_hash=existing_metadata.get("git_commit_hash"),
        library_versions=existing_metadata.get("library_versions"),
        timestamp=existing_metadata.get("timestamp"),
        status="completed",
    )
    metadata_path = write_metadata(run_dir, metadata_payload, create_checkpoint_dir=False)
    return DispatchResult(
        status="completed",
        message=f"Report completed for {experiment_group or report_title}",
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=Path(artifact_paths["report_summary_json"]),
        preset_name=preset_name,
        extras={
            "experiment_group": experiment_group,
            "source_eval_ids": [candidate.eval_id for candidate in selected_candidates],
        },
    )


def dispatch_perturbation_report(
    *,
    config: dict[str, Any],
    experiment_group: str | None,
    run_dir: Path,
    metadata_path: Path,
    metrics_path: Path,
    preset_name: str,
) -> DispatchResult:
    report_config = config.get("report", {})
    eval_ids = report_config.get("eval_ids")
    selected_candidates = load_perturbation_report_inputs(
        experiment_group=experiment_group if not eval_ids else None,
        eval_ids=eval_ids,
    )
    tables = build_perturbation_report_tables(selected_candidates)
    report_title = str(
        report_config.get("report_name")
        or experiment_group
        or "Synthetic Perturbation Report"
    )
    report_summary = build_perturbation_report_summary(
        selected_candidates,
        suite_summary=tables["suite_summary"],
        family_summary=tables["family_summary"],
        severity_summary=tables["severity_summary"],
        report_title=report_title,
    )
    markdown = render_perturbation_report_markdown(
        report_title=report_title,
        report_summary=report_summary,
        figure_paths={
            "clean_vs_perturbed_primary_metric": "figures/clean_vs_perturbed_primary_metric.png",
            "perturbation_family_drop": "figures/perturbation_family_drop.png",
            "severity_ladder": "figures/severity_ladder.png",
        },
        table_paths={
            "suite_summary": "tables/suite_summary.csv",
            "family_summary": "tables/family_summary.csv",
            "severity_summary": "tables/severity_summary.csv",
            "family_severity_matrix": "tables/family_severity_matrix.csv",
        },
    )
    artifact_paths = write_perturbation_report_bundle(
        run_dir,
        markdown=markdown,
        report_summary=report_summary,
        figures={
            "clean_vs_perturbed_primary_metric": build_clean_vs_perturbed_figure(
                tables["suite_summary"]
            ),
            "perturbation_family_drop": build_perturbation_family_drop_figure(
                tables["family_summary"]
            ),
            "severity_ladder": build_severity_ladder_figure(tables["severity_summary"]),
        },
        suite_summary=tables["suite_summary"],
        family_summary=tables["family_summary"],
        severity_summary=tables["severity_summary"],
        family_severity_matrix=tables["family_severity_matrix"],
    )

    existing_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    first_candidate = selected_candidates[0]
    metadata_payload = build_perturbation_report_metadata(
        report_id=str(config["run_id"]),
        report_scope=str(experiment_group or report_title),
        selection_mode="eval_ids" if eval_ids else "experiment_group",
        source_eval_ids=[candidate.eval_id for candidate in selected_candidates],
        resolved_config=config,
        command=str(existing_metadata.get("command", "")),
        run_dir=run_dir,
        dataset_name=str(first_candidate.metadata.get("dataset_name", config["dataset_name"])),
        split_details=dict(first_candidate.metadata.get("split_details", config["split_details"])),
        artifact_paths=artifact_paths,
        git_commit_hash=existing_metadata.get("git_commit_hash"),
        library_versions=existing_metadata.get("library_versions"),
        timestamp=existing_metadata.get("timestamp"),
        status="completed",
    )
    metadata_payload["source_split"] = str(first_candidate.metadata.get("source_split", ""))
    metadata_payload["perturbation_schema_version"] = str(
        first_candidate.metadata.get("perturbation_schema_version", "unknown")
    )
    metadata_path = write_metadata(run_dir, metadata_payload, create_checkpoint_dir=False)
    return DispatchResult(
        status="completed",
        message=f"Perturbation report completed for {experiment_group or report_title}",
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=metrics_path,
        preset_name=preset_name,
        extras={
            "experiment_group": experiment_group,
            "source_eval_ids": [candidate.eval_id for candidate in selected_candidates],
        },
    )


def dispatch_data_download(
    *,
    config: dict[str, Any],
    run_dir: Path,
    metadata_path: Path,
    metrics_path: Path,
    preset_name: str,
) -> DispatchResult:
    return DispatchResult(
        status="scaffold_ready",
        message=f"Data download scaffold ready for {config['dataset_name']}",
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=metrics_path,
        preset_name=preset_name,
    )
