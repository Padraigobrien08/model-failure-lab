from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import perf_counter

import pytest

from model_failure_lab.adapters import ModelMetadata, ModelRequest, ModelResult, register_model
from model_failure_lab.classifiers import ClassifierInput, ClassifierResult, register_classifier
from model_failure_lab.cli import main
from model_failure_lab.datasets import FailureDataset
from model_failure_lab.index import (
    QueryFilters,
    aggregate_case_query,
    aggregate_delta_query,
    artifact_overview_summary,
    count_case_query,
    count_delta_query,
    ensure_query_index,
    list_comparison_inventory,
    list_run_inventory,
    query_case_deltas,
    query_cases,
    query_comparison_signals,
    query_index_path,
    rebuild_query_index,
)
from model_failure_lab.reporting import (
    build_comparison_report,
    build_run_report,
    load_saved_run_artifacts,
    write_comparison_report_artifacts,
    write_report_artifacts,
)
from model_failure_lab.runner import execute_dataset_run, write_run_artifacts
from model_failure_lab.schemas import PromptCase

TEST_ADAPTER_ID = "query_test_adapter"
TEST_CLASSIFIER_ID = "query_test_classifier"


class QueryTestAdapter:
    def generate(self, request: ModelRequest) -> ModelResult:
        prompt = request.prompt.lower()
        if "improvement" in prompt:
            marker = "hallucination" if request.model == "baseline-model" else "no_failure"
        elif "regression" in prompt:
            marker = "no_failure" if request.model == "baseline-model" else "hallucination"
        elif "swap" in prompt:
            marker = "reasoning" if request.model == "baseline-model" else "instruction_following"
        else:
            marker = "no_failure"
        return ModelResult(
            text=f"{marker}::{request.prompt}",
            metadata=ModelMetadata(model=request.model, latency_ms=5.0),
        )


class QueryTestClassifier:
    def __call__(self, classifier_input: ClassifierInput) -> ClassifierResult:
        output = classifier_input.output.text
        if output.startswith("hallucination::"):
            return ClassifierResult(
                failure_type="hallucination",
                confidence=0.91,
                explanation="Unsupported factual claim detected.",
            )
        if output.startswith("reasoning::"):
            return ClassifierResult(
                failure_type="reasoning",
                confidence=0.82,
                explanation="Reasoning mismatch detected.",
            )
        if output.startswith("instruction_following::"):
            return ClassifierResult(
                failure_type="instruction_following",
                confidence=0.77,
                explanation="Instruction constraint missed.",
            )
        return ClassifierResult(
            failure_type="no_failure",
            confidence=0.18,
            explanation="No failure signal detected.",
        )


def _ensure_test_registry() -> None:
    try:
        register_model(TEST_ADAPTER_ID, QueryTestAdapter)
    except ValueError:
        pass
    try:
        register_classifier(TEST_CLASSIFIER_ID, QueryTestClassifier())
    except ValueError:
        pass


def _query_dataset() -> FailureDataset:
    return FailureDataset(
        dataset_id="query-fixture-v1",
        name="Query Fixture",
        cases=(
            PromptCase(id="case-stable", prompt="Stable no failure case", tags=("stable",)),
            PromptCase(id="case-improvement", prompt="Improvement case", tags=("delta",)),
            PromptCase(id="case-regression", prompt="Regression case", tags=("delta",)),
            PromptCase(id="case-swap", prompt="Swap case", tags=("delta",)),
        ),
    )


def _materialize_workspace(root: Path) -> dict[str, str]:
    _ensure_test_registry()
    dataset = _query_dataset()
    baseline_time = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    candidate_time = baseline_time + timedelta(minutes=5)
    comparison_time = candidate_time + timedelta(minutes=5)

    baseline_execution = execute_dataset_run(
        dataset=dataset,
        adapter_id=TEST_ADAPTER_ID,
        classifier_id=TEST_CLASSIFIER_ID,
        model="baseline-model",
        run_seed=13,
        now=baseline_time,
    )
    candidate_execution = execute_dataset_run(
        dataset=dataset,
        adapter_id=TEST_ADAPTER_ID,
        classifier_id=TEST_CLASSIFIER_ID,
        model="candidate-model",
        run_seed=13,
        now=candidate_time,
    )
    write_run_artifacts(baseline_execution, root=root)
    write_run_artifacts(candidate_execution, root=root)

    baseline_saved = load_saved_run_artifacts(baseline_execution.run.run_id, root=root)
    candidate_saved = load_saved_run_artifacts(candidate_execution.run.run_id, root=root)
    baseline_report = build_run_report(baseline_saved, now=baseline_time + timedelta(seconds=1))
    candidate_report = build_run_report(candidate_saved, now=candidate_time + timedelta(seconds=1))
    write_report_artifacts(baseline_report.report, baseline_report.details, root=root)
    write_report_artifacts(candidate_report.report, candidate_report.details, root=root)

    comparison_report = build_comparison_report(
        baseline_saved,
        candidate_saved,
        now=comparison_time,
    )
    write_comparison_report_artifacts(
        comparison_report.report,
        comparison_report.details,
        root=root,
    )

    return {
        "baseline_run_id": baseline_execution.run.run_id,
        "candidate_run_id": candidate_execution.run.run_id,
        "comparison_report_id": comparison_report.report.report_id,
    }


