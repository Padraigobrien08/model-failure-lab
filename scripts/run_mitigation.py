from __future__ import annotations

import argparse
from typing import Sequence

from model_failure_lab.config import apply_cli_overrides, load_experiment_config
from model_failure_lab.mitigations import (
    build_inherited_mitigation_config,
    load_parent_run_context,
    validate_distilbert_parent_run,
)
from model_failure_lab.runners.dispatch import build_scaffold_metrics, dispatch_mitigation
from model_failure_lab.tracking import (
    append_experiment_index,
    build_index_entry,
    build_run_metadata,
    generate_run_id,
    write_metadata,
    write_metrics,
)
from model_failure_lab.utils.paths import build_mitigation_run_dir

METHOD_PRESETS = {
    "reweighting": "civilcomments_distilbert_reweighting",
    "calibration": "civilcomments_distilbert_calibrated",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap a mitigation experiment run.")
    parser.add_argument("--run-id", required=True, help="Parent baseline run ID.")
    parser.add_argument("--method", choices=sorted(METHOD_PRESETS), required=True)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--notes")
    parser.add_argument("--output-run-id")
    return parser


def run_command(argv: Sequence[str] | None = None):
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    preset_name = METHOD_PRESETS[args.method]
    preset_config = load_experiment_config(preset_name)
    preset_config = apply_cli_overrides(
        preset_config,
        {
            "seed": args.seed,
            "notes": args.notes,
            "run_id": args.output_run_id or generate_run_id(args.method),
        },
    )
    if args.method == "reweighting":
        parent_context = load_parent_run_context(args.run_id)
        validate_distilbert_parent_run(parent_context)
        config = build_inherited_mitigation_config(parent_context, preset_config)
    else:
        config = preset_config
        config["parent_run_id"] = args.run_id

    run_dir = build_mitigation_run_dir(
        method_name=args.method,
        model_name=config["model_name"],
        run_id=config["run_id"],
        create=True,
    )
    command = "python scripts/run_mitigation.py " + " ".join(argv or [])
    metadata = build_run_metadata(
        run_id=config["run_id"],
        experiment_type="mitigation",
        model_name=config["model_name"],
        dataset_name=config["dataset_name"],
        split_details=config["split_details"],
        random_seed=config["seed"],
        resolved_config=config,
        command=command.strip(),
        run_dir=run_dir,
        parent_run_id=args.run_id,
        notes=config.get("notes", ""),
        tags=config.get("tags", []),
        status="scaffold_ready",
    )
    metadata_path = write_metadata(run_dir, metadata)
    metrics_path = write_metrics(run_dir, build_scaffold_metrics(config))
    append_experiment_index(build_index_entry(metadata_path, metadata))
    return dispatch_mitigation(
        config=config,
        method_name=args.method,
        parent_run_id=args.run_id,
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=metrics_path,
        preset_name=preset_name,
    )


def main(argv: Sequence[str] | None = None) -> int:
    result = run_command(argv)
    print(result.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
