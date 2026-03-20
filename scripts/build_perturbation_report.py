# ruff: noqa: E402

from __future__ import annotations

import argparse
import json
from typing import Sequence

try:
    from scripts._bootstrap import bootstrap_repo_paths
except ModuleNotFoundError:
    from _bootstrap import bootstrap_repo_paths

bootstrap_repo_paths()

from model_failure_lab.config import apply_cli_overrides, load_experiment_config
from model_failure_lab.runners.dispatch import dispatch_perturbation_report
from model_failure_lab.tracking import (
    append_experiment_index,
    build_index_entry,
    build_run_metadata,
    generate_run_id,
    write_metadata,
)
from model_failure_lab.utils.paths import (
    build_perturbation_report_artifact_paths,
    build_perturbation_report_run_dir,
)

DEFAULT_PRESET = "civilcomments_perturbation_stress"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap a perturbation report build run.")
    selection_group = parser.add_mutually_exclusive_group(required=True)
    selection_group.add_argument("--experiment-group")
    selection_group.add_argument("--eval-ids")
    parser.add_argument("--preset", default=DEFAULT_PRESET)
    parser.add_argument("--report-name")
    parser.add_argument("--output-format", default="markdown", choices=["markdown"])
    parser.add_argument("--seed", type=int)
    parser.add_argument("--notes")
    return parser


def run_command(argv: Sequence[str] | None = None):
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    config = load_experiment_config(args.preset)
    report_scope = args.experiment_group or args.report_name or "explicit_selection"
    config = apply_cli_overrides(
        config,
        {
            "seed": args.seed,
            "notes": args.notes,
            "run_id": generate_run_id("perturbation_report"),
            "experiment_group": report_scope,
            "eval_ids": args.eval_ids,
            "report_name": args.report_name or report_scope,
            "output_format": args.output_format,
        },
    )
    config["experiment_type"] = "perturbation_report"

    run_dir = build_perturbation_report_run_dir(
        report_scope,
        str(config["run_id"]),
        create=True,
    )
    command = "python scripts/build_perturbation_report.py " + " ".join(argv or [])
    metadata = build_run_metadata(
        run_id=str(config["run_id"]),
        experiment_type="perturbation_report",
        model_name="perturbation_report",
        dataset_name=str(config["dataset_name"]),
        split_details=dict(config["split_details"]),
        random_seed=int(config["seed"]),
        resolved_config=config,
        command=command.strip(),
        run_dir=run_dir,
        artifact_paths=build_perturbation_report_artifact_paths(run_dir),
        notes=str(config.get("notes", "")),
        tags=[*config.get("tags", []), "perturbation_report"],
        status="running",
    )
    metadata_path = write_metadata(run_dir, metadata, create_checkpoint_dir=False)
    result = dispatch_perturbation_report(
        config=config,
        experiment_group=args.experiment_group,
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=run_dir / "report_summary.json",
        preset_name=args.preset,
    )
    final_metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    append_experiment_index(build_index_entry(result.metadata_path, final_metadata))
    return result


def main(argv: Sequence[str] | None = None) -> int:
    result = run_command(argv)
    print(result.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
