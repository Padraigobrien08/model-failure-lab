"""CLI-first entrypoint for the v1.8 failure-analysis engine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

from model_failure_lab.datasets import (
    DatasetEvolutionSummary,
    DatasetVersionRecord,
    RegressionPackDraftSummary,
    available_bundled_dataset_ids,
    available_bundled_datasets,
    available_local_datasets,
    evolve_dataset_family,
    generate_regression_pack,
    has_bundled_dataset,
    list_dataset_versions,
    load_bundled_dataset,
    load_dataset,
    load_demo_dataset,
)
from model_failure_lab.analysis import build_query_insight_report, explain_comparison_report
from model_failure_lab.harvest import (
    harvest_artifact_cases,
    promote_harvest_dataset,
    review_harvest_dataset,
)
from model_failure_lab.governance import (
    DatasetFamilyHealth,
    GovernanceApplyResult,
    GovernancePolicy,
    GovernanceRecommendation,
    apply_dataset_actions,
    list_dataset_family_health,
    recommend_dataset_action,
    review_dataset_actions,
)
from model_failure_lab.history import HistorySnapshot, query_history_snapshot
from model_failure_lab.index import (
    QueryFilters,
    aggregate_case_query,
    query_case_deltas,
    query_cases,
    query_comparison_signals,
    rebuild_query_index,
)
from model_failure_lab.runner.artifacts import write_run_artifacts
from model_failure_lab.runner.execute import DatasetRunExecution, execute_dataset_run
from model_failure_lab.schemas import Run
from model_failure_lab.storage import (
    RESULTS_FILENAME,
    RUN_FILENAME,
    dataset_file,
    read_json,
    write_json,
)

if TYPE_CHECKING:
    from model_failure_lab.datasets import FailureDataset
    from model_failure_lab.reporting.load import SavedRunArtifacts

CANONICAL_COMMAND = "failure-lab"
COMPATIBILITY_COMMAND = "model-failure-lab"
DEFAULT_CLASSIFIER_ID = "heuristic_v1"
DEFAULT_RUN_SEED = 13
DEFAULT_SIGNAL_ALERT_THRESHOLD = 0.05
DEFAULT_GOVERNANCE_REVIEW_LIMIT = 10
DEFAULT_HISTORY_LIMIT = 10


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = list(argv) if argv is not None else sys.argv[1:]
    if not args:
        parser.print_help()
        return 1

    parsed = parser.parse_args(args)
    handler = getattr(parsed, "handler", None)
    if handler is None:
        parser.print_help()
        return 1

    try:
        return int(handler(parsed))
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=CANONICAL_COMMAND,
        description=(
            "Run structured failure analysis on local prompt datasets and inspect the resulting "
            "run, report, and comparison artifacts."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run",
        help="Execute one dataset through the failure-analysis engine.",
    )
    run_parser.add_argument(
        "--dataset",
        required=True,
        help="Dataset path or canonical dataset ID under the active root.",
    )
    run_parser.add_argument(
        "--model",
        required=True,
        help=(
            "Use `demo` for deterministic local execution, an OpenAI model name such as "
            "`gpt-4.1-mini`, or explicit adapter routing such as `ollama:<model>` or "
            "`anthropic:<model>`."
        ),
    )
    run_parser.add_argument(
        "--classifier",
        default=DEFAULT_CLASSIFIER_ID,
        help=f"Registered classifier ID (default: {DEFAULT_CLASSIFIER_ID}).",
    )
    run_parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Override the artifact root for this invocation. Defaults to the current working "
            "directory."
        ),
    )
    run_parser.add_argument(
        "--full",
        action="store_true",
        help="For bundled datasets, include the extended tail instead of the default core slice.",
    )
    run_parser.add_argument(
        "--system-prompt",
        help="Attach a system prompt to each model request in this run.",
    )
    run_parser.add_argument(
        "--model-option",
        action="append",
        default=[],
        metavar="KEY=JSON_VALUE",
        help=(
            "Attach one JSON-valued model option such as `temperature=0` or "
            "`stop=[\"DONE\"]`. Repeat as needed."
        ),
    )
    run_parser.add_argument(
        "--ollama-host",
        help="Override the Ollama host URL when using `--model ollama:<model>`.",
    )
    run_parser.add_argument(
        "--anthropic-base-url",
        help="Override the Anthropic base URL when using `--model anthropic:<model>`.",
    )
    run_parser.set_defaults(handler=_handle_run)

    report_parser = subparsers.add_parser(
        "report",
        help="Build a compact report from one saved run.",
    )
    report_parser.add_argument(
        "--run",
        required=True,
        dest="run_ref",
        help="Run directory, run.json path, results.json path, or canonical run ID.",
    )
    report_parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Override the artifact root for this invocation. Defaults to the current working "
            "directory."
        ),
    )
    report_parser.set_defaults(handler=_handle_report)

    compare_parser = subparsers.add_parser(
        "compare",
        help="Compare two saved runs as baseline -> candidate.",
    )
    compare_parser.add_argument(
        "baseline",
        help="Baseline run directory/path or canonical run ID.",
    )
    compare_parser.add_argument(
        "candidate",
        help="Candidate run directory/path or canonical run ID.",
    )
    compare_parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Override the artifact root for this invocation. Defaults to the current working "
            "directory."
        ),
    )
    compare_parser.add_argument(
        "--score",
        action="store_true",
        help="Emit the raw persisted comparison signal payload as JSON.",
    )
    compare_parser.add_argument(
        "--summary",
        action="store_true",
        help="Emit a deterministic signal summary with top drivers and evidence-linked case ids.",
    )
    compare_parser.add_argument(
        "--alert",
        action="store_true",
        help="Only emit alert-style output when the comparison signal exceeds the alert threshold.",
    )
    compare_parser.add_argument(
        "--alert-threshold",
        type=float,
        default=DEFAULT_SIGNAL_ALERT_THRESHOLD,
        help="Minimum severity score needed before `--alert` emits output (default: 0.05).",
    )
    _add_analysis_arguments(compare_parser, verb="explain")
    compare_parser.set_defaults(handler=_handle_compare)

    demo_parser = subparsers.add_parser(
        "demo",
        help="Run the bundled deterministic demo flow and emit normal artifacts.",
    )
    demo_parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Override the artifact root for this invocation. Defaults to the current working "
            "directory."
        ),
    )
    demo_parser.set_defaults(handler=_handle_demo)

    datasets_parser = subparsers.add_parser(
        "datasets",
        help="Inspect bundled datasets available by canonical ID.",
    )
    datasets_subparsers = datasets_parser.add_subparsers(dest="datasets_command")

    datasets_list_parser = datasets_subparsers.add_parser(
        "list",
        help="List bundled datasets available by canonical ID.",
    )
    datasets_list_parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Override the artifact root for this invocation. Defaults to the current working "
            "directory."
        ),
    )
    datasets_list_parser.set_defaults(handler=_handle_datasets_list)

    dataset_parser = subparsers.add_parser(
        "dataset",
        help="Review or promote harvested dataset packs.",
    )
    dataset_subparsers = dataset_parser.add_subparsers(dest="dataset_command")

    dataset_review_parser = dataset_subparsers.add_parser(
        "review",
        help="Inspect deterministic duplicate groups inside one harvested draft dataset pack.",
    )
    dataset_review_parser.add_argument("draft_path", type=Path)
    dataset_review_parser.add_argument("--json", action="store_true", dest="as_json")
    dataset_review_parser.set_defaults(handler=_handle_dataset_review)

    dataset_promote_parser = dataset_subparsers.add_parser(
        "promote",
        help="Promote one harvested draft dataset pack into a curated dataset file.",
    )
    dataset_promote_parser.add_argument("draft_path", type=Path)
    dataset_promote_parser.add_argument("--dataset-id", required=True)
    dataset_promote_parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Override the artifact root for this invocation. Defaults to the current working "
            "directory."
        ),
    )
    dataset_promote_parser.add_argument(
        "--out",
        type=Path,
        help="Optional output path for the curated dataset JSON file.",
    )
    dataset_promote_parser.set_defaults(handler=_handle_dataset_promote)

    dataset_versions_parser = dataset_subparsers.add_parser(
        "versions",
        help="List immutable versions for one evolved dataset family.",
    )
    dataset_versions_parser.add_argument("dataset_id")
    dataset_versions_parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Override the artifact root for this invocation. Defaults to the current working "
            "directory."
        ),
    )
    dataset_versions_parser.add_argument("--json", action="store_true", dest="as_json")
    dataset_versions_parser.set_defaults(handler=_handle_dataset_versions)

    dataset_families_parser = dataset_subparsers.add_parser(
        "families",
        help="Inspect deterministic health summaries for evolved dataset families.",
    )
    dataset_families_parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Override the artifact root for this invocation. Defaults to the current working "
            "directory."
        ),
    )
    dataset_families_parser.add_argument("--json", action="store_true", dest="as_json")
    dataset_families_parser.set_defaults(handler=_handle_dataset_families)

    dataset_evolve_parser = dataset_subparsers.add_parser(
        "evolve",
        help="Create the next immutable dataset version from one saved comparison signal.",
    )
    dataset_evolve_parser.add_argument("dataset_id")
    dataset_evolve_parser.add_argument("--from-comparison", required=True, dest="comparison_id")
    dataset_evolve_parser.add_argument("--failure-type", dest="failure_type")
    dataset_evolve_parser.add_argument("--top-n", type=int, default=10)
    dataset_evolve_parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Override the artifact root for this invocation. Defaults to the current working "
            "directory."
        ),
    )
    dataset_evolve_parser.add_argument(
        "--out",
        type=Path,
        help="Optional output path for the new immutable dataset version JSON file.",
    )
    dataset_evolve_parser.add_argument("--json", action="store_true", dest="as_json")
    dataset_evolve_parser.set_defaults(handler=_handle_dataset_evolve)

    index_parser = subparsers.add_parser(
        "index",
        help="Manage the derived local query index over saved artifacts.",
    )
    index_subparsers = index_parser.add_subparsers(dest="index_command")

    index_rebuild_parser = index_subparsers.add_parser(
        "rebuild",
        help="Rebuild the derived local query index from saved artifacts.",
        description="Rebuild the derived local query index from saved artifacts.",
    )
    index_rebuild_parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Override the artifact root for this invocation. Defaults to the current working "
            "directory."
        ),
    )
    index_rebuild_parser.set_defaults(handler=_handle_index_rebuild)

    query_parser = subparsers.add_parser(
        "query",
        help="Run structured cross-run queries over the derived local index.",
    )
    query_parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Override the artifact root for this invocation. Defaults to the current working "
            "directory."
        ),
    )
    query_parser.add_argument("--failure-type", dest="failure_type")
    query_parser.add_argument("--model")
    query_parser.add_argument("--dataset")
    query_parser.add_argument("--run", dest="run_id")
    query_parser.add_argument("--report-id")
    query_parser.add_argument("--baseline-run")
    query_parser.add_argument("--candidate-run")
    query_parser.add_argument("--delta")
    query_parser.add_argument("--aggregate-by", choices=["failure_type", "model", "dataset", "prompt_id"])
    query_parser.add_argument("--last-n", type=int)
    query_parser.add_argument("--since")
    query_parser.add_argument("--until")
    query_parser.add_argument("--limit", type=int, default=20)
    _add_analysis_arguments(query_parser, verb="summarize")
    query_parser.add_argument("--json", action="store_true", dest="as_json")
    query_parser.set_defaults(handler=_handle_query)

    history_parser = subparsers.add_parser(
        "history",
        help="Inspect deterministic run, comparison, or dataset-family history over local artifacts.",
    )
    history_parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Override the artifact root for this invocation. Defaults to the current working "
            "directory."
        ),
    )
    history_scope = history_parser.add_mutually_exclusive_group(required=True)
    history_scope.add_argument("--dataset")
    history_scope.add_argument("--model")
    history_scope.add_argument("--family", dest="family_id")
    history_parser.add_argument("--limit", type=int, default=DEFAULT_HISTORY_LIMIT)
    history_parser.add_argument("--json", action="store_true", dest="as_json")
    history_parser.set_defaults(handler=_handle_history)

    regressions_parser = subparsers.add_parser(
        "regressions",
        help="List recent saved comparison signals ordered by severity.",
    )
    regressions_subparsers = regressions_parser.add_subparsers(dest="regressions_command")
    regressions_parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Override the artifact root for this invocation. Defaults to the current working "
            "directory."
        ),
    )
    regressions_parser.add_argument(
        "--direction",
        choices=["regression", "improvement", "neutral", "incompatible", "all"],
        default="regression",
    )
    regressions_parser.add_argument("--failure-type", dest="failure_type")
    regressions_parser.add_argument("--model")
    regressions_parser.add_argument("--dataset")
    regressions_parser.add_argument("--report-id")
    regressions_parser.add_argument("--baseline-run")
    regressions_parser.add_argument("--candidate-run")
    regressions_parser.add_argument("--last-n", type=int)
    regressions_parser.add_argument("--since")
    regressions_parser.add_argument("--until")
    regressions_parser.add_argument("--limit", type=int, default=10)
    regressions_parser.add_argument("--json", action="store_true", dest="as_json")
    regressions_parser.set_defaults(handler=_handle_regressions)

    regressions_generate_parser = regressions_subparsers.add_parser(
        "generate",
        help="Generate a deterministic draft regression pack from one saved comparison signal.",
    )
    regressions_generate_parser.add_argument("--comparison", required=True, dest="comparison_id")
    regressions_generate_parser.add_argument("--family-id")
    regressions_generate_parser.add_argument("--failure-type", dest="failure_type")
    regressions_generate_parser.add_argument("--top-n", type=int, default=10)
    regressions_generate_parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Override the artifact root for this invocation. Defaults to the current working "
            "directory."
        ),
    )
    regressions_generate_parser.add_argument(
        "--out",
        type=Path,
        help="Optional output path for the generated draft regression pack JSON file.",
    )
    regressions_generate_parser.add_argument("--json", action="store_true", dest="as_json")
    regressions_generate_parser.set_defaults(handler=_handle_regressions_generate)

    regressions_recommend_parser = regressions_subparsers.add_parser(
        "recommend",
        help="Evaluate one saved comparison against the deterministic governance policy.",
    )
    regressions_recommend_parser.add_argument("--comparison", required=True, dest="comparison_id")
    regressions_recommend_parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Override the artifact root for this invocation. Defaults to the current working "
            "directory."
        ),
    )
    _add_governance_policy_arguments(regressions_recommend_parser)
    regressions_recommend_parser.add_argument("--json", action="store_true", dest="as_json")
    regressions_recommend_parser.set_defaults(handler=_handle_regressions_recommend)

    regressions_review_parser = regressions_subparsers.add_parser(
        "review",
        help="Review recent governance recommendations over saved comparison signals.",
    )
    regressions_review_parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Override the artifact root for this invocation. Defaults to the current working "
            "directory."
        ),
    )
    _add_signal_filter_arguments(regressions_review_parser)
    _add_governance_policy_arguments(regressions_review_parser)
    regressions_review_parser.add_argument(
        "--include-ignored",
        action="store_true",
        help="Include `ignore` recommendations in the review output.",
    )
    regressions_review_parser.add_argument("--json", action="store_true", dest="as_json")
    regressions_review_parser.set_defaults(handler=_handle_regressions_review)

    regressions_apply_parser = regressions_subparsers.add_parser(
        "apply",
        help="Apply deterministic governance recommendations to saved comparison signals.",
    )
    regressions_apply_parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Override the artifact root for this invocation. Defaults to the current working "
            "directory."
        ),
    )
    _add_signal_filter_arguments(regressions_apply_parser)
    _add_governance_policy_arguments(regressions_apply_parser)
    regressions_apply_parser.add_argument(
        "--include-ignored",
        action="store_true",
        help="Include skipped `ignore` decisions in the apply output.",
    )
    regressions_apply_parser.add_argument("--json", action="store_true", dest="as_json")
    regressions_apply_parser.set_defaults(handler=_handle_regressions_apply)

    harvest_parser = subparsers.add_parser(
        "harvest",
        help="Harvest saved artifact cases into a draft dataset pack.",
    )
    harvest_parser.add_argument(
        "--root",
        type=Path,
        help=(
            "Override the artifact root for this invocation. Defaults to the current working "
            "directory."
        ),
    )
    harvest_parser.add_argument("--failure-type", dest="failure_type")
    harvest_parser.add_argument("--model")
    harvest_parser.add_argument("--dataset")
    harvest_parser.add_argument("--run", dest="run_id")
    harvest_parser.add_argument("--prompt-id")
    harvest_parser.add_argument("--report-id")
    harvest_parser.add_argument(
        "--comparison",
        dest="comparison_id",
        help="Saved comparison report ID to harvest delta cases from.",
    )
    harvest_parser.add_argument("--baseline-run")
    harvest_parser.add_argument("--candidate-run")
    harvest_parser.add_argument("--delta")
    harvest_parser.add_argument("--last-n", type=int)
    harvest_parser.add_argument("--since")
    harvest_parser.add_argument("--until")
    harvest_parser.add_argument("--limit", type=int, default=200)
    harvest_parser.add_argument(
        "--dataset-id",
        help="Optional draft dataset ID. Defaults to the output filename stem.",
    )
    harvest_parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Write the harvested draft dataset pack to this JSON path.",
    )
    harvest_parser.set_defaults(handler=_handle_harvest)

    return parser


def _add_signal_filter_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--failure-type", dest="failure_type")
    parser.add_argument("--model")
    parser.add_argument("--dataset")
    parser.add_argument("--report-id")
    parser.add_argument("--baseline-run")
    parser.add_argument("--candidate-run")
    parser.add_argument("--last-n", type=int)
    parser.add_argument("--since")
    parser.add_argument("--until")
    parser.add_argument("--limit", type=int, default=DEFAULT_GOVERNANCE_REVIEW_LIMIT)


def _add_governance_policy_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--min-severity",
        type=float,
        default=DEFAULT_SIGNAL_ALERT_THRESHOLD,
        dest="minimum_severity",
        help="Minimum severity needed before a regression qualifies for governance.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Maximum number of regression cases to preview or apply per comparison.",
    )
    parser.add_argument("--family-id", dest="family_id")
    parser.add_argument(
        "--family-case-cap",
        type=int,
        default=200,
        dest="family_case_cap",
        help="Maximum projected case count allowed for one dataset family.",
    )
    parser.add_argument(
        "--max-duplicate-ratio",
        type=float,
        default=0.6,
        dest="max_duplicate_ratio",
        help="Maximum duplicate ratio allowed before governance ignores a family update.",
    )
    parser.add_argument(
        "--recurrence-window",
        type=int,
        default=5,
        dest="recurrence_window",
        help="Recent history window used for deterministic recurring-regression context.",
    )
    parser.add_argument(
        "--recurrence-threshold",
        type=int,
        default=2,
        dest="recurrence_threshold",
        help="Minimum recent regressions needed before history can override a low-severity ignore.",
    )


def _build_signal_filters(args: argparse.Namespace) -> QueryFilters:
    return QueryFilters(
        failure_type=args.failure_type,
        model=args.model,
        dataset=args.dataset,
        report_id=args.report_id,
        baseline_run_id=args.baseline_run,
        candidate_run_id=args.candidate_run,
        last_n=args.last_n,
        since=args.since,
        until=args.until,
        limit=args.limit,
    )


def _build_governance_policy(args: argparse.Namespace) -> GovernancePolicy:
    return GovernancePolicy(
        minimum_severity=args.minimum_severity,
        top_n=args.top_n,
        failure_type=args.failure_type,
        family_id=args.family_id,
        family_case_cap=args.family_case_cap,
        max_duplicate_ratio=args.max_duplicate_ratio,
        recurrence_window=args.recurrence_window,
        recurrence_threshold=args.recurrence_threshold,
    )


def _handle_run(args: argparse.Namespace) -> int:
    root = _normalized_root(args.root)
    dataset, dataset_source = _load_dataset_reference(
        args.dataset,
        root=root,
        include_full=args.full,
    )
    adapter_id, model_name = _resolve_model_target(args.model)
    run_config = _build_run_config(
        dataset_source=dataset_source,
        include_full=args.full,
        adapter_id=adapter_id,
        system_prompt=args.system_prompt,
        model_options=_parse_model_options(args.model_option),
        ollama_host=args.ollama_host,
        anthropic_base_url=args.anthropic_base_url,
    )
    execution = execute_dataset_run(
        dataset=dataset,
        adapter_id=adapter_id,
        classifier_id=args.classifier,
        model=model_name,
        run_seed=DEFAULT_RUN_SEED,
        run_config=run_config,
    )
    run_path, results_path = write_run_artifacts(execution, root=root)
    print(_render_run_summary(execution, dataset, run_path, results_path))
    return 0


def _handle_report(args: argparse.Namespace) -> int:
    root = _normalized_root(args.root)
    saved_run = _load_saved_run_reference(args.run_ref, root=root)
    built = _build_run_report(saved_run)
    report_path, details_path = _write_report_artifacts(
        built.report,
        built.details,
        root=root,
    )
    print(
        _render_report_summary(
            saved_run,
            built.report,
            built.details,
            report_path,
            details_path,
        )
    )
    return 0


def _handle_compare(args: argparse.Namespace) -> int:
    if args.score and (args.summary or args.alert or args.explain):
        raise ValueError("`--score` cannot be combined with `--summary`, `--alert`, or `--explain`")
    if args.alert and (args.summary or args.explain):
        raise ValueError("`--alert` cannot be combined with `--summary` or `--explain`")

    root = _normalized_root(args.root)
    baseline = _load_saved_run_reference(args.baseline, root=root)
    candidate = _load_saved_run_reference(args.candidate, root=root)
    built = _build_comparison_report(baseline, candidate)
    report_path, details_path = _write_comparison_report_artifacts(
        built.report,
        built.details,
        root=root,
    )
    compare_summary = _render_compare_summary(built.report, built.details, report_path, details_path)
    if args.score:
        print(
            _render_json_payload(
                {
                    "report_id": built.report.report_id,
                    "baseline_run_id": built.report.comparison.get("baseline_run_id"),
                    "candidate_run_id": built.report.comparison.get("candidate_run_id"),
                    "status": built.report.status.get("overall"),
                    "compatible": built.report.comparison.get("compatible"),
                    "signal": _comparison_signal_payload(built.report, built.details),
                }
            )
        )
        return 0

    if args.alert:
        alert_output = _render_signal_alert(
            built.report,
            built.details,
            threshold=args.alert_threshold,
        )
        if alert_output is not None:
            print(alert_output)
        return 0

    output_sections = [compare_summary]
    if args.summary:
        output_sections.append(_render_signal_summary(built.report, built.details))
    if not args.explain:
        print("\n\n".join(output_sections))
        return 0

    rebuild_query_index(root=root)
    analysis_adapter_id, analysis_model_name, analysis_options = _resolve_analysis_request(args)
    insight_report = explain_comparison_report(
        report_id=built.report.report_id,
        root=root,
        analysis_mode=args.analysis_mode,
        analysis_adapter_id=analysis_adapter_id,
        analysis_model=analysis_model_name,
        analysis_system_prompt=args.analysis_system_prompt,
        analysis_options=analysis_options,
    )
    output_sections.append(_render_insight_report(insight_report))
    print("\n\n".join(output_sections))
    return 0


def _handle_demo(args: argparse.Namespace) -> int:
    root = _normalized_root(args.root)
    dataset = load_demo_dataset()
    dataset_path = _write_dataset_snapshot(dataset, root=root)
    execution = execute_dataset_run(
        dataset=dataset,
        adapter_id="demo",
        classifier_id=DEFAULT_CLASSIFIER_ID,
        model="demo",
        run_seed=DEFAULT_RUN_SEED,
    )
    run_path, results_path = write_run_artifacts(execution, root=root)
    built = _build_run_report(_load_saved_run_reference(execution.run.run_id, root=root))
    report_path, details_path = _write_report_artifacts(
        built.report,
        built.details,
        root=root,
    )
    print(
        _render_demo_summary(
            dataset=dataset,
            execution=execution,
            dataset_path=dataset_path,
            run_path=run_path,
            results_path=results_path,
            report_path=report_path,
            details_path=details_path,
            report_id=built.report.report_id,
        )
    )
    return 0


def _handle_datasets_list(args: argparse.Namespace) -> int:
    print(_render_dataset_catalog(root=_normalized_root(args.root)))
    return 0


def _handle_dataset_review(args: argparse.Namespace) -> int:
    review = review_harvest_dataset(args.draft_path)
    if args.as_json:
        payload = {
            "dataset_id": review.dataset.dataset_id,
            "lifecycle": review.dataset.lifecycle,
            "total_cases": review.total_cases,
            "unique_case_count": review.unique_case_count,
            "duplicate_case_count": review.duplicate_case_count,
            "duplicate_groups": [
                {
                    "canonical_case_id": group.canonical_case_id,
                    "kept_case_id": group.kept_case_id,
                    "case_ids": list(group.case_ids),
                    "source_case_ids": list(group.source_case_ids),
                    "size": group.size,
                    "match_kind": group.match_kind,
                }
                for group in review.duplicate_groups
            ],
        }
        print(_render_json_payload(payload))
        return 0
    print(_render_dataset_review(review))
    return 0


def _handle_dataset_promote(args: argparse.Namespace) -> int:
    summary = promote_harvest_dataset(
        args.draft_path,
        dataset_id=args.dataset_id,
        root=_normalized_root(args.root),
        output_path=args.out,
    )
    print(_render_dataset_promotion(summary))
    return 0


def _handle_dataset_versions(args: argparse.Namespace) -> int:
    rows = list_dataset_versions(args.dataset_id, root=_normalized_root(args.root))
    if args.as_json:
        print(
            _render_json_payload(
                {
                    "dataset_family_id": args.dataset_id,
                    "versions": [row.to_payload() for row in rows],
                }
            )
        )
        return 0
    print(_render_dataset_versions(args.dataset_id, rows))
    return 0


def _handle_dataset_evolve(args: argparse.Namespace) -> int:
    summary = evolve_dataset_family(
        args.dataset_id,
        comparison_id=args.comparison_id,
        root=_normalized_root(args.root),
        failure_type=args.failure_type,
        top_n=args.top_n,
        output_path=args.out,
    )
    if args.as_json:
        print(_render_json_payload(summary.to_payload()))
        return 0
    print(_render_dataset_evolution(summary))
    return 0


def _handle_index_rebuild(args: argparse.Namespace) -> int:
    root = _normalized_root(args.root)
    summary = rebuild_query_index(root=root)
    print(_render_index_rebuild_summary(summary))
    return 0


def _handle_query(args: argparse.Namespace) -> int:
    if args.delta and args.aggregate_by:
        raise ValueError("`--delta` and `--aggregate-by` cannot be combined in one query")

    root = _normalized_root(args.root)
    filters = QueryFilters(
        failure_type=args.failure_type,
        model=args.model,
        dataset=args.dataset,
        run_id=args.run_id,
        report_id=args.report_id,
        baseline_run_id=args.baseline_run,
        candidate_run_id=args.candidate_run,
        delta=args.delta,
        last_n=args.last_n,
        since=args.since,
        until=args.until,
        limit=args.limit,
    )
    if args.aggregate_by:
        rows = aggregate_case_query(args.aggregate_by, filters, root=root)
        query_kind = "aggregate"
    elif args.delta:
        rows = query_case_deltas(filters, root=root)
        query_kind = "delta"
    else:
        rows = query_cases(filters, root=root)
        query_kind = "cases"

    insight_report = None
    if args.summarize:
        analysis_adapter_id, analysis_model_name, analysis_options = _resolve_analysis_request(args)
        insight_report = build_query_insight_report(
            mode="aggregates" if args.aggregate_by else ("deltas" if args.delta else "cases"),
            filters=filters,
            aggregate_by=args.aggregate_by or "failure_type",
            root=root,
            analysis_mode=args.analysis_mode,
            analysis_adapter_id=analysis_adapter_id,
            analysis_model=analysis_model_name,
            analysis_system_prompt=args.analysis_system_prompt,
            analysis_options=analysis_options,
        )

    if args.as_json:
        payload = {
            "query_kind": query_kind,
            "filters": _query_filters_payload(filters, aggregate_by=args.aggregate_by),
            "rows": rows,
        }
        if insight_report is not None:
            payload["insight_report"] = insight_report.to_payload()
        print(
            _render_json_payload(payload)
        )
        return 0

    if insight_report is not None:
        print(_render_insight_report(insight_report))
        return 0

    if query_kind == "aggregate":
        print(_render_aggregate_rows(rows))
    elif query_kind == "delta":
        print(_render_delta_rows(rows))
    else:
        print(_render_case_rows(rows))
    return 0


def _handle_regressions(args: argparse.Namespace) -> int:
    root = _normalized_root(args.root)
    filters = _build_signal_filters(args)
    verdict = None if args.direction == "all" else args.direction
    rows = query_comparison_signals(filters, verdict=verdict, root=root)
    if args.as_json:
        print(
            _render_json_payload(
                {
                    "query_kind": "comparison_signals",
                    "filters": {
                        **_query_filters_payload(filters),
                        "direction": args.direction,
                    },
                    "rows": rows,
                }
            )
        )
        return 0
    print(_render_signal_rows(rows, direction=args.direction))
    return 0


def _handle_history(args: argparse.Namespace) -> int:
    snapshot = query_history_snapshot(
        dataset=args.dataset,
        model=args.model,
        family_id=args.family_id,
        limit=args.limit,
        root=_normalized_root(args.root),
    )
    if args.as_json:
        print(_render_json_payload(snapshot.to_payload()))
        return 0
    print(_render_history_snapshot(snapshot))
    return 0


def _handle_regressions_recommend(args: argparse.Namespace) -> int:
    recommendation = recommend_dataset_action(
        args.comparison_id,
        root=_normalized_root(args.root),
        policy=_build_governance_policy(args),
    )
    if args.as_json:
        print(_render_json_payload(recommendation.to_payload()))
        return 0
    print(_render_governance_recommendation(recommendation))
    return 0


def _handle_regressions_review(args: argparse.Namespace) -> int:
    recommendations = review_dataset_actions(
        filters=_build_signal_filters(args),
        root=_normalized_root(args.root),
        policy=_build_governance_policy(args),
        include_ignored=args.include_ignored,
    )
    if args.as_json:
        print(
            _render_json_payload(
                {
                    "query_kind": "governance_review",
                    "filters": _query_filters_payload(_build_signal_filters(args)),
                    "include_ignored": args.include_ignored,
                    "policy": _build_governance_policy(args).to_payload(),
                    "rows": [recommendation.to_payload() for recommendation in recommendations],
                }
            )
        )
        return 0
    print(_render_governance_review(recommendations, include_ignored=args.include_ignored))
    return 0


def _handle_regressions_apply(args: argparse.Namespace) -> int:
    results = apply_dataset_actions(
        filters=_build_signal_filters(args),
        root=_normalized_root(args.root),
        policy=_build_governance_policy(args),
        include_ignored=args.include_ignored,
    )
    if args.as_json:
        print(
            _render_json_payload(
                {
                    "query_kind": "governance_apply",
                    "filters": _query_filters_payload(_build_signal_filters(args)),
                    "include_ignored": args.include_ignored,
                    "policy": _build_governance_policy(args).to_payload(),
                    "rows": [result.to_payload() for result in results],
                }
            )
        )
        return 0
    print(_render_governance_apply(results, include_ignored=args.include_ignored))
    return 0


def _handle_regressions_generate(args: argparse.Namespace) -> int:
    summary = generate_regression_pack(
        comparison_id=args.comparison_id,
        root=_normalized_root(args.root),
        family_id=args.family_id,
        failure_type=args.failure_type,
        top_n=args.top_n,
        output_path=args.out,
    )
    if args.as_json:
        print(_render_json_payload(summary.to_payload()))
        return 0
    print(_render_regression_pack(summary))
    return 0


def _handle_harvest(args: argparse.Namespace) -> int:
    root = _normalized_root(args.root)
    filters = QueryFilters(
        failure_type=args.failure_type,
        model=args.model,
        dataset=args.dataset,
        run_id=args.run_id,
        prompt_id=args.prompt_id,
        report_id=args.report_id,
        baseline_run_id=args.baseline_run,
        candidate_run_id=args.candidate_run,
        delta=args.delta,
        last_n=args.last_n,
        since=args.since,
        until=args.until,
        limit=args.limit,
    )
    summary = harvest_artifact_cases(
        filters=filters,
        output_path=args.out,
        root=root,
        dataset_id=args.dataset_id,
        comparison_id=args.comparison_id,
    )
    print(_render_harvest_summary(summary))
    return 0


def _handle_dataset_families(args: argparse.Namespace) -> int:
    rows = list_dataset_family_health(root=_normalized_root(args.root))
    if args.as_json:
        print(
            _render_json_payload(
                {
                    "query_kind": "dataset_family_health",
                    "rows": [row.to_payload() for row in rows],
                }
            )
        )
        return 0
    print(_render_dataset_family_health(rows))
    return 0


def _load_dataset_reference(
    reference: str,
    *,
    root: Path | None,
    include_full: bool,
) -> tuple[FailureDataset, str]:
    source = Path(reference)
    if source.exists():
        if source.is_dir():
            raise FileNotFoundError(
                f"dataset reference is a directory, expected JSON file: {source}"
            )
        return load_dataset(source), "path"

    candidate = dataset_file(reference, root=root)
    if candidate.exists():
        return load_dataset(candidate), "root"
    if has_bundled_dataset(reference):
        return (
            load_bundled_dataset(reference, include_extended=include_full),
            "bundled",
        )

    bundled_ids = available_bundled_dataset_ids()
    bundled_hint = ""
    if bundled_ids:
        bundled_hint = f" Bundled IDs: {', '.join(bundled_ids)}."
    raise FileNotFoundError(
        "dataset not found: "
        f"{reference}. Use a valid path, dataset ID under the active root, or a bundled dataset ID."
        f"{bundled_hint}"
    )


def _build_run_config(
    *,
    dataset_source: str,
    include_full: bool,
    adapter_id: str,
    system_prompt: str | None = None,
    model_options: dict[str, object] | None = None,
    ollama_host: str | None = None,
    anthropic_base_url: str | None = None,
) -> dict[str, object]:
    config: dict[str, object] = {}
    if dataset_source == "bundled":
        config["dataset_source"] = "bundled"
        config["dataset_scope"] = "full" if include_full else "core"

    if isinstance(system_prompt, str) and system_prompt.strip():
        config["system_prompt"] = system_prompt.strip()

    parsed_model_options = dict(model_options or {})
    if ollama_host is not None:
        if adapter_id != "ollama":
            raise ValueError("`--ollama-host` requires `--model ollama:<model>`")
        if not ollama_host.strip():
            raise ValueError("`--ollama-host` must be a non-empty URL")
        parsed_model_options["base_url"] = ollama_host.strip()

    if anthropic_base_url is not None:
        if adapter_id != "anthropic":
            raise ValueError("`--anthropic-base-url` requires `--model anthropic:<model>`")
        if not anthropic_base_url.strip():
            raise ValueError("`--anthropic-base-url` must be a non-empty URL")
        parsed_model_options["base_url"] = anthropic_base_url.strip()

    if parsed_model_options:
        config["model_options"] = parsed_model_options

    return config


def _parse_model_options(values: Sequence[str]) -> dict[str, object]:
    parsed: dict[str, object] = {}
    for raw_option in values:
        key, separator, raw_value = raw_option.partition("=")
        if separator != "=" or not key.strip() or not raw_value.strip():
            raise ValueError(f"model option must use `key=json-value`: {raw_option}")
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"model option must use `key=json-value`: {raw_option}") from exc
        parsed[key.strip()] = value
    return parsed


def _load_saved_run_reference(reference: str, *, root: Path | None) -> SavedRunArtifacts:
    from model_failure_lab.reporting.load import load_saved_run_artifacts

    source = Path(reference)
    if source.exists():
        run_path = _resolve_run_json_path(source)
        run_payload = read_json(run_path)
        run = Run.from_payload(run_payload)
        resolved_root = run_path.parents[2]
        return load_saved_run_artifacts(run.run_id, root=resolved_root)
    return load_saved_run_artifacts(reference, root=root)


def _resolve_run_json_path(source: Path) -> Path:
    if source.is_dir():
        run_path = source / RUN_FILENAME
    elif source.name == RUN_FILENAME:
        run_path = source
    elif source.name == RESULTS_FILENAME:
        run_path = source.parent / RUN_FILENAME
    else:
        raise FileNotFoundError(
            "run reference must be a run directory, "
            f"{RUN_FILENAME}, {RESULTS_FILENAME}, or canonical run ID: {source}"
        )
    if not run_path.exists():
        raise FileNotFoundError(f"run.json not found for reference: {source}")
    return run_path


def _resolve_model_target(model_value: str) -> tuple[str, str]:
    normalized = model_value.strip()
    if not normalized:
        raise ValueError("model must be a non-empty string")

    if ":" in normalized:
        adapter_id, model_name = normalized.split(":", 1)
        adapter_id = adapter_id.strip()
        model_name = model_name.strip()
        if not adapter_id or not model_name:
            raise ValueError(
                "model must be either `demo`, an OpenAI model name, or `<adapter>:<model>`"
            )
        return adapter_id, model_name

    if normalized == "demo":
        return "demo", "demo"

    return "openai", normalized


def _normalized_root(root: Path | None) -> Path | None:
    return root.resolve() if root is not None else None


def _write_dataset_snapshot(dataset: FailureDataset, *, root: Path | None) -> Path:
    dataset_path = dataset_file(dataset.dataset_id, root=root, create=True)
    write_json(dataset_path, dataset.to_payload())
    return dataset_path


def _render_dataset_catalog(*, root: Path | None) -> str:
    summaries = available_bundled_datasets()
    local_summaries = available_local_datasets(root=root)
    lines = ["Failure Lab Datasets"]

    if summaries:
        rows = [
            (
                "id",
                "name",
                "target",
                "scope",
                "core",
                "full",
                "description",
            )
        ]
        for summary in summaries:
            rows.append(
                (
                    summary.dataset_id,
                    _truncate(summary.name, 24),
                    summary.target_failure_type,
                    summary.default_scope,
                    str(summary.core_case_count),
                    str(summary.full_case_count),
                    _truncate(summary.description, 68),
                )
            )
        lines.append(_render_table(rows))
    else:
        lines.append("No bundled datasets registered.")

    if local_summaries:
        lines.extend(
            [
                "",
                "Local dataset packs",
                _render_table(
                    [
                        ("id", "name", "lifecycle", "cases", "description"),
                        *[
                            (
                                summary.dataset_id,
                                _truncate(summary.name, 24),
                                summary.lifecycle,
                                str(summary.case_count),
                                _truncate(summary.description, 68),
                            )
                            for summary in local_summaries
                        ],
                    ]
                ),
            ]
        )

    return "\n".join(lines)


def _render_index_rebuild_summary(summary) -> str:
    return "\n".join(
        [
            "Failure Lab Index",
            f"Path: {summary.path}",
            f"Runs: {summary.run_count}",
            f"Cases: {summary.case_count}",
            f"Comparisons: {summary.comparison_count}",
            f"Case deltas: {summary.case_delta_count}",
        ]
    )


def _render_harvest_summary(summary) -> str:
    return "\n".join(
        [
            "Failure Lab Harvest",
            f"Dataset: {summary.dataset.dataset_id}",
            f"Lifecycle: {summary.dataset.lifecycle or 'draft'}",
            f"Mode: {summary.mode}",
            f"Cases: {summary.selected_case_count}",
            f"Output: {summary.output_path}",
        ]
    )


def _render_regression_pack(summary: RegressionPackDraftSummary) -> str:
    lines = [
        "Failure Lab Regression Pack",
        f"Comparison: {summary.comparison_id}",
        f"Dataset: {summary.dataset.dataset_id}",
        f"Suggested family: {summary.suggested_family_id}",
        f"Cases: {summary.selected_case_count}",
        f"Policy: top_n={summary.policy.top_n} failure_type={summary.policy.failure_type or 'all'}",
        f"Output: {summary.output_path}",
    ]
    top_driver = _first_signal_driver({"top_drivers": summary.signal.get("top_drivers", [])})
    lines.append(f"Primary driver: {top_driver}")
    if summary.preview_cases:
        lines.append(
            _render_table(
                [
                    ("case_id", "prompt_id", "driver", "transition"),
                    *[
                        (
                            entry.case_id,
                            entry.prompt_id,
                            entry.driver_failure_type or "n/a",
                            entry.transition_type,
                        )
                        for entry in summary.preview_cases
                    ],
                ]
            )
        )
    return "\n".join(lines)


def _render_dataset_review(review) -> str:
    lines = [
        "Failure Lab Dataset Review",
        f"Dataset: {review.dataset.dataset_id}",
        f"Lifecycle: {review.dataset.lifecycle or 'draft'}",
        f"Draft path: {review.draft_path}",
        f"Cases: total={review.total_cases} unique={review.unique_case_count} duplicates={review.duplicate_case_count}",
    ]
    if review.duplicate_groups:
        lines.append(
            _render_table(
                [
                    ("canonical_case", "kept_case", "group_size", "match_kind"),
                    *[
                        (
                            group.canonical_case_id,
                            group.kept_case_id,
                            str(group.size),
                            group.match_kind,
                        )
                        for group in review.duplicate_groups
                    ],
                ]
            )
        )
    return "\n".join(lines)


def _render_dataset_promotion(summary) -> str:
    return "\n".join(
        [
            "Failure Lab Dataset Promotion",
            f"Dataset: {summary.dataset.dataset_id}",
            f"Lifecycle: {summary.dataset.lifecycle or 'curated'}",
            f"Cases: total={summary.total_cases} unique={summary.unique_case_count} duplicates={summary.duplicate_case_count}",
            f"Output: {summary.output_path}",
        ]
    )


def _render_dataset_versions(
    dataset_family_id: str,
    rows: tuple[DatasetVersionRecord, ...],
) -> str:
    if not rows:
        return (
            "Failure Lab Dataset Versions\n"
            f"Family: {dataset_family_id}\n"
            "No immutable versions exist for this dataset family."
        )
    table_rows = [
        ("dataset_id", "version", "cases", "parent", "comparison", "severity"),
        *[
            (
                row.dataset_id,
                row.version_tag,
                str(row.case_count),
                row.parent_dataset_id or "root",
                row.source_comparison_id or "n/a",
                _format_rate(row.severity),
            )
            for row in rows
        ],
    ]
    return "\n".join(
        [
            "Failure Lab Dataset Versions",
            f"Family: {rows[0].family_id}",
            _render_table(table_rows),
        ]
    )


def _render_dataset_family_health(rows: tuple[DatasetFamilyHealth, ...]) -> str:
    if not rows:
        return "Failure Lab Dataset Families\nNo governed dataset families exist under the active root."
    return "\n".join(
        [
            "Failure Lab Dataset Families",
            _render_table(
                [
                    (
                        "family_id",
                        "health",
                        "trend",
                        "versions",
                        "latest",
                        "cases",
                        "fail_rate",
                        "driver",
                        "severity",
                    ),
                    *[
                        (
                            row.family_id,
                            row.health_label,
                            row.trend_label,
                            str(row.version_count),
                            row.latest_version_tag,
                            str(row.latest_case_count),
                            _format_rate(row.recent_fail_rate),
                            row.primary_failure_type or "n/a",
                            _format_rate(row.latest_severity),
                        )
                        for row in rows
                    ],
                ]
            ),
        ]
    )


def _render_dataset_evolution(summary: DatasetEvolutionSummary) -> str:
    lines = [
        "Failure Lab Dataset Evolution",
        f"Family: {summary.family_id}",
        f"Dataset: {summary.dataset.dataset_id}",
        f"Version: {summary.version_tag}",
        f"Parent: {summary.parent_dataset_id or 'none'}",
        (
            "Cases: "
            f"selected={summary.selected_case_count} "
            f"added={summary.added_case_count} "
            f"duplicates={summary.duplicate_case_count} "
            f"total={summary.total_case_count}"
        ),
        f"Comparison: {summary.comparison_id}",
        f"Output: {summary.output_path}",
    ]
    if summary.preview_cases:
        lines.append(
            _render_table(
                [
                    ("source_case", "prompt_id", "driver", "transition"),
                    *[
                        (
                            entry.source_case_id,
                            entry.prompt_id,
                            entry.driver_failure_type or "n/a",
                            entry.transition_type,
                        )
                        for entry in summary.preview_cases[: min(len(summary.preview_cases), 5)]
                    ],
                ]
            )
        )
    return "\n".join(lines)


def _render_governance_recommendation(recommendation: GovernanceRecommendation) -> str:
    lines = [
        "Failure Lab Governance Recommendation",
        f"Comparison: {recommendation.comparison_id}",
        f"Action: {recommendation.action}",
        f"Rule: {recommendation.policy_rule}",
        f"Severity: {_format_rate(recommendation.signal.get('severity'))}",
        f"Matched family: {recommendation.matched_family.family_id}",
        f"Family health: versions={recommendation.matched_family.version_count} projected_cases={recommendation.matched_family.projected_case_count} duplicates={recommendation.matched_family.duplicate_case_count}",
        (
            "Policy: "
            f"min_severity={recommendation.policy.minimum_severity:.3f} "
            f"top_n={recommendation.policy.top_n} "
            f"failure_type={recommendation.policy.failure_type or 'all'} "
            f"family_cap={recommendation.policy.family_case_cap or 'none'} "
            f"max_duplicate_ratio={recommendation.policy.max_duplicate_ratio if recommendation.policy.max_duplicate_ratio is not None else 'none'} "
            f"recurrence_window={recommendation.policy.recurrence_window} "
            f"recurrence_threshold={recommendation.policy.recurrence_threshold or 'none'}"
        ),
        f"Rationale: {recommendation.rationale}",
    ]
    if recommendation.history_context is not None:
        lines.extend(
            [
                (
                    "Recent history: "
                    f"{recommendation.history_context.scope_kind}={recommendation.history_context.scope_value} "
                    f"regressions={recommendation.history_context.recent_regression_count}/"
                    f"{recommendation.history_context.recent_comparison_count} "
                    f"trend={recommendation.history_context.comparison_trend.label} "
                    f"volatility={recommendation.history_context.comparison_trend.volatility_label}"
                ),
            ]
        )
        if recommendation.history_context.family_health is not None:
            lines.append(
                (
                    "Family trend: "
                    f"{recommendation.history_context.family_health.health_label} "
                    f"(fail_rate={_format_rate(recommendation.history_context.family_health.recent_fail_rate)}, "
                    f"previous={_format_rate(recommendation.history_context.family_health.previous_fail_rate)})"
                )
            )
        if recommendation.history_context.recurring_failures:
            lines.append(
                "Recurring drivers: "
                + ", ".join(
                    f"{pattern.failure_type} x{pattern.occurrences}"
                    for pattern in recommendation.history_context.recurring_failures
                )
            )
    if recommendation.preview_cases:
        lines.append(
            _render_table(
                [
                    ("source_case", "prompt_id", "driver", "transition"),
                    *[
                        (
                            entry.source_case_id,
                            entry.prompt_id,
                            entry.driver_failure_type or "n/a",
                            entry.transition_type,
                        )
                        for entry in recommendation.preview_cases
                    ],
                ]
            )
        )
    return "\n".join(lines)


def _render_history_snapshot(snapshot: HistorySnapshot) -> str:
    lines = [
        "Failure Lab History",
        f"Scope: {snapshot.scope_kind}={snapshot.scope_value}",
    ]
    if snapshot.run_trend is not None:
        lines.append(
            (
                "Run trend: "
                f"{snapshot.run_trend.label} "
                f"(delta={_format_signed_rate(snapshot.run_trend.delta)} "
                f"volatility={snapshot.run_trend.volatility_label})"
            )
        )
    if snapshot.comparison_trend is not None:
        lines.append(
            (
                "Comparison trend: "
                f"{snapshot.comparison_trend.label} "
                f"(net={_format_signed_rate(snapshot.comparison_trend.delta)} "
                f"volatility={snapshot.comparison_trend.volatility_label})"
            )
        )
    if snapshot.dataset_health is not None:
        lines.append(
            (
                "Dataset health: "
                f"{snapshot.dataset_health.health_label} "
                f"(recent={_format_rate(snapshot.dataset_health.recent_fail_rate)} "
                f"previous={_format_rate(snapshot.dataset_health.previous_fail_rate)} "
                f"runs={snapshot.dataset_health.evaluation_run_count})"
            )
        )
    if snapshot.recurring_failures:
        lines.append(
            "Recurring drivers: "
            + ", ".join(
                f"{pattern.failure_type} x{pattern.occurrences}"
                for pattern in snapshot.recurring_failures
            )
        )
    if snapshot.run_history:
        lines.append(
            _render_table(
                [
                    ("run_id", "created_at", "model", "failure_rate", "errors"),
                    *[
                        (
                            row.run_id,
                            row.created_at,
                            row.model,
                            _format_rate(row.failure_rate),
                            str(row.execution_error_count),
                        )
                        for row in snapshot.run_history
                    ],
                ]
            )
        )
    if snapshot.comparison_history:
        lines.append(
            _render_table(
                [
                    ("report_id", "created_at", "verdict", "severity", "net"),
                    *[
                        (
                            row.report_id,
                            row.created_at,
                            row.signal_verdict,
                            _format_rate(row.severity),
                            _format_signed_rate(row.net_score),
                        )
                        for row in snapshot.comparison_history
                    ],
                ]
            )
        )
    if snapshot.dataset_versions:
        lines.append(
            _render_table(
                [
                    ("dataset_id", "version", "runs", "fail_rate", "comparison"),
                    *[
                        (
                            row.dataset_id,
                            row.version_tag,
                            str(row.run_count),
                            _format_rate(row.average_failure_rate),
                            row.source_comparison_id or "n/a",
                        )
                        for row in snapshot.dataset_versions
                    ],
                ]
            )
        )
    return "\n".join(lines)


def _render_governance_review(
    recommendations: tuple[GovernanceRecommendation, ...],
    *,
    include_ignored: bool,
) -> str:
    if not recommendations:
        label = " including ignored decisions" if include_ignored else ""
        return f"Failure Lab Governance Review\nNo governance recommendations matched the current filters{label}."
    return "\n".join(
        [
            "Failure Lab Governance Review",
            _render_table(
                [
                    (
                        "comparison",
                        "action",
                        "family",
                        "rule",
                        "severity",
                        "cases",
                    ),
                    *[
                        (
                            recommendation.comparison_id,
                            recommendation.action,
                            recommendation.matched_family.family_id,
                            recommendation.policy_rule,
                            _format_rate(recommendation.signal.get("severity")),
                            str(recommendation.selected_case_count),
                        )
                        for recommendation in recommendations
                    ],
                ]
            ),
        ]
    )


def _render_governance_apply(
    results: tuple[GovernanceApplyResult, ...],
    *,
    include_ignored: bool,
) -> str:
    if not results:
        label = " including ignored decisions" if include_ignored else ""
        return f"Failure Lab Governance Apply\nNo governance actions were produced for the current filters{label}."
    return "\n".join(
        [
            "Failure Lab Governance Apply",
            _render_table(
                [
                    (
                        "comparison",
                        "status",
                        "action",
                        "family",
                        "dataset",
                        "rule",
                    ),
                    *[
                        (
                            result.comparison_id,
                            result.status,
                            result.action,
                            result.family_id,
                            result.dataset_id or "n/a",
                            result.policy_rule,
                        )
                        for result in results
                    ],
                ]
            ),
        ]
    )


def _render_case_rows(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "Failure Lab Query\nNo matching cross-run cases."
    table_rows = [("run_id", "dataset", "model", "case_id", "failure_type", "prompt")]
    for row in rows:
        table_rows.append(
            (
                str(row.get("run_id", "")),
                str(row.get("dataset", "")),
                str(row.get("model", "")),
                str(row.get("case_id", "")),
                str(row.get("failure_type", "")),
                _truncate(str(row.get("prompt", "")), 48),
            )
        )
    return "\n".join(["Failure Lab Query", _render_table(table_rows)])


def _render_delta_rows(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "Failure Lab Query\nNo matching saved deltas."
    table_rows = [("report_id", "delta_kind", "case_id", "baseline_run", "candidate_run", "prompt")]
    for row in rows:
        table_rows.append(
            (
                str(row.get("report_id", "")),
                str(row.get("delta_kind", "")),
                str(row.get("case_id", "")),
                str(row.get("baseline_run_id", "")),
                str(row.get("candidate_run_id", "")),
                _truncate(str(row.get("prompt", "")), 40),
            )
        )
    return "\n".join(["Failure Lab Query", _render_table(table_rows)])


def _render_signal_rows(
    rows: list[dict[str, object]],
    *,
    direction: str,
) -> str:
    if not rows:
        return "Failure Lab Signals\nNo saved comparison signals matched the current filters."
    title = "Failure Lab Regressions" if direction == "regression" else "Failure Lab Signals"
    table_rows = [
        (
            "report_id",
            "verdict",
            "severity",
            "dataset",
            "baseline_run",
            "candidate_run",
            "top_driver",
        )
    ]
    for row in rows:
        driver = _first_signal_driver(row)
        table_rows.append(
            (
                str(row.get("report_id", "")),
                str(row.get("signal_verdict", "")),
                _format_rate(row.get("severity")),
                str(row.get("dataset", "")),
                str(row.get("baseline_run_id", "")),
                str(row.get("candidate_run_id", "")),
                driver,
            )
        )
    return "\n".join([title, _render_table(table_rows)])


def _render_aggregate_rows(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "Failure Lab Query\nNo aggregate rows matched the current filters."
    table_rows = [("group", "label", "case_count")]
    for row in rows:
        table_rows.append(
            (
                str(row.get("group_key", "")),
                str(row.get("group_label", "")),
                str(row.get("case_count", "")),
            )
        )
    return "\n".join(["Failure Lab Query", _render_table(table_rows)])


def _render_table(rows: list[tuple[str, ...]]) -> str:
    widths = [max(len(row[index]) for row in rows) for index in range(len(rows[0]))]
    rendered: list[str] = []
    for index, row in enumerate(rows):
        rendered.append(
            "  ".join(value.ljust(widths[column_index]) for column_index, value in enumerate(row))
        )
        if index == 0:
            rendered.append("  ".join("-" * width for width in widths))
    return "\n".join(rendered)


def _query_filters_payload(
    filters: QueryFilters,
    *,
    aggregate_by: str | None = None,
) -> dict[str, object]:
    return {
        "failure_type": filters.failure_type,
        "model": filters.model,
        "dataset": filters.dataset,
        "run_id": filters.run_id,
        "prompt_id": filters.prompt_id,
        "report_id": filters.report_id,
        "baseline_run_id": filters.baseline_run_id,
        "candidate_run_id": filters.candidate_run_id,
        "delta": filters.delta,
        "aggregate_by": aggregate_by,
        "last_n": filters.last_n,
        "since": filters.since,
        "until": filters.until,
        "limit": filters.limit,
    }


def _render_json_payload(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def _render_insight_report(report) -> str:
    lines = [
        "Failure Lab Insights",
        f"Mode: {report.analysis_mode}",
        f"Source: {report.source_kind}",
        f"Generated by: {report.generated_by}",
        f"Summary: {report.summary}",
        (
            "Sampling: "
            f"sampled={report.sampling.sampled_matches}/{report.sampling.total_matches} "
            f"limit={report.sampling.sample_limit} truncated={report.sampling.truncated}"
        ),
    ]
    if report.patterns:
        lines.append("Patterns:")
        for pattern in report.patterns:
            share = f"{pattern.share * 100:.1f}%" if pattern.share is not None else "n/a"
            lines.append(
                f"- {pattern.label} [{pattern.kind}] count={pattern.count} share={share}: "
                f"{pattern.summary}"
            )
            if pattern.evidence_refs:
                lines.append(
                    "  evidence: "
                    + ", ".join(reference.label for reference in pattern.evidence_refs)
                )
    if report.anomalies:
        lines.append("Anomalies:")
        for anomaly in report.anomalies:
            lines.append(f"- {anomaly.label}: {anomaly.summary}")
    return "\n".join(lines)


def _add_analysis_arguments(parser: argparse.ArgumentParser, *, verb: str) -> None:
    parser.add_argument(
        f"--{verb}",
        action="store_true",
        help=f"Produce a structured insight report that {verb}s the current result set.",
    )
    parser.add_argument(
        "--analysis-mode",
        choices=["heuristic", "llm"],
        default="heuristic",
        help="Choose deterministic heuristic analysis or opt-in llm enrichment.",
    )
    parser.add_argument(
        "--analysis-model",
        help="Explicit model target used only when `--analysis-mode llm`, for example `anthropic:claude-sonnet-4-0`.",
    )
    parser.add_argument(
        "--analysis-system-prompt",
        help="Optional system prompt applied only to llm analysis requests.",
    )
    parser.add_argument(
        "--analysis-option",
        action="append",
        default=[],
        metavar="KEY=JSON_VALUE",
        help="Attach one JSON-valued adapter option used only for llm analysis. Repeat as needed.",
    )


def _resolve_analysis_request(
    args: argparse.Namespace,
) -> tuple[str | None, str | None, dict[str, object]]:
    if args.analysis_mode != "llm":
        return None, None, {}
    if not args.analysis_model:
        raise ValueError("`--analysis-model` is required when `--analysis-mode llm`")
    adapter_id, model_name = _resolve_model_target(args.analysis_model)
    return adapter_id, model_name, _parse_model_options(args.analysis_option)


def _build_run_report(saved_run: SavedRunArtifacts):
    from model_failure_lab.reporting.core import build_run_report

    return build_run_report(saved_run)


def _build_comparison_report(baseline: SavedRunArtifacts, candidate: SavedRunArtifacts):
    from model_failure_lab.reporting.compare import build_comparison_report

    return build_comparison_report(baseline, candidate)


def _write_report_artifacts(report, details, *, root: Path | None):
    from model_failure_lab.reporting.artifacts import write_report_artifacts

    return write_report_artifacts(report, details, root=root)


def _write_comparison_report_artifacts(report, details, *, root: Path | None):
    from model_failure_lab.reporting.artifacts import write_comparison_report_artifacts

    return write_comparison_report_artifacts(report, details, root=root)


def _summarize_case_results(case_results):
    from model_failure_lab.reporting.core import summarize_case_executions

    return summarize_case_executions(case_results)


def _render_run_summary(
    execution: DatasetRunExecution,
    dataset: FailureDataset,
    run_path: Path,
    results_path: Path,
) -> str:
    summary = _summarize_case_results(execution.case_results)
    metrics = summary.metrics_payload()
    lines = [
        "Failure Lab Run",
        f"Dataset: {dataset.dataset_id}",
        f"Model: {execution.run.model}",
        f"Adapter: {execution.adapter_id}",
        f"Classifier: {execution.classifier_id}",
        f"Run ID: {execution.run.run_id}",
        f"Status: {execution.status}",
        (
            "Cases: "
            f"attempted={metrics['attempted_case_count']} "
            f"classified={metrics['classified_case_count']} "
            f"errors={metrics['execution_error_count']}"
        ),
        f"Failure rate: {_format_rate(metrics.get('failure_rate'))}",
        f"Classification coverage: {_format_rate(metrics.get('classification_coverage'))}",
        "Artifacts:",
        f"- {run_path}",
        f"- {results_path}",
    ]
    dataset_scope = execution.run.config.get("dataset_scope")
    if isinstance(dataset_scope, str):
        lines.insert(6, f"Dataset scope: {dataset_scope}")
    if execution.status == "completed_with_errors":
        lines.append("Warning: run completed with per-case errors.")
        first_error = next((case.error for case in execution.case_results if case.error), None)
        if first_error is not None:
            lines.append(f"First error: {first_error.stage}: {first_error.message}")
    return "\n".join(lines)


def _render_report_summary(
    saved_run: SavedRunArtifacts,
    report,
    details: dict[str, object],
    report_path: Path,
    details_path: Path,
) -> str:
    metrics = report.metrics
    lines = [
        "Failure Lab Report",
        f"Run ID: {saved_run.run.run_id}",
        f"Report ID: {report.report_id}",
        f"Dataset: {saved_run.dataset_id}",
        f"Status: {report.status.get('overall', saved_run.status)}",
        (
            "Cases: "
            f"attempted={metrics.get('attempted_case_count', 0)} "
            f"classified={metrics.get('classified_case_count', 0)} "
            f"errors={metrics.get('execution_error_count', 0)}"
        ),
        f"Failure rate: {_format_rate(metrics.get('failure_rate'))}",
        f"Classification coverage: {_format_rate(metrics.get('classification_coverage'))}",
    ]
    failure_summary = _render_failure_type_summary(report.failure_counts, report.failure_rates)
    if failure_summary is not None:
        lines.append(f"Failure types: {failure_summary}")
    verdict_summary = _render_verdict_summary(details)
    if verdict_summary is not None:
        lines.append(f"Verdicts: {verdict_summary}")
    lines.extend(
        [
            "Artifacts:",
            f"- {report_path}",
            f"- {details_path}",
        ]
    )
    if saved_run.status == "completed_with_errors":
        lines.append("Warning: source run completed with per-case errors.")
    return "\n".join(lines)


def _render_demo_summary(
    *,
    dataset: FailureDataset,
    execution: DatasetRunExecution,
    dataset_path: Path,
    run_path: Path,
    results_path: Path,
    report_path: Path,
    details_path: Path,
    report_id: str,
) -> str:
    summary = _summarize_case_results(execution.case_results)
    metrics = summary.metrics_payload()
    lines = [
        "Failure Lab Demo",
        f"Dataset: {dataset.dataset_id}",
        f"Run ID: {execution.run.run_id}",
        f"Report ID: {report_id}",
        f"Status: {execution.status}",
        (
            "Cases: "
            f"attempted={metrics['attempted_case_count']} "
            f"classified={metrics['classified_case_count']} "
            f"errors={metrics['execution_error_count']}"
        ),
        f"Failure rate: {_format_rate(metrics.get('failure_rate'))}",
        "Artifacts:",
        f"- {dataset_path}",
        f"- {run_path}",
        f"- {results_path}",
        f"- {report_path}",
        f"- {details_path}",
    ]
    if execution.status == "completed_with_errors":
        lines.append("Warning: demo run completed with per-case errors.")
    return "\n".join(lines)


def _render_compare_summary(
    report,
    details: dict[str, object],
    report_path: Path,
    details_path: Path,
) -> str:
    comparison = report.comparison
    delta = report.metrics.get("delta", {})
    lines = [
        "Failure Lab Compare",
        f"Baseline: {comparison.get('baseline_run_id', 'unknown')}",
        f"Candidate: {comparison.get('candidate_run_id', 'unknown')}",
        f"Report ID: {report.report_id}",
        f"Status: {report.status.get('overall', 'unknown')}",
        f"Compatible: {comparison.get('compatible', False)}",
        (
            "Shared coverage: "
            f"shared={comparison.get('shared_case_count', 0)} "
            f"baseline_only={comparison.get('baseline_only_case_count', 0)} "
            f"candidate_only={comparison.get('candidate_only_case_count', 0)}"
        ),
        f"Signal verdict: {_comparison_signal_payload(report, details).get('verdict', 'unknown')}",
        (
            "Signal scores: "
            f"regression={_format_rate(_comparison_signal_payload(report, details).get('regression_score'))} "
            f"improvement={_format_rate(_comparison_signal_payload(report, details).get('improvement_score'))} "
            f"severity={_format_rate(_comparison_signal_payload(report, details).get('severity'))}"
        ),
        f"Failure rate delta: {_format_signed_rate(delta.get('failure_rate'))}",
        f"Coverage delta: {_format_signed_rate(delta.get('classification_coverage'))}",
    ]
    transition_summary = _render_transition_summary(details)
    if transition_summary is not None:
        lines.append(f"Case changes: {transition_summary}")
    lines.extend(
        [
            "Artifacts:",
            f"- {report_path}",
            f"- {details_path}",
        ]
    )
    if comparison.get("compatible") is False:
        lines.append("Warning: comparison is incompatible, but artifacts were still written.")
    return "\n".join(lines)


def _comparison_signal_payload(report, details: dict[str, object]) -> dict[str, object]:
    comparison = getattr(report, "comparison", {})
    if isinstance(comparison, dict):
        signal = comparison.get("signal")
        if isinstance(signal, dict):
            return signal
    signal = details.get("signal")
    if isinstance(signal, dict):
        return signal
    raise ValueError("comparison signal payload is unavailable")


def _render_signal_summary(report, details: dict[str, object]) -> str:
    signal = _comparison_signal_payload(report, details)
    drivers = signal.get("top_drivers")
    lines = [
        "Failure Lab Signal Summary",
        f"Report ID: {report.report_id}",
        f"Verdict: {signal.get('verdict', 'unknown')}",
        (
            "Scores: "
            f"regression={_format_rate(signal.get('regression_score'))} "
            f"improvement={_format_rate(signal.get('improvement_score'))} "
            f"severity={_format_rate(signal.get('severity'))} "
            f"net={_format_signed_rate(signal.get('net_score'))}"
        ),
    ]
    if isinstance(signal.get("reason"), str):
        lines.append(f"Reason: {signal['reason']}")
    if isinstance(drivers, list) and drivers:
        lines.append("Top drivers:")
        for driver in drivers:
            if not isinstance(driver, dict):
                continue
            evidence = driver.get("case_ids")
            evidence_suffix = ""
            if isinstance(evidence, list) and evidence:
                evidence_suffix = " evidence=" + ", ".join(str(case_id) for case_id in evidence[:3])
            lines.append(
                f"- {driver.get('failure_type', 'unknown')} "
                f"{_format_signed_rate(driver.get('delta'))} "
                f"({driver.get('direction', 'unknown')}){evidence_suffix}"
            )
    else:
        lines.append("Top drivers: none")
    return "\n".join(lines)


def _render_signal_alert(report, details: dict[str, object], *, threshold: float) -> str | None:
    signal = _comparison_signal_payload(report, details)
    verdict = signal.get("verdict")
    severity = signal.get("severity")
    if verdict not in {"regression", "improvement"} or not isinstance(severity, (int, float)):
        return None
    if float(severity) < threshold:
        return None
    primary_driver = _first_signal_driver(signal)
    return "\n".join(
        [
            "Failure Lab Alert",
            f"Report ID: {report.report_id}",
            f"Verdict: {verdict}",
            f"Severity: {_format_rate(severity)} (threshold {_format_rate(threshold)})",
            f"Primary driver: {primary_driver}",
        ]
    )


def _first_signal_driver(payload: dict[str, object]) -> str:
    drivers = payload.get("top_drivers")
    if not isinstance(drivers, list) or not drivers:
        return "n/a"
    first = drivers[0]
    if not isinstance(first, dict):
        return "n/a"
    evidence = first.get("case_ids")
    evidence_suffix = ""
    if isinstance(evidence, list) and evidence:
        evidence_suffix = f" [{', '.join(str(case_id) for case_id in evidence[:2])}]"
    return (
        f"{first.get('failure_type', 'unknown')} "
        f"{_format_signed_rate(first.get('delta'))}"
        f"{evidence_suffix}"
    )


def _render_failure_type_summary(
    failure_counts: dict[str, int],
    failure_rates: dict[str, float],
) -> str | None:
    if not failure_counts:
        return None
    return ", ".join(
        f"{failure_type}={_format_rate(failure_rates.get(failure_type))} ({count})"
        for failure_type, count in sorted(
            failure_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )[:3]
    )


def _render_verdict_summary(details: dict[str, object]) -> str | None:
    raw_counts = details.get("expectation_verdict_counts")
    if not isinstance(raw_counts, dict):
        return None
    parts: list[str] = []
    for verdict in ("unexpected_failure", "missed_expected"):
        count = raw_counts.get(verdict)
        if type(count) is int and count > 0:
            parts.append(f"{verdict}={count}")
    if not parts:
        return None
    return ", ".join(parts)


def _render_transition_summary(details: dict[str, object]) -> str | None:
    raw_counts = details.get("case_transition_counts")
    if not isinstance(raw_counts, dict):
        return None
    ordered_keys = (
        ("improvements", "improvements"),
        ("regressions", "regressions"),
        ("failure_type_swaps", "swaps"),
        ("error_changes", "error_changes"),
    )
    parts: list[str] = []
    for key, label in ordered_keys:
        count = raw_counts.get(key)
        if type(count) is int and count > 0:
            parts.append(f"{label}={count}")
    if not parts:
        return None
    return ", ".join(parts)


def _format_rate(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value) * 100:.1f}%"
    return "n/a"


def _format_signed_rate(value: object) -> str:
    if isinstance(value, (int, float)):
        sign = "+" if float(value) > 0 else ""
        return f"{sign}{float(value) * 100:.1f}%"
    return "n/a"


def _truncate(value: str, limit: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 1].rstrip()}…"


if __name__ == "__main__":
    raise SystemExit(main())
