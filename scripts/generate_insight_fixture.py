#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from model_failure_lab.testing import materialize_insight_fixture  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate_insight_fixture.py",
        description=(
            "Create a deterministic local artifact workspace for query, summarize, compare, "
            "and debugger insight testing."
        ),
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT / "artifacts" / "insight-fixture-workspace",
        help=(
            "Artifact root to create. The directory must be empty or absent. "
            "Defaults to artifacts/insight-fixture-workspace under the repo root."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the generated fixture summary as JSON instead of human-readable text.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = materialize_insight_fixture(args.root, reuse_existing=True)

    if args.json:
        print(json.dumps(summary.to_payload(), indent=2, sort_keys=True))
        return 0

    print(render_summary(summary))
    return 0


def render_summary(summary) -> str:
    run_lines = "\n".join(
        f"- {run.model}: {run.run_id} (report: {run.report_id})"
        for run in summary.runs
    )
    comparison_lines = "\n".join(
        f"- {comparison.baseline_model} -> {comparison.candidate_model}: {comparison.report_id}"
        for comparison in summary.comparisons
    )
    first_comparison = summary.comparisons[0]
    return "\n".join(
        [
            "Failure Lab Insight Fixture",
            f"Root: {summary.root}",
            f"Dataset: {summary.dataset_id}",
            f"Dataset snapshot: {summary.dataset_path}",
            "",
            "Runs:",
            run_lines,
            "",
            "Comparisons:",
            comparison_lines,
            "",
            "Query index:",
            f"- {summary.query_index.path}",
            f"- runs={summary.query_index.run_count} cases={summary.query_index.case_count} comparisons={summary.query_index.comparison_count} case_deltas={summary.query_index.case_delta_count}",
            "",
            "Suggested commands:",
            f"- failure-lab query --root {summary.root} --failure-type hallucination --last-n 4 --summarize",
            f"- failure-lab compare {summary.runs[0].run_id} {summary.runs[1].run_id} --root {summary.root} --explain",
            f"- export FAILURE_LAB_ARTIFACT_ROOT={summary.root}",
            "- npm --prefix frontend run dev",
            f"- open /comparisons/{first_comparison.report_id} after the dev server starts",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
