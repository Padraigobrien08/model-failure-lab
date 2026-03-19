from __future__ import annotations

import argparse
import json
from copy import deepcopy
from typing import Sequence

from model_failure_lab.config import RunConfig, apply_cli_overrides, load_experiment_config
from model_failure_lab.evaluation.bundle import build_evaluation_metadata
from model_failure_lab.runners.dispatch import dispatch_shift_eval
from model_failure_lab.tracking import (
    append_experiment_index,
    build_index_entry,
    generate_run_id,
    write_metadata,
)
from model_failure_lab.utils.paths import build_evaluation_run_dir, find_run_metadata_path

DEFAULT_PRESET = "civilcomments_distilbert_baseline"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate a saved baseline or mitigation run.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--preset", default=DEFAULT_PRESET)
    parser.add_argument("--splits")
    parser.add_argument("--min-group-support", type=int)
    parser.add_argument("--calibration-bins", type=int)
    parser.add_argument("--output-tag")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--notes")
    return parser


def _build_eval_config(
    source_metadata: dict[str, object],
    *,
    preset_name: str,
) -> dict[str, object]:
    preset_config = load_experiment_config(preset_name)
    source_config = deepcopy(source_metadata.get("resolved_config", {}))
    return {
        "run_id": source_config.get("run_id"),
        "experiment_name": str(
            source_config.get("experiment_name", preset_config["experiment_name"])
        ),
        "experiment_group": str(
            source_config.get("experiment_group", preset_config["experiment_group"])
        ),
        "experiment_type": "shift_eval",
        "model_name": str(
            source_metadata.get(
                "model_name",
                source_config.get("model_name", preset_config["model_name"]),
            )
        ),
        "dataset_name": str(
            source_metadata.get(
                "dataset_name",
                source_config.get("dataset_name", preset_config["dataset_name"]),
            )
        ),
        "split_details": dict(
            source_metadata.get(
                "split_details",
                source_config.get("split_details", preset_config["split_details"]),
            )
        ),
        "seed": int(source_config.get("seed", preset_config["seed"])),
        "tags": list(source_config.get("tags", preset_config.get("tags", []))),
        "notes": str(source_config.get("notes", "")),
        "parent_run_id": str(source_metadata["run_id"]),
        "data": deepcopy(source_config.get("data", preset_config["data"])),
        "model": deepcopy(source_config.get("model", preset_config["model"])),
        "train": deepcopy(source_config.get("train", preset_config["train"])),
        "eval": {
            **deepcopy(preset_config["eval"]),
            **deepcopy(source_config.get("eval", {})),
        },
    }


def run_command(argv: Sequence[str] | None = None):
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    source_metadata_path = find_run_metadata_path(args.run_id)
    source_metadata = json.loads(source_metadata_path.read_text(encoding="utf-8"))

    config = _build_eval_config(source_metadata, preset_name=args.preset)
    config = apply_cli_overrides(
        config,
        {
            "seed": args.seed,
            "notes": args.notes,
            "run_id": generate_run_id("shift_eval"),
            "experiment_group": args.run_id,
            "eval_splits": args.splits,
            "min_group_support": args.min_group_support,
            "calibration_bins": args.calibration_bins,
            "output_tag": args.output_tag,
        },
    )
    config = RunConfig.from_dict(config).to_dict()

    run_dir = build_evaluation_run_dir(
        source_metadata_path.parent,
        str(config["run_id"]),
        create=True,
    )
    command = "python scripts/run_shift_eval.py " + " ".join(argv or [])
    metadata = build_evaluation_metadata(
        eval_id=str(config["run_id"]),
        source_run_metadata=source_metadata,
        source_metadata_path=source_metadata_path,
        resolved_config=config,
        command=command.strip(),
        eval_dir=run_dir,
        evaluated_splits=list(config.get("eval", {}).get("requested_splits") or []),
        min_group_support=int(config["eval"]["min_group_support"]),
        calibration_bins=int(config["eval"]["calibration_bins"]),
        output_tag=config["eval"].get("output_tag"),
        status="running",
    )
    metadata_path = write_metadata(run_dir, metadata, create_checkpoint_dir=False)
    result = dispatch_shift_eval(
        config=config,
        target_run_id=args.run_id,
        source_metadata_path=source_metadata_path,
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=run_dir / "overall_metrics.json",
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
