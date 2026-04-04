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
    get_failure_cluster_detail,
    QueryFilters,
    aggregate_case_query,
    artifact_overview_summary,
    list_failure_clusters,
    list_comparison_inventory,
    list_query_facets,
    list_clusters_for_comparison,
    list_run_inventory,
    query_case_deltas,
    query_cases,
    query_comparison_signals,
)
from model_failure_lab.analysis import (  # noqa: E402
    build_query_insight_report,
    explain_comparison_report,
)
from model_failure_lab.harvest import harvest_artifact_cases  # noqa: E402
from model_failure_lab.datasets import (  # noqa: E402
    evolve_dataset_family,
    generate_regression_pack,
    list_dataset_versions,
)
from model_failure_lab.governance import recommend_dataset_action  # noqa: E402
from model_failure_lab.history import query_history_snapshot  # noqa: E402


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
            prompt_id=args.prompt_id,
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
        elif args.mode == "clusters":
            rows = [row.to_payload() for row in list_failure_clusters(
                filters,
                cluster_kind=None if args.cluster_kind == "all" else args.cluster_kind,
                recurring_only=not args.include_non_recurring,
                root=root,
            )]
        elif args.mode == "signals":
            rows = query_comparison_signals(
                filters,
                verdict=None if args.signal_direction == "all" else args.signal_direction,
                root=root,
            )
            rows = [
                {
                    **row,
                    "governance_recommendation": recommend_dataset_action(
                        str(row["report_id"]),
                        root=root,
                    ).to_payload(),
                }
                for row in rows
            ]
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
                "promptId": filters.prompt_id,
                "reportId": filters.report_id,
                "baselineRunId": filters.baseline_run_id,
                "candidateRunId": filters.candidate_run_id,
                "delta": filters.delta,
                "aggregateBy": args.aggregate_by if args.mode == "aggregates" else None,
                "clusterKind": args.cluster_kind if args.mode == "clusters" else None,
                "includeNonRecurring": (
                    args.include_non_recurring if args.mode == "clusters" else False
                ),
                "lastN": filters.last_n,
                "since": filters.since,
                "until": filters.until,
                "limit": filters.limit,
            },
            "facets": list_query_facets(root=root),
            "insight_report": (
                build_query_insight_report(
                    mode=args.mode,
                    filters=filters,
                    aggregate_by=args.aggregate_by,
                    root=root,
                ).to_payload()
                if args.summarize and args.mode not in {"signals", "clusters"}
                else None
            ),
            "rows": rows,
        }
    elif args.command == "comparison-insight":
        payload = {
            "report_id": args.report_id,
            "insight_report": explain_comparison_report(
                report_id=args.report_id,
                root=root,
            ).to_payload(),
        }
    elif args.command == "governance-recommend":
        payload = {
            "comparison_id": args.comparison_id,
            "recommendation": recommend_dataset_action(
                args.comparison_id,
                root=root,
            ).to_payload(),
        }
    elif args.command == "harvest":
        filters = QueryFilters(
            failure_type=args.failure_type,
            model=args.model,
            dataset=args.dataset,
            run_id=args.run_id,
            prompt_id=args.prompt_id,
            report_id=args.report_id,
            baseline_run_id=args.baseline_run_id,
            candidate_run_id=args.candidate_run_id,
            delta=args.delta,
            last_n=args.last_n,
            since=args.since,
            until=args.until,
            limit=args.limit,
        )
        output_path = _default_harvest_output_path(
            root=root,
            output_stem=args.output_stem,
            mode=args.mode,
            filters=filters,
            comparison_id=args.comparison_id,
        )
        summary = harvest_artifact_cases(
            filters=filters,
            output_path=output_path,
            root=root,
            comparison_id=args.comparison_id,
            mode=args.mode,
        )
        payload = {
            "source": build_source_descriptor(root),
            "dataset_id": summary.dataset.dataset_id,
            "lifecycle": summary.dataset.lifecycle,
            "mode": summary.mode,
            "output_path": str(summary.output_path),
            "selected_case_count": summary.selected_case_count,
        }
    elif args.command == "regression-pack":
        summary = generate_regression_pack(
            comparison_id=args.comparison_id,
            root=root,
            family_id=args.family_id,
            failure_type=args.failure_type,
            top_n=args.top_n,
            output_path=args.out,
        )
        payload = {
            "source": build_source_descriptor(root),
            **summary.to_payload(),
        }
    elif args.command == "dataset-evolve":
        summary = evolve_dataset_family(
            args.dataset_family,
            comparison_id=args.comparison_id,
            root=root,
            failure_type=args.failure_type,
            top_n=args.top_n,
            output_path=args.out,
        )
        payload = {
            "source": build_source_descriptor(root),
            **summary.to_payload(),
        }
    elif args.command == "dataset-versions":
        versions = list_dataset_versions(args.dataset_family, root=root)
        history = query_history_snapshot(
            family_id=args.dataset_family,
            root=root,
            limit=args.limit,
        )
        payload = {
            "source": build_source_descriptor(root),
            "family_id": args.dataset_family,
            "versions": [version.to_payload() for version in versions],
            "history": history.to_payload(),
        }
    elif args.command == "history":
        history = query_history_snapshot(
            dataset=args.dataset,
            model=args.model,
            family_id=args.family_id,
            root=root,
            limit=args.limit,
        )
        payload = {
            "source": build_source_descriptor(root),
            **history.to_payload(),
        }
    elif args.command == "cluster-detail":
        detail = get_failure_cluster_detail(
            args.cluster_id,
            root=root,
            limit=args.limit,
        )
        payload = {
            "source": build_source_descriptor(root),
            **detail.to_payload(),
        }
    elif args.command == "comparison-clusters":
        rows = list_clusters_for_comparison(
            args.report_id,
            root=root,
            limit=args.limit,
            recurring_only=not args.include_non_recurring,
        )
        payload = {
            "source": build_source_descriptor(root),
            "report_id": args.report_id,
            "rows": [row.to_payload() for row in rows],
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
    query_parser.add_argument(
        "--mode",
        choices=["cases", "deltas", "aggregates", "signals", "clusters"],
        required=True,
    )
    query_parser.add_argument("--failure-type")
    query_parser.add_argument("--model")
    query_parser.add_argument("--dataset")
    query_parser.add_argument("--run-id")
    query_parser.add_argument("--prompt-id")
    query_parser.add_argument("--report-id")
    query_parser.add_argument("--baseline-run-id")
    query_parser.add_argument("--candidate-run-id")
    query_parser.add_argument("--delta")
    query_parser.add_argument(
        "--aggregate-by",
        choices=["failure_type", "model", "dataset", "prompt_id"],
        default="failure_type",
    )
    query_parser.add_argument(
        "--signal-direction",
        choices=["regression", "improvement", "neutral", "incompatible", "all"],
        default="regression",
    )
    query_parser.add_argument(
        "--cluster-kind",
        choices=["run_case", "comparison_delta", "all"],
        default="all",
    )
    query_parser.add_argument("--include-non-recurring", action="store_true")
    query_parser.add_argument("--summarize", action="store_true")
    query_parser.add_argument("--last-n", type=int)
    query_parser.add_argument("--since")
    query_parser.add_argument("--until")
    query_parser.add_argument("--limit", type=int, default=20)

    comparison_insight_parser = subparsers.add_parser("comparison-insight")
    comparison_insight_parser.add_argument("--root", required=True)
    comparison_insight_parser.add_argument("--report-id", required=True)

    governance_recommend_parser = subparsers.add_parser("governance-recommend")
    governance_recommend_parser.add_argument("--root", required=True)
    governance_recommend_parser.add_argument("--comparison-id", required=True)

    harvest_parser = subparsers.add_parser("harvest")
    harvest_parser.add_argument("--root", required=True)
    harvest_parser.add_argument("--mode", choices=["cases", "deltas"], required=True)
    harvest_parser.add_argument("--failure-type")
    harvest_parser.add_argument("--model")
    harvest_parser.add_argument("--dataset")
    harvest_parser.add_argument("--run-id")
    harvest_parser.add_argument("--prompt-id")
    harvest_parser.add_argument("--report-id")
    harvest_parser.add_argument("--comparison-id")
    harvest_parser.add_argument("--baseline-run-id")
    harvest_parser.add_argument("--candidate-run-id")
    harvest_parser.add_argument("--delta")
    harvest_parser.add_argument("--last-n", type=int)
    harvest_parser.add_argument("--since")
    harvest_parser.add_argument("--until")
    harvest_parser.add_argument("--limit", type=int, default=200)
    harvest_parser.add_argument("--output-stem")

    regression_pack_parser = subparsers.add_parser("regression-pack")
    regression_pack_parser.add_argument("--root", required=True)
    regression_pack_parser.add_argument("--comparison-id", required=True)
    regression_pack_parser.add_argument("--family-id")
    regression_pack_parser.add_argument("--failure-type")
    regression_pack_parser.add_argument("--top-n", type=int, default=10)
    regression_pack_parser.add_argument("--out")

    dataset_evolve_parser = subparsers.add_parser("dataset-evolve")
    dataset_evolve_parser.add_argument("--root", required=True)
    dataset_evolve_parser.add_argument("--dataset-family", required=True)
    dataset_evolve_parser.add_argument("--comparison-id", required=True)
    dataset_evolve_parser.add_argument("--failure-type")
    dataset_evolve_parser.add_argument("--top-n", type=int, default=10)
    dataset_evolve_parser.add_argument("--out")

    dataset_versions_parser = subparsers.add_parser("dataset-versions")
    dataset_versions_parser.add_argument("--root", required=True)
    dataset_versions_parser.add_argument("--dataset-family", required=True)
    dataset_versions_parser.add_argument("--limit", type=int, default=10)

    history_parser = subparsers.add_parser("history")
    history_parser.add_argument("--root", required=True)
    history_scope = history_parser.add_mutually_exclusive_group(required=True)
    history_scope.add_argument("--dataset")
    history_scope.add_argument("--model")
    history_scope.add_argument("--family-id")
    history_parser.add_argument("--limit", type=int, default=10)

    cluster_detail_parser = subparsers.add_parser("cluster-detail")
    cluster_detail_parser.add_argument("--root", required=True)
    cluster_detail_parser.add_argument("--cluster-id", required=True)
    cluster_detail_parser.add_argument("--limit", type=int, default=20)

    comparison_clusters_parser = subparsers.add_parser("comparison-clusters")
    comparison_clusters_parser.add_argument("--root", required=True)
    comparison_clusters_parser.add_argument("--report-id", required=True)
    comparison_clusters_parser.add_argument("--limit", type=int, default=5)
    comparison_clusters_parser.add_argument("--include-non-recurring", action="store_true")

    return parser


def build_source_descriptor(root: Path) -> dict[str, str]:
    repo_root = Path(os.path.abspath(str(REPO_ROOT)))
    return {
        "label": "Configured artifact store" if root != repo_root else "Repo root artifact store",
        "path": str(root),
        "runsPath": str(root / "runs"),
        "reportsPath": str(root / "reports"),
    }


def _default_harvest_output_path(
    *,
    root: Path,
    output_stem: str | None,
    mode: str,
    filters: QueryFilters,
    comparison_id: str | None,
) -> str:
    stem = _slugify(
        output_stem
        or (
            f"analysis-{filters.failure_type or filters.dataset or filters.model or 'cases'}"
            if mode == "cases"
            else f"comparison-{comparison_id or filters.report_id or 'deltas'}-{filters.delta or 'slice'}"
        )
    )
    harvested_dir = root / "datasets" / "harvested"
    candidate = harvested_dir / f"{stem}.json"
    suffix = 2
    while candidate.exists():
        candidate = harvested_dir / f"{stem}-{suffix}.json"
        suffix += 1
    return os.path.relpath(candidate, root)


def _slugify(value: str) -> str:
    normalized = "".join(character if character.isalnum() else "-" for character in value.lower())
    collapsed = "-".join(part for part in normalized.split("-") if part)
    return collapsed or "harvested-draft"


if __name__ == "__main__":
    raise SystemExit(main())
