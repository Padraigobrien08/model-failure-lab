# ruff: noqa: E402

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

try:
    from scripts._bootstrap import bootstrap_repo_paths
except ModuleNotFoundError:
    from _bootstrap import bootstrap_repo_paths

bootstrap_repo_paths()

from model_failure_lab.utils.paths import artifact_root

_EXPECTED_SEEDS = (13, 42, 87)
_REQUIRED_BASELINE_TAGS = {"baseline", "official", "v1.2_baseline"}


@dataclass(frozen=True)
class CohortSpec:
    name: str
    model_dir: str
    experiment_group: str
    model_tag: str


_COHORT_SPECS = {
    "logistic": CohortSpec(
        name="logistic",
        model_dir="logistic_tfidf",
        experiment_group="baselines_v1_2_logistic",
        model_tag="logistic",
    ),
    "distilbert": CohortSpec(
        name="distilbert",
        model_dir="distilbert",
        experiment_group="baselines_v1_2_distilbert",
        model_tag="distilbert",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect official Phase 17 baseline seed cohorts and eval coverage."
    )
    parser.add_argument(
        "--cohort",
        choices=("all", "logistic", "distilbert"),
        default="all",
        help="Limit output to one official model cohort.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Print machine-readable JSON instead of a text summary.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero unless every expected seed exists exactly once with a completed eval.",
    )
    return parser


def _parse_seed_tag(tags: list[str]) -> int | None:
    seed_tag = next((tag for tag in tags if tag.startswith("seed_")), None)
    if seed_tag is None:
        return None
    try:
        return int(seed_tag.split("_", 1)[1])
    except (IndexError, ValueError):
        return None


def _latest_completed_eval_id(run_dir: Path) -> str | None:
    evaluation_root = run_dir / "evaluations"
    if not evaluation_root.exists():
        return None

    completed_eval_ids: list[str] = []
    for metadata_path in evaluation_root.glob("*/metadata.json"):
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        if payload.get("status") == "completed":
            completed_eval_ids.append(metadata_path.parent.name)

    if not completed_eval_ids:
        return None
    return sorted(completed_eval_ids)[-1]


def _execution_tier(payload: dict[str, Any]) -> str | None:
    resolved_config = dict(payload.get("resolved_config") or {})
    model_config = dict(resolved_config.get("model") or {})
    return model_config.get("execution_tier") or model_config.get("tier")


def _load_runs_for_cohort(spec: CohortSpec) -> list[dict[str, Any]]:
    baseline_root = artifact_root() / "baselines" / spec.model_dir
    records: list[dict[str, Any]] = []

    if not baseline_root.exists():
        return records

    for metadata_path in sorted(baseline_root.glob("*/metadata.json")):
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        tags = [str(tag) for tag in payload.get("tags") or []]
        seed = _parse_seed_tag(tags)
        if payload.get("experiment_group") != spec.experiment_group:
            continue
        if payload.get("status") != "completed":
            continue
        if spec.model_tag not in tags:
            continue
        if not _REQUIRED_BASELINE_TAGS.issubset(tags):
            continue
        if seed is None:
            continue

        run_dir = metadata_path.parent
        records.append(
            {
                "seed": seed,
                "run_id": str(payload["run_id"]),
                "eval_id": _latest_completed_eval_id(run_dir),
                "status": str(payload["status"]),
                "metadata_path": str(metadata_path),
                "execution_tier": _execution_tier(payload),
                "tags": tags,
            }
        )

    return records


def _cohort_payload(spec: CohortSpec) -> dict[str, Any]:
    records = _load_runs_for_cohort(spec)
    by_seed: dict[int, list[dict[str, Any]]] = {}
    for record in records:
        by_seed.setdefault(int(record["seed"]), []).append(record)

    expected_seed_rows: list[dict[str, Any]] = []
    missing_seeds: list[int] = []
    duplicate_seeds: list[dict[str, Any]] = []
    extra_seeds: list[int] = []

    for seed in sorted(_EXPECTED_SEEDS):
        seed_records = sorted(by_seed.get(seed, []), key=lambda item: str(item["run_id"]))
        if not seed_records:
            missing_seeds.append(seed)
            expected_seed_rows.append(
                {
                    "seed": seed,
                    "present": False,
                    "run_id": None,
                    "eval_id": None,
                    "execution_tier": None,
                }
            )
            continue

        primary = seed_records[0]
        expected_seed_rows.append(
            {
                "seed": seed,
                "present": True,
                "run_id": primary["run_id"],
                "eval_id": primary["eval_id"],
                "execution_tier": primary["execution_tier"],
            }
        )
        if len(seed_records) > 1:
            duplicate_seeds.append(
                {
                    "seed": seed,
                    "run_ids": [str(record["run_id"]) for record in seed_records],
                }
            )

    for seed in sorted(by_seed):
        if seed not in _EXPECTED_SEEDS:
            extra_seeds.append(seed)

    eval_missing_seeds = sorted(
        row["seed"] for row in expected_seed_rows if row["present"] and not row["eval_id"]
    )
    complete = (
        not missing_seeds
        and not duplicate_seeds
        and not extra_seeds
        and not eval_missing_seeds
    )

    return {
        "experiment_group": spec.experiment_group,
        "expected_seeds": list(_EXPECTED_SEEDS),
        "missing_seeds": missing_seeds,
        "duplicate_seeds": duplicate_seeds,
        "extra_seeds": extra_seeds,
        "eval_missing_seeds": eval_missing_seeds,
        "complete": complete,
        "runs": expected_seed_rows,
    }


def run_command(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    selected_names = (
        list(_COHORT_SPECS.keys()) if args.cohort == "all" else [str(args.cohort)]
    )
    cohorts = {
        name: _cohort_payload(_COHORT_SPECS[name])
        for name in selected_names
    }
    payload = {
        "artifact_root": str(artifact_root()),
        "complete": all(bool(cohort["complete"]) for cohort in cohorts.values()),
        "cohorts": cohorts,
    }

    if args.as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload

    print("Phase 17 seeded cohort status")
    print(f"Artifact root: {payload['artifact_root']}")
    for name in selected_names:
        cohort = cohorts[name]
        status = "complete" if cohort["complete"] else "incomplete"
        print()
        print(f"[{name}] {status} :: {cohort['experiment_group']}")
        print("seed | run_id | eval_id | tier")
        for row in cohort["runs"]:
            run_id = row["run_id"] or "-"
            eval_id = row["eval_id"] or "-"
            tier = row["execution_tier"] or "-"
            print(f"{row['seed']} | {run_id} | {eval_id} | {tier}")
        if cohort["missing_seeds"]:
            print(f"missing seeds: {', '.join(str(seed) for seed in cohort['missing_seeds'])}")
        if cohort["eval_missing_seeds"]:
            print(
                "missing eval bundles: "
                + ", ".join(str(seed) for seed in cohort["eval_missing_seeds"])
            )
        if cohort["duplicate_seeds"]:
            duplicate_text = ", ".join(
                f"{row['seed']} -> {', '.join(row['run_ids'])}"
                for row in cohort["duplicate_seeds"]
            )
            print(f"duplicate seeds: {duplicate_text}")
        if cohort["extra_seeds"]:
            print(f"unexpected seeds: {', '.join(str(seed) for seed in cohort['extra_seeds'])}")

    return payload


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv) if argv is not None else None
    payload = run_command(args)
    if args is None:
        parsed = build_parser().parse_args()
    else:
        parsed = build_parser().parse_args(args)
    if parsed.strict and not payload["complete"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