def test_rebuild_query_index_creates_expected_rows(tmp_path: Path) -> None:
    ids = _materialize_workspace(tmp_path)

    summary = rebuild_query_index(root=tmp_path)

    assert summary.path == query_index_path(root=tmp_path)
    assert summary.path.exists()
    assert summary.run_count == 2
    assert summary.case_count == 8
    assert summary.comparison_count == 1
    assert summary.case_delta_count == 3

    overview = artifact_overview_summary(root=tmp_path)
    assert overview == {
        "run_count": 2,
        "comparison_count": 1,
        "case_count": 4,
        "delta_count": 3,
    }

    run_inventory = list_run_inventory(root=tmp_path)
    assert [row["run_id"] for row in run_inventory] == [
        ids["candidate_run_id"],
        ids["baseline_run_id"],
    ]
    comparison_inventory = list_comparison_inventory(root=tmp_path)
    assert [row["report_id"] for row in comparison_inventory] == [ids["comparison_report_id"]]
    assert comparison_inventory[0]["compatible"] is True
    assert comparison_inventory[0]["signal_verdict"] == "neutral"
    assert comparison_inventory[0]["regression_score"] == 0.25
    assert comparison_inventory[0]["improvement_score"] == 0.25
    assert comparison_inventory[0]["severity"] == 0.25
    assert comparison_inventory[0]["top_drivers"] == [
        {
            "driver_rank": 0,
            "failure_type": "instruction_following",
            "delta": 0.25,
            "direction": "regression",
            "case_ids": ["case-swap"],
        },
        {
            "driver_rank": 1,
            "failure_type": "reasoning",
            "delta": -0.25,
            "direction": "improvement",
            "case_ids": ["case-swap"],
        },
    ]


def test_query_index_rebuild_is_deterministic(tmp_path: Path) -> None:
    _materialize_workspace(tmp_path)

    first = rebuild_query_index(root=tmp_path)
    with sqlite3.connect(first.path) as connection:
        first_rows = connection.execute(
            """
            SELECT run_id, case_id, failure_type
            FROM cases
            ORDER BY run_id, case_id
            """
        ).fetchall()

    second = rebuild_query_index(root=tmp_path)
    with sqlite3.connect(second.path) as connection:
        second_rows = connection.execute(
            """
            SELECT run_id, case_id, failure_type
            FROM cases
            ORDER BY run_id, case_id
            """
        ).fetchall()

    assert first.run_count == second.run_count == 2
    assert first.case_count == second.case_count == 8
    assert first_rows == second_rows


def test_ensure_query_index_refreshes_when_artifacts_change(tmp_path: Path) -> None:
    _materialize_workspace(tmp_path)

    first = ensure_query_index(root=tmp_path)
    second = ensure_query_index(root=tmp_path)

    assert first.rebuilt is True
    assert second.rebuilt is False


def test_rebuild_query_index_fails_for_partial_run_artifact(tmp_path: Path) -> None:
    broken_run = tmp_path / "runs" / "broken_run"
    broken_run.mkdir(parents=True)
    (broken_run / "run.json").write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="run artifact is incomplete"):
        rebuild_query_index(root=tmp_path)


def test_query_cases_and_aggregates_respect_filters(tmp_path: Path) -> None:
    ids = _materialize_workspace(tmp_path)
    rebuild_query_index(root=tmp_path)

    assert count_case_query(root=tmp_path) == 4
    assert count_delta_query(root=tmp_path) == 3

    hallucinations = query_cases(QueryFilters(failure_type="hallucination", limit=10), root=tmp_path)
    assert [(row["run_id"], row["case_id"]) for row in hallucinations] == [
        (ids["candidate_run_id"], "case-regression"),
        (ids["baseline_run_id"], "case-improvement"),
    ]

    latest_hallucinations = query_cases(
        QueryFilters(failure_type="hallucination", last_n=1, limit=10),
        root=tmp_path,
    )
    assert [(row["run_id"], row["case_id"]) for row in latest_hallucinations] == [
        (ids["candidate_run_id"], "case-regression"),
    ]

    baseline_aggregate = aggregate_case_query(
        "failure_type",
        QueryFilters(model="baseline-model", limit=10),
        root=tmp_path,
    )
    assert baseline_aggregate == [
        {"group_key": "hallucination", "group_label": "hallucination", "case_count": 1},
        {"group_key": "reasoning", "group_label": "reasoning", "case_count": 1},
    ]

    delta_aggregate = aggregate_delta_query("delta_kind", QueryFilters(limit=10), root=tmp_path)
    assert delta_aggregate == [
        {"group_key": "improvement", "group_label": "improvement", "case_count": 1},
        {"group_key": "regression", "group_label": "regression", "case_count": 1},
        {"group_key": "swap", "group_label": "swap", "case_count": 1},
    ]


