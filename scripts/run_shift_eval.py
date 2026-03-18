from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from model_failure_lab.config import apply_cli_overrides, load_experiment_config
from model_failure_lab.runners.dispatch import build_scaffold_metrics, dispatch_shift_eval
from model_failure_lab.tracking import (
    append_experiment_index,
    build_index_entry,
    build_run_metadata,
    generate_run_id,
    write_metadata,
    write_metrics,
)
from model_failure_lab.utils.paths import build_report_dir

DEFAULT_PRESET = "civilcomments_distilbert_baseline"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap a shift-evaluation run.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--preset", default=DEFAULT_PRESET)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--notes")
    return parser


def run_command(argv: Sequence[str] | None = None):
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    config = load_experiment_config(args.preset)
    config = apply_cli_overrides(
        config,
        {
            "seed": args.seed,
            "notes": args.notes,
            "run_id": generate_run_id("shift_eval"),
            "experiment_group": args.run_id,
        },
    )

    report_root = build_report_dir(
        experiment_group=args.run_id,
        category="comparisons",
        create=True,
    )
    run_dir = report_root / Path(config["run_id"])
    command = "python scripts/run_shift_eval.py " + " ".join(argv or [])
    metadata = build_run_metadata(
        run_id=config["run_id"],
        experiment_type="shift_eval",
        model_name=config["model_name"],
        dataset_name=config["dataset_name"],
        split_details=config["split_details"],
        random_seed=config["seed"],
        resolved_config=config,
        command=command.strip(),
        run_dir=run_dir,
        parent_run_id=args.run_id,
        notes=config.get("notes", ""),
        tags=[*config.get("tags", []), "shift_eval"],
        status="scaffold_ready",
    )
    metadata_path = write_metadata(run_dir, metadata)
    metrics_path = write_metrics(run_dir, build_scaffold_metrics(config))
    append_experiment_index(build_index_entry(metadata_path, metadata))
    return dispatch_shift_eval(
        config=config,
        target_run_id=args.run_id,
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=metrics_path,
        preset_name=args.preset,
    )


def main(argv: Sequence[str] | None = None) -> int:
    result = run_command(argv)
    print(result.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
