# ruff: noqa: E402

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

try:
    from scripts._bootstrap import bootstrap_repo_paths
except ModuleNotFoundError:
    from _bootstrap import bootstrap_repo_paths

bootstrap_repo_paths()

from model_failure_lab.config import apply_cli_overrides, load_experiment_config
from model_failure_lab.reporting import (
    build_exploratory_mitigation_summary,
    build_final_robustness_summary,
    build_official_mitigation_summary,
    build_promotion_audit,
    build_robustness_method_tables,
    build_robustness_reference_reports,
    build_robustness_report_metadata,
    build_seeded_baseline_summary,
    load_saved_report_metadata,
    load_saved_report_payload,
    render_promotion_audit_markdown,
    render_robustness_report_markdown,
    write_robustness_report_bundle,
)
from model_failure_lab.runners.contracts import DispatchResult
from model_failure_lab.tracking import (
    append_experiment_index,
    build_index_entry,
    generate_run_id,
    write_metadata,
)
from model_failure_lab.utils.paths import (
    build_report_run_dir,
    build_robustness_promotion_audit_path,
    build_robustness_report_artifact_paths,
    repository_root,
)

DEFAULT_PRESET = "civilcomments_distilbert_baseline"
DEFAULT_AUDIT_NAME = "phase25_group_balanced_sampling"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build the final robustness comparison package from saved "
            "Phase 18/19/20/23/25 artifacts."
        )
    )
    parser.add_argument("--temperature-report-data", required=True)
    parser.add_argument("--reweighting-report-data", required=True)
    parser.add_argument("--stability-report-data", required=True)
    parser.add_argument("--stability-summary", required=True)
    parser.add_argument("--group-dro-report-data", required=True)
    parser.add_argument("--group-balanced-report-data", required=True)
    parser.add_argument("--preset", default=DEFAULT_PRESET)
    parser.add_argument("--report-name", default="phase26_robustness_final")
    parser.add_argument("--promotion-audit-name", default=DEFAULT_AUDIT_NAME)
    parser.add_argument("--notes")
    return parser


def _path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _relative_repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repository_root()))
    except ValueError:
        return path.as_posix()