def test_query_case_deltas_returns_regressions_and_improvements(tmp_path: Path) -> None:
    ids = _materialize_workspace(tmp_path)
    rebuild_query_index(root=tmp_path)

    regressions = query_case_deltas(QueryFilters(delta="regression", limit=10), root=tmp_path)
    improvements = query_case_deltas(QueryFilters(delta="improvement", limit=10), root=tmp_path)

    assert [(row["report_id"], row["case_id"]) for row in regressions] == [
        (ids["comparison_report_id"], "case-regression"),
    ]
    assert [(row["report_id"], row["case_id"]) for row in improvements] == [
        (ids["comparison_report_id"], "case-improvement"),
    ]

    pair_filtered = query_case_deltas(
        QueryFilters(
            delta="swap",
            baseline_run_id=ids["baseline_run_id"],
            candidate_run_id=ids["candidate_run_id"],
            limit=10,
        ),
        root=tmp_path,
    )
    assert [(row["report_id"], row["case_id"]) for row in pair_filtered] == [
        (ids["comparison_report_id"], "case-swap"),
    ]


def test_query_comparison_signals_orders_by_severity_and_supports_failure_type_filters(
    tmp_path: Path,
) -> None:
    ids = _materialize_workspace(tmp_path)
    rebuild_query_index(root=tmp_path)

    neutral_rows = query_comparison_signals(
        QueryFilters(limit=10),
        verdict="neutral",
        root=tmp_path,
    )
    assert [row["report_id"] for row in neutral_rows] == [ids["comparison_report_id"]]
    assert neutral_rows[0]["compatible"] is True
    assert neutral_rows[0]["top_drivers"][0]["failure_type"] == "instruction_following"

    filtered_rows = query_comparison_signals(
        QueryFilters(failure_type="instruction_following", limit=10),
        verdict="neutral",
        root=tmp_path,
    )
    assert [row["report_id"] for row in filtered_rows] == [ids["comparison_report_id"]]


def test_local_query_operations_finish_quickly(tmp_path: Path) -> None:
    _materialize_workspace(tmp_path)
    rebuild_query_index(root=tmp_path)

    started = perf_counter()
    hallucinations = query_cases(QueryFilters(failure_type="hallucination", limit=10), root=tmp_path)
    case_elapsed = perf_counter() - started

    started = perf_counter()
    regressions = query_case_deltas(QueryFilters(delta="regression", limit=10), root=tmp_path)
    delta_elapsed = perf_counter() - started

    started = perf_counter()
    failure_types = aggregate_case_query("failure_type", QueryFilters(limit=10), root=tmp_path)
    aggregate_elapsed = perf_counter() - started

    assert hallucinations
    assert regressions
    assert failure_types
    assert max(case_elapsed, delta_elapsed, aggregate_elapsed) < 1.0


def test_index_rebuild_cli_renders_summary(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _materialize_workspace(tmp_path)

    exit_code = main(["index", "rebuild", "--root", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Failure Lab Index" in output
    assert "Runs: 2" in output
    assert "Comparisons: 1" in output
    assert "Case deltas: 3" in output


def test_query_cli_renders_json_for_cases_and_deltas(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ids = _materialize_workspace(tmp_path)

    cases_exit = main(
        [
            "query",
            "--root",
            str(tmp_path),
            "--failure-type",
            "hallucination",
            "--last-n",
            "1",
            "--json",
        ]
    )
    cases_output = capsys.readouterr().out
    assert cases_exit == 0
    assert '"query_kind": "cases"' in cases_output
    assert ids["candidate_run_id"] in cases_output
    assert "case-regression" in cases_output

    deltas_exit = main(
        [
            "query",
            "--root",
            str(tmp_path),
            "--delta",
            "regression",
            "--json",
        ]
    )
    deltas_output = capsys.readouterr().out
    assert deltas_exit == 0
    assert '"query_kind": "delta"' in deltas_output
    assert ids["comparison_report_id"] in deltas_output
    assert "case-regression" in deltas_output
