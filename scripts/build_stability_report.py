# ruff: noqa: E402

from __future__ import annotations

import argparse
from typing import Sequence

try:
    from scripts._bootstrap import bootstrap_repo_paths
except ModuleNotFoundError:
    from _bootstrap import bootstrap_repo_paths

bootstrap_repo_paths()

from model_failure_lab.config import apply_cli_overrides, load_experiment_config
from model_failure_lab.reporting import (
    build_baseline_stability_table,
    build_default_reference_reports,
    build_mitigation_stability_table,
    build_stability_report_metadata,
    build_stability_summary,
    load_report_inputs,
    render_stability_report_markdown,
    write_stability_report_bundle,
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
    build_stability_report_artifact_paths,
)

DEFAULT_PRESET = "civilcomments_distilbert_baseline"


def _parse_eval_ids(raw_value: str) -> list[str]:
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a seeded stability report from saved official evaluation bundles."
    )
    parser.add_argument("--logistic-eval-ids", required=True)
    parser.add_argument("--distilbert-eval-ids", required=True)
    parser.add_argument("--temperature-eval-ids", required=True)
    parser.add_argument("--reweighting-eval-ids", required=True)
    parser.add_argument("--preset", default=DEFAULT_PRESET)
    parser.add_argument("--report-name", default="phase20_stability")
    parser.add_argument("--notes")
    return parser


def run_command(argv: Sequence[str] | None = None) -> DispatchResult:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    cohort_eval_ids = {
        "logistic": _parse_eval_ids(args.logistic_eval_ids),
        "distilbert": _parse_eval_ids(args.distilbert_eval_ids),
        "temperature_scaling": _parse_eval_ids(args.temperature_eval_ids),
        "reweighting": _parse_eval_ids(args.reweighting_eval_ids),
    }
    all_eval_ids = [
        *cohort_eval_ids["logistic"],
        *cohort_eval_ids["distilbert"],
        *cohort_eval_ids["temperature_scaling"],
        *cohort_eval_ids["reweighting"],
    ]

    config = load_experiment_config(args.preset)
    report_scope = args.report_name or "phase20_stability"
    config = apply_cli_overrides(
        config,
        {
            "notes": args.notes,
            "run_id": generate_run_id("report"),
            "experiment_group": report_scope,
            "report_name": report_scope,
            "output_format": "markdown",
            "tags": ["stability", "phase20"],
        },
    )
    config["stability_report"] = cohort_eval_ids

    run_dir = build_report_run_dir(report_scope, str(config["run_id"]), create=True)
    command = "python scripts/build_stability_report.py " + " ".join(argv or [])
    metadata = build_stability_report_metadata(
        report_id=str(config["run_id"]),
        report_scope=report_scope,
        selection_mode="explicit_cohorts",
        source_eval_ids=all_eval_ids,
        cohort_eval_ids=cohort_eval_ids,
        resolved_config=config,
        command=command.strip(),
        run_dir=run_dir,
        dataset_name=str(config["dataset_name"]),
        split_details=dict(config["split_details"]),
        artifact_paths=build_stability_report_artifact_paths(run_dir),
        status="running",
    )
    metadata_path = write_metadata(run_dir, metadata, create_checkpoint_dir=False)

    logistic_candidates = load_report_inputs(eval_ids=cohort_eval_ids["logistic"])
    distilbert_candidates = load_report_inputs(eval_ids=cohort_eval_ids["distilbert"])
    temperature_candidates = load_report_inputs(eval_ids=cohort_eval_ids["temperature_scaling"])
    reweighting_candidates = load_report_inputs(eval_ids=cohort_eval_ids["reweighting"])

    baseline_stability_table = build_baseline_stability_table(
        logistic_candidates=logistic_candidates,
        distilbert_candidates=distilbert_candidates,
    )
    temperature_scaling_deltas = build_mitigation_stability_table(
        parent_candidates=distilbert_candidates,
        mitigation_candidates=temperature_candidates,
    )
    reweighting_deltas = build_mitigation_stability_table(
        parent_candidates=distilbert_candidates,
        mitigation_candidates=reweighting_candidates,
    )
    stability_summary = build_stability_summary(
        report_title=report_scope,
        baseline_stability_table=baseline_stability_table,
        temperature_scaling_deltas=temperature_scaling_deltas,
        reweighting_deltas=reweighting_deltas,
        reference_reports=build_default_reference_reports(),
    )
    artifact_paths = write_stability_report_bundle(
        run_dir,
        markdown=render_stability_report_markdown(
            report_title=report_scope,
            stability_summary=stability_summary,
            table_paths={
                "baseline_stability": "tables/baseline_stability.csv",
                "temperature_scaling_deltas": "tables/temperature_scaling_deltas.csv",
                "reweighting_deltas": "tables/reweighting_deltas.csv",
            },
        ),
        stability_summary=stability_summary,
        baseline_stability_table=baseline_stability_table,
        temperature_scaling_deltas=temperature_scaling_deltas,
        reweighting_deltas=reweighting_deltas,
    )

    final_metadata = build_stability_report_metadata(
        report_id=str(config["run_id"]),
        report_scope=report_scope,
        selection_mode="explicit_cohorts",
        source_eval_ids=all_eval_ids,
        cohort_eval_ids=cohort_eval_ids,
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
        message=f"Stability report completed for {report_scope}",
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=run_dir / "stability_summary.json",
        preset_name=args.preset,
    )


def main(argv: Sequence[str] | None = None) -> int:
    result = run_command(argv)
    print(result.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
