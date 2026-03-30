"""CLI-first entrypoint for the v1.8 failure-analysis engine."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from model_failure_lab.datasets import FailureDataset, load_dataset, load_demo_dataset
from model_failure_lab.reporting.artifacts import (
    write_comparison_report_artifacts,
    write_report_artifacts,
)
from model_failure_lab.reporting.compare import build_comparison_report
from model_failure_lab.reporting.core import build_run_report, summarize_case_executions
from model_failure_lab.reporting.load import SavedRunArtifacts, load_saved_run_artifacts
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

CANONICAL_COMMAND = "failure-lab"
COMPATIBILITY_COMMAND = "model-failure-lab"
DEFAULT_CLASSIFIER_ID = "heuristic_v1"
DEFAULT_RUN_SEED = 13


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
            "Use `demo` for deterministic local execution or an OpenAI model name "
            "such as `gpt-4.1-mini`."
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
        help="Override the dataset/run/report root for this invocation.",
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
        help="Override the dataset/run/report root for this invocation.",
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
        help="Override the dataset/run/report root for this invocation.",
    )
    compare_parser.set_defaults(handler=_handle_compare)

    demo_parser = subparsers.add_parser(
        "demo",
        help="Run the bundled deterministic demo flow and emit normal artifacts.",
    )
    demo_parser.add_argument(
        "--root",
        type=Path,
        help="Override the dataset/run/report root for this invocation.",
    )
    demo_parser.set_defaults(handler=_handle_demo)

    return parser


def _handle_run(args: argparse.Namespace) -> int:
    root = _normalized_root(args.root)
    dataset_path = _resolve_dataset_reference(args.dataset, root=root)
    dataset = load_dataset(dataset_path)
    adapter_id, model_name = _resolve_model_target(args.model)
    execution = execute_dataset_run(
        dataset=dataset,
        adapter_id=adapter_id,
        classifier_id=args.classifier,
        model=model_name,
        run_seed=DEFAULT_RUN_SEED,
    )
    run_path, results_path = write_run_artifacts(execution, root=root)
    print(_render_run_summary(execution, dataset, run_path, results_path))
    return 0


def _handle_report(args: argparse.Namespace) -> int:
    root = _normalized_root(args.root)
    saved_run = _load_saved_run_reference(args.run_ref, root=root)
    built = build_run_report(saved_run)
    report_path, details_path = write_report_artifacts(built.report, built.details, root=root)
    print(_render_report_summary(saved_run, built.report, report_path, details_path))
    return 0


def _handle_compare(args: argparse.Namespace) -> int:
    root = _normalized_root(args.root)
    baseline = _load_saved_run_reference(args.baseline, root=root)
    candidate = _load_saved_run_reference(args.candidate, root=root)
    built = build_comparison_report(baseline, candidate)
    report_path, details_path = write_comparison_report_artifacts(
        built.report,
        built.details,
        root=root,
    )
    print(_render_compare_summary(built.report, report_path, details_path))
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
    built = build_run_report(load_saved_run_artifacts(execution.run.run_id, root=root))
    report_path, details_path = write_report_artifacts(built.report, built.details, root=root)
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


def _resolve_dataset_reference(reference: str, *, root: Path | None) -> Path:
    source = Path(reference)
    if source.exists():
        if source.is_dir():
            raise FileNotFoundError(
                f"dataset reference is a directory, expected JSON file: {source}"
            )
        return source

    candidate = dataset_file(reference, root=root)
    if candidate.exists():
        return candidate
    raise FileNotFoundError(
        f"dataset not found: {reference}. Use a valid path or dataset ID under the active root."
    )


def _load_saved_run_reference(reference: str, *, root: Path | None) -> SavedRunArtifacts:
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


def _render_run_summary(
    execution: DatasetRunExecution,
    dataset: FailureDataset,
    run_path: Path,
    results_path: Path,
) -> str:
    summary = summarize_case_executions(execution.case_results)
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
    if execution.status == "completed_with_errors":
        lines.append("Warning: run completed with per-case errors.")
    return "\n".join(lines)


def _render_report_summary(
    saved_run: SavedRunArtifacts,
    report,
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
        "Artifacts:",
        f"- {report_path}",
        f"- {details_path}",
    ]
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
    summary = summarize_case_executions(execution.case_results)
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


def _render_compare_summary(report, report_path: Path, details_path: Path) -> str:
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
        f"Failure rate delta: {_format_signed_rate(delta.get('failure_rate'))}",
        f"Coverage delta: {_format_signed_rate(delta.get('classification_coverage'))}",
        "Artifacts:",
        f"- {report_path}",
        f"- {details_path}",
    ]
    if comparison.get("compatible") is False:
        lines.append("Warning: comparison is incompatible, but artifacts were still written.")
    return "\n".join(lines)

def _format_rate(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value) * 100:.1f}%"
    return "n/a"


def _format_signed_rate(value: object) -> str:
    if isinstance(value, (int, float)):
        sign = "+" if float(value) > 0 else ""
        return f"{sign}{float(value) * 100:.1f}%"
    return "n/a"


if __name__ == "__main__":
    raise SystemExit(main())
