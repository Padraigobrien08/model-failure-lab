from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from model_failure_lab.index import (  # noqa: E402
    QueryFilters,
    aggregate_case_query,
    artifact_overview_summary,
    list_comparison_inventory,
    list_query_facets,
    list_run_inventory,
    query_case_deltas,
    query_cases,
)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(os.path.abspath(os.path.expanduser(args.root)))

    if args.command == "overview":
        payload = artifact_overview_summary(root=root)
    elif args.command == "runs":
        payload = list_run_inventory(root=root)
    elif args.command == "comparisons":
        payload = list_comparison_inventory(root=root)
    elif args.command == "query":
        filters = QueryFilters(
            failure_type=args.failure_type,
            model=args.model,
            dataset=args.dataset,
            run_id=args.run_id,
            report_id=args.report_id,
            baseline_run_id=args.baseline_run_id,
            candidate_run_id=args.candidate_run_id,
            delta=args.delta,
            last_n=args.last_n,
            since=args.since,
            until=args.until,
            limit=args.limit,
        )
        if args.mode == "aggregates":
            rows = aggregate_case_query(args.aggregate_by, filters, root=root)
        elif args.mode == "deltas":
            rows = query_case_deltas(filters, root=root)
        else:
            rows = query_cases(filters, root=root)
        payload = {
            "source": build_source_descriptor(root),
            "mode": args.mode,
            "filters": {
                "failureType": filters.failure_type,
                "model": filters.model,
                "dataset": filters.dataset,
                "runId": filters.run_id,
                "reportId": filters.report_id,
                "baselineRunId": filters.baseline_run_id,
                "candidateRunId": filters.candidate_run_id,
                "delta": filters.delta,
                "aggregateBy": args.aggregate_by if args.mode == "aggregates" else None,
                "lastN": filters.last_n,
                "since": filters.since,
                "until": filters.until,
                "limit": filters.limit,
            },
            "facets": list_query_facets(root=root),
            "rows": rows,
        }
    else:
        raise ValueError(f"Unsupported query bridge command: {args.command}")

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="query_bridge.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    overview_parser = subparsers.add_parser("overview")
    overview_parser.add_argument("--root", required=True)

    runs_parser = subparsers.add_parser("runs")
    runs_parser.add_argument("--root", required=True)

    comparisons_parser = subparsers.add_parser("comparisons")
    comparisons_parser.add_argument("--root", required=True)

    query_parser = subparsers.add_parser("query")
    query_parser.add_argument("--root", required=True)
    query_parser.add_argument("--mode", choices=["cases", "deltas", "aggregates"], required=True)
    query_parser.add_argument("--failure-type")
    query_parser.add_argument("--model")
    query_parser.add_argument("--dataset")
    query_parser.add_argument("--run-id")
    query_parser.add_argument("--report-id")
    query_parser.add_argument("--baseline-run-id")
    query_parser.add_argument("--candidate-run-id")
    query_parser.add_argument("--delta")
    query_parser.add_argument(
        "--aggregate-by",
        choices=["failure_type", "model", "dataset", "prompt_id"],
        default="failure_type",
    )
    query_parser.add_argument("--last-n", type=int)
    query_parser.add_argument("--since")
    query_parser.add_argument("--until")
    query_parser.add_argument("--limit", type=int, default=20)

    return parser


def build_source_descriptor(root: Path) -> dict[str, str]:
    repo_root = Path(os.path.abspath(str(REPO_ROOT)))
    return {
        "label": "Configured artifact store" if root != repo_root else "Repo root artifact store",
        "path": str(root),
        "runsPath": str(root / "runs"),
        "reportsPath": str(root / "reports"),
    }


if __name__ == "__main__":
    raise SystemExit(main())
