from __future__ import annotations

import argparse
from typing import Sequence

from model_failure_lab.config import apply_cli_overrides, load_experiment_config
from model_failure_lab.data import DataDependencyError, materialize_civilcomments
from model_failure_lab.runners.contracts import DispatchResult
from model_failure_lab.tracking import (
    append_experiment_index,
    build_artifact_paths,
    build_index_entry,
    build_run_metadata,
    build_metrics_payload,
    generate_run_id,
    write_metadata,
    write_metrics,
)
from model_failure_lab.utils.paths import build_data_dir

DEFAULT_PRESET = "civilcomments_logistic_baseline"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bootstrap the CivilComments data-download workflow."
    )
    parser.add_argument("--preset", default=DEFAULT_PRESET)
    parser.add_argument("--notes")
    parser.add_argument("--skip-download", action="store_true")
    return parser


def _build_data_download_metrics(result_status: str) -> dict[str, object]:
    return build_metrics_payload(
        primary_metric={"name": "manifest_status", "value": result_status},
        worst_group_metric={"name": "worst_group_metric", "value": None},
        robustness_gap={"name": "robustness_gap", "value": None},
        calibration_metric=None,
    )


def run_command(
    argv: Sequence[str] | None = None,
    *,
    materialize_fn=materialize_civilcomments,
):
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    config = load_experiment_config(args.preset)
    config = apply_cli_overrides(
        config,
        {
            "notes": args.notes,
            "run_id": generate_run_id("download_data"),
            "experiment_group": "data_download",
        },
    )

    run_dir = build_data_dir(create=True) / "runs" / str(config["run_id"])
    command = "python scripts/download_data.py " + " ".join(argv or [])
    artifact_paths = build_artifact_paths(run_dir)
    metadata = build_run_metadata(
        run_id=config["run_id"],
        experiment_type="data_download",
        model_name=config["model_name"],
        dataset_name=config["dataset_name"],
        split_details=config["split_details"],
        random_seed=config["seed"],
        resolved_config=config,
        command=command.strip(),
        run_dir=run_dir,
        artifact_paths=artifact_paths,
        notes=config.get("notes", ""),
        tags=[*config.get("tags", []), "data_download"],
        status="initializing",
    )
    metadata_path = write_metadata(run_dir, metadata)

    try:
        materialization = materialize_fn(
            config,
            download=not args.skip_download,
        )
    except DataDependencyError as exc:
        failed_artifact_paths = {
            **artifact_paths,
            "manifest_json": str(run_dir / "failed_manifest.json"),
            "data_summary_dir": str(run_dir / "summaries"),
        }
        failure_metadata = build_run_metadata(
            run_id=config["run_id"],
            experiment_type="data_download",
            model_name=config["model_name"],
            dataset_name=config["dataset_name"],
            split_details=config["split_details"],
            random_seed=config["seed"],
            resolved_config=config,
            command=command.strip(),
            run_dir=run_dir,
            artifact_paths=failed_artifact_paths,
            notes=str(exc),
            tags=[*config.get("tags", []), "data_download"],
            status="failed_dependency",
        )
        write_metadata(run_dir, failure_metadata)
        raise

    artifact_paths = {
        **artifact_paths,
        "manifest_json": str(materialization.manifest_path),
        "data_summary_dir": str(materialization.summary_dir),
    }
    success_metadata = build_run_metadata(
        run_id=config["run_id"],
        experiment_type="data_download",
        model_name=config["model_name"],
        dataset_name=config["dataset_name"],
        split_details=config["split_details"],
        random_seed=config["seed"],
        resolved_config=config,
        command=command.strip(),
        run_dir=run_dir,
        artifact_paths=artifact_paths,
        notes=config.get("notes", ""),
        tags=[*config.get("tags", []), "data_download"],
        status="materialized",
    )
    metadata_path = write_metadata(run_dir, success_metadata)
    metrics_path = write_metrics(run_dir, _build_data_download_metrics("materialized"))
    append_experiment_index(build_index_entry(metadata_path, success_metadata))
    return DispatchResult(
        status="materialized",
        message=f"Data manifest ready for {config['dataset_name']}",
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=metrics_path,
        preset_name=args.preset,
        extras={"manifest_path": str(materialization.manifest_path)},
    )


def main(argv: Sequence[str] | None = None) -> int:
    result = run_command(argv)
    print(result.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
