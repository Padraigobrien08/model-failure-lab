from __future__ import annotations

import argparse
import json
from copy import deepcopy
from typing import Sequence

from model_failure_lab.config import RunConfig, apply_cli_overrides, load_experiment_config
from model_failure_lab.data import load_canonical_civilcomments_dataset
from model_failure_lab.perturbations import (
    generate_perturbation_suite,
    select_source_samples,
    write_perturbation_bundle,
)
from model_failure_lab.runners.contracts import DispatchResult
from model_failure_lab.tracking import (
    append_experiment_index,
    build_index_entry,
    build_run_metadata,
    generate_run_id,
    write_metadata,
)
from model_failure_lab.utils.paths import (
    build_perturbation_artifact_paths,
    build_perturbation_run_dir,
    find_run_metadata_path,
)

DEFAULT_PRESET = "civilcomments_perturbation_stress"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Materialize a deterministic perturbation suite for one saved run."
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--preset", default=DEFAULT_PRESET)
    parser.add_argument("--source-split")
    parser.add_argument("--max-source-samples", type=int)
    parser.add_argument("--families")
    parser.add_argument("--severities")
    parser.add_argument("--selection-seed", type=int)
    parser.add_argument("--perturbation-seed", type=int)
    parser.add_argument("--output-tag")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--notes")
    parser.add_argument("--output-run-id")
    return parser


def _build_perturbation_config(
    source_metadata: dict[str, object],
    *,
    preset_name: str,
) -> dict[str, object]:
    preset_config = load_experiment_config(preset_name)
    source_config = deepcopy(source_metadata.get("resolved_config", {}))
    source_tags = list(source_config.get("tags", []))
    preset_tags = list(preset_config.get("tags", []))
    merged_tags = list(dict.fromkeys([*source_tags, *preset_tags, "perturbation", "synthetic_stress"]))
    perturbation_config = {
        **deepcopy(preset_config.get("perturbation", {})),
        **deepcopy(source_config.get("perturbation", {})),
    }
    return {
        "run_id": source_config.get("run_id"),
        "experiment_name": str(
            source_config.get("experiment_name", preset_config["experiment_name"])
        ),
        "experiment_group": str(
            source_config.get("experiment_group", preset_config["experiment_group"])
        ),
        "experiment_type": "perturbation_eval",
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
        "tags": merged_tags,
        "notes": str(source_config.get("notes", "")),
        "parent_run_id": str(source_metadata["run_id"]),
        "data": deepcopy(source_config.get("data", preset_config["data"])),
        "model": deepcopy(source_config.get("model", preset_config["model"])),
        "train": deepcopy(source_config.get("train", preset_config["train"])),
        "eval": {
            **deepcopy(preset_config["eval"]),
            **deepcopy(source_config.get("eval", {})),
        },
        "report": deepcopy(source_config.get("report", preset_config.get("report", {}))),
        "perturbation": perturbation_config,
    }


def run_command(argv: Sequence[str] | None = None) -> DispatchResult:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    source_metadata_path = find_run_metadata_path(args.run_id)
    source_metadata = json.loads(source_metadata_path.read_text(encoding="utf-8"))

    config = _build_perturbation_config(source_metadata, preset_name=args.preset)
    config = apply_cli_overrides(
        config,
        {
            "seed": args.seed,
            "notes": args.notes,
            "run_id": args.output_run_id or generate_run_id("perturbation"),
            "source_split": args.source_split,
            "max_source_samples": args.max_source_samples,
            "families": args.families,
            "severities": args.severities,
            "selection_seed": args.selection_seed,
            "perturbation_seed": args.perturbation_seed,
            "output_tag": args.output_tag,
        },
    )
    config = RunConfig.from_dict(config).to_dict()

    run_dir = build_perturbation_run_dir(
        source_metadata_path.parent,
        str(config["run_id"]),
        create=True,
    )

    dataset = load_canonical_civilcomments_dataset(config, download=True)
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
    artifact_paths = write_perturbation_bundle(
        run_dir,
        suite=suite,
        source_run_metadata=source_metadata,
        resolved_config=config,
        preview_limit=5,
    )

    command = "python scripts/run_perturbation_eval.py " + " ".join(argv or [])
    metadata = build_run_metadata(
        run_id=str(config["run_id"]),
        experiment_type="perturbation_eval",
        model_name=str(config["model_name"]),
        dataset_name=str(config["dataset_name"]),
        split_details=dict(config["split_details"]),
        random_seed=int(config["seed"]),
        resolved_config=config,
        command=command.strip(),
        run_dir=run_dir,
        artifact_paths=build_perturbation_artifact_paths(run_dir),
        parent_run_id=str(source_metadata["run_id"]),
        notes=str(config.get("notes", "")),
        tags=list(config.get("tags", [])),
        status="completed",
    )
    metadata["source_run_id"] = str(source_metadata["run_id"])
    metadata["source_metadata_path"] = str(source_metadata_path)
    metadata["selected_source_count"] = suite.source_sample_count
    metadata["perturbed_sample_count"] = suite.perturbed_sample_count
    metadata["perturbation_schema_version"] = suite.schema_version
    metadata["artifact_paths"] = artifact_paths
    metadata_path = write_metadata(run_dir, metadata, create_checkpoint_dir=False)
    final_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    append_experiment_index(build_index_entry(metadata_path, final_metadata))

    return DispatchResult(
        status="completed",
        message=(
            "Perturbation suite materialized for "
            f"{config['model_name']} with {suite.perturbed_sample_count} samples"
        ),
        run_dir=run_dir,
        metadata_path=metadata_path,
        metrics_path=run_dir / "suite_manifest.json",
        preset_name=args.preset,
        extras={
            "source_run_id": str(source_metadata["run_id"]),
            "selected_source_count": suite.source_sample_count,
            "perturbed_sample_count": suite.perturbed_sample_count,
        },
    )


def main(argv: Sequence[str] | None = None) -> int:
    result = run_command(argv)
    print(result.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