def run_command(argv: Sequence[str] | None = None) -> DispatchResult:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    temperature_report_data_path = _path(args.temperature_report_data)
    reweighting_report_data_path = _path(args.reweighting_report_data)
    stability_report_data_path = _path(args.stability_report_data)
    stability_summary_path = _path(args.stability_summary)
    group_dro_report_data_path = _path(args.group_dro_report_data)
    group_balanced_report_data_path = _path(args.group_balanced_report_data)

    temperature_report_data = load_saved_report_payload(temperature_report_data_path)
    reweighting_report_data = load_saved_report_payload(reweighting_report_data_path)
    stability_report_data = load_saved_report_payload(stability_report_data_path)
    stability_summary = load_saved_report_payload(stability_summary_path)
    group_dro_report_data = load_saved_report_payload(group_dro_report_data_path)
    group_balanced_report_data = load_saved_report_payload(group_balanced_report_data_path)
    stability_metadata = load_saved_report_metadata(stability_report_data_path)

    baseline_summary = build_seeded_baseline_summary(
        stability_report_data=stability_report_data,
        stability_summary=stability_summary,
    )
    temperature_summary = build_official_mitigation_summary(
        method_name="temperature_scaling",
        display_name="Temperature Scaling",
        seeded_report_data=temperature_report_data,
        stability_report_data=stability_report_data,
        stability_summary=stability_summary,
    )
    reweighting_summary = build_official_mitigation_summary(
        method_name="reweighting",
        display_name="Reweighting",
        seeded_report_data=reweighting_report_data,
        stability_report_data=stability_report_data,
        stability_summary=stability_summary,
    )
    group_dro_summary = build_exploratory_mitigation_summary(
        method_name="group_dro",
        display_name="Group DRO",
        scout_report_data=group_dro_report_data,
        promotion_decision="do_not_promote",
    )
    group_balanced_summary = build_exploratory_mitigation_summary(
        method_name="group_balanced_sampling",
        display_name="Group-Balanced Sampling",
        scout_report_data=group_balanced_report_data,
        promotion_decision="do_not_promote",
    )

    reference_reports = build_robustness_reference_reports(
        temperature_report_data_path=temperature_report_data_path,
        reweighting_report_data_path=reweighting_report_data_path,
        stability_report_data_path=stability_report_data_path,
        group_dro_report_data_path=group_dro_report_data_path,
        group_balanced_report_data_path=group_balanced_report_data_path,
    )
    promotion_audit = build_promotion_audit(
        candidate_summary=group_balanced_summary,
        reference_summary=reweighting_summary,
        stability_summary=stability_summary,
        audit_name=args.promotion_audit_name,
    )
    promotion_audit_path = build_robustness_promotion_audit_path(args.promotion_audit_name)
    promotion_audit_markdown = render_promotion_audit_markdown(
        promotion_audit=promotion_audit,
        reference_reports=reference_reports,
    )
    report_scope = args.report_name or "phase26_robustness_final"
    report_summary = build_final_robustness_summary(
        report_title=report_scope,
        baseline_summary=baseline_summary,
        official_method_summaries=[temperature_summary, reweighting_summary],
        exploratory_method_summaries=[group_dro_summary, group_balanced_summary],
        promotion_audit=promotion_audit,
        reference_reports=reference_reports,
        stability_summary=stability_summary,
    )
    tables = build_robustness_method_tables(
        baseline_summary=baseline_summary,
        official_method_summaries=[temperature_summary, reweighting_summary],
        exploratory_method_summaries=[group_dro_summary, group_balanced_summary],
    )

    config = load_experiment_config(args.preset)
    config = apply_cli_overrides(
        config,
        {
            "notes": args.notes,
            "run_id": generate_run_id("report"),
            "experiment_group": report_scope,
            "report_name": report_scope,
            "output_format": "markdown",
            "tags": ["robustness", "phase26"],
        },
    )
    config["robustness_report"] = {
        "temperature_report_data": str(temperature_report_data_path),
        "reweighting_report_data": str(reweighting_report_data_path),
        "stability_report_data": str(stability_report_data_path),
        "stability_summary": str(stability_summary_path),
        "group_dro_report_data": str(group_dro_report_data_path),
        "group_balanced_report_data": str(group_balanced_report_data_path),
    }
    config["promotion_audit_path"] = str(promotion_audit_path)

    run_dir = build_report_run_dir(report_scope, str(config["run_id"]), create=True)
    command = "python scripts/build_robustness_report.py " + " ".join(argv or [])
    source_eval_ids = [str(item) for item in stability_metadata.get("source_eval_ids", [])]
    metadata = build_robustness_report_metadata(
        report_id=str(config["run_id"]),
        report_scope=report_scope,
        selection_mode="saved_reports",
        source_eval_ids=source_eval_ids,
        resolved_config=config,
        command=command.strip(),
        run_dir=run_dir,
        dataset_name=str(config["dataset_name"]),
        split_details=dict(config["split_details"]),
        artifact_paths=build_robustness_report_artifact_paths(
            run_dir,
            promotion_audit_path=promotion_audit_path,
        ),
        status="running",
    )
    metadata_path = write_metadata(run_dir, metadata, create_checkpoint_dir=False)

    artifact_paths = write_robustness_report_bundle(
        run_dir,
        markdown=render_robustness_report_markdown(
            report_title=report_scope,
            report_summary=report_summary,
            official_method_summaries=[temperature_summary, reweighting_summary],
            exploratory_method_summaries=[group_dro_summary, group_balanced_summary],
            promotion_audit=promotion_audit,
            reference_reports=reference_reports,
            table_paths={
                "worst_group_summary": "tables/worst_group_summary.csv",
                "ood_summary": "tables/ood_summary.csv",
                "id_summary": "tables/id_summary.csv",
                "calibration_summary": "tables/calibration_summary.csv",
                "promotion_audit_markdown": _relative_repo_path(promotion_audit_path),
            },
        ),
        report_summary=report_summary,
        official_method_summaries=[temperature_summary, reweighting_summary],
        exploratory_method_summaries=[group_dro_summary, group_balanced_summary],
        promotion_audit=promotion_audit,
        reference_reports=reference_reports,
        worst_group_summary=tables["worst_group_summary"],
        ood_summary=tables["ood_summary"],
        id_summary=tables["id_summary"],
        calibration_summary=tables["calibration_summary"],
        promotion_audit_markdown=promotion_audit_markdown,
        promotion_audit_path=promotion_audit_path,
    )

    final_metadata = build_robustness_report_metadata(
        report_id=str(config["run_id"]),
        report_scope=report_scope,
        selection_mode="saved_reports",
        source_eval_ids=source_eval_ids,
        resolved_config=config,
        command=command.strip(),
        run_dir=run_dir,
        dataset_name=str(config["dataset_name"]),
        split_details=dict(config["split_details"]),
        artifact_paths=artifact_paths,
        status="completed",
    )
    metadata_path = write_metadata(run_dir, final_metadata, create_checkpoint_dir=False)
    append_experiment_index(build_index_entry(metadata_path, final_metadata))
    return DispatchResult(
        status="completed",
        message=f"Robustness report completed for {report_scope}",
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=run_dir / "report_summary.json",
        preset_name=args.preset,
    )


def main(argv: Sequence[str] | None = None) -> int:
    result = run_command(argv)
    print(result.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
