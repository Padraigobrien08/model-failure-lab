"""CLI-first entrypoint for the v1.8 failure-analysis engine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

from model_failure_lab.datasets import (
    available_bundled_dataset_ids,
    available_bundled_datasets,
    has_bundled_dataset,
    load_bundled_dataset,
    load_dataset,
    load_demo_dataset,
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
    datasets_list_parser.set_defaults(handler=_handle_datasets_list)

    return parser


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
    root = _normalized_root(args.root)
    baseline = _load_saved_run_reference(args.baseline, root=root)
    candidate = _load_saved_run_reference(args.candidate, root=root)
    built = _build_comparison_report(baseline, candidate)
    report_path, details_path = _write_comparison_report_artifacts(
        built.report,
        built.details,
        root=root,
    )
    print(_render_compare_summary(built.report, built.details, report_path, details_path))
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
    del args
    print(_render_bundled_dataset_list())
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


def _render_bundled_dataset_list() -> str:
    summaries = available_bundled_datasets()
    if not summaries:
        return "Failure Lab Datasets\nNo bundled datasets registered."

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

    widths = [max(len(row[index]) for row in rows) for index in range(len(rows[0]))]
    rendered_rows = []
    for index, row in enumerate(rows):
        rendered_row = "  ".join(
            value.ljust(widths[column_index])
            for column_index, value in enumerate(row)
        ).rstrip()
        rendered_rows.append(rendered_row)
        if index == 0:
            rendered_rows.append(
                "  ".join("-" * widths[column_index] for column_index in range(len(widths)))
            )

    return "\n".join(["Failure Lab Datasets", *rendered_rows])


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
