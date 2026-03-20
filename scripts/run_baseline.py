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
from model_failure_lab.runners.dispatch import build_scaffold_metrics, dispatch_baseline
from model_failure_lab.tracking import (
    append_experiment_index,
    build_artifact_paths,
    build_index_entry,
    build_run_metadata,
    generate_run_id,
    resolve_prediction_splits,
    write_metadata,
    write_metrics,
)
from model_failure_lab.utils.paths import build_baseline_run_dir

MODEL_PRESETS = {
    "logistic_tfidf": {
        "canonical": "civilcomments_logistic_baseline",
    },
    "distilbert": {
        "canonical": "civilcomments_distilbert_baseline",
        "constrained": "civilcomments_distilbert_baseline_constrained",
    },
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap a baseline experiment run.")
    parser.add_argument("--model", choices=sorted(MODEL_PRESETS), required=True)
    parser.add_argument(
        "--tier",
        choices=("canonical", "constrained"),
        default="canonical",
        help="Select the runtime tier for baseline execution.",
    )
    parser.add_argument("--seed", type=int)
    parser.add_argument("--notes")
    parser.add_argument("--run-id")
    parser.add_argument("--experiment-group")
    parser.add_argument(
        "--tag",
        action="append",
        dest="tags",
        help="Add a comparison tag without replacing the preset tags. Repeatable.",
    )
    return parser


def resolve_preset_name(model_name: str, tier: str) -> str:
    presets_for_model = MODEL_PRESETS[model_name]
    if tier not in presets_for_model:
        supported_tiers = ", ".join(sorted(presets_for_model))
        raise ValueError(f"{model_name} supports tiers: {supported_tiers}")
    return presets_for_model[tier]


def run_command(argv: Sequence[str] | None = None):
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    preset_name = resolve_preset_name(args.model, args.tier)
    config = load_experiment_config(preset_name)
    config = apply_cli_overrides(
        config,
        {
            "seed": args.seed,
            "notes": args.notes,
            "run_id": args.run_id or generate_run_id("baseline"),
            "experiment_group": args.experiment_group,
            "tags": args.tags,
        },
    )
    config.setdefault("model", {})["execution_tier"] = args.tier

    run_dir = build_baseline_run_dir(config["model_name"], config["run_id"], create=True)
    command = "python scripts/run_baseline.py " + " ".join(argv or [])
    prediction_splits = resolve_prediction_splits(config)
    metadata = build_run_metadata(
        run_id=config["run_id"],
        experiment_type="baseline",
        model_name=config["model_name"],
        dataset_name=config["dataset_name"],
        split_details=config["split_details"],
        random_seed=config["seed"],
        resolved_config=config,
        command=command.strip(),
        run_dir=run_dir,
        artifact_paths=build_artifact_paths(run_dir, prediction_splits=prediction_splits),
        notes=config.get("notes", ""),
        tags=config.get("tags", []),
        status="scaffold_ready",
    )
    metadata_path = write_metadata(run_dir, metadata)
    metrics_path = write_metrics(run_dir, build_scaffold_metrics(config))
    append_experiment_index(build_index_entry(metadata_path, metadata))
    return dispatch_baseline(
        config=config,
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
