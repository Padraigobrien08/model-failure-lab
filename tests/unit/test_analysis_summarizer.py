from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from model_failure_lab.adapters import ModelMetadata, ModelRequest, ModelResult, register_model
from model_failure_lab.analysis import (
    summarize_aggregate_query,
    summarize_case_query,
    summarize_delta_query,
    summarize_query_results,
)
from model_failure_lab.classifiers import ClassifierInput, ClassifierResult, register_classifier
from model_failure_lab.datasets import FailureDataset
from model_failure_lab.index import QueryFilters, rebuild_query_index
from model_failure_lab.reporting import (
    build_comparison_report,
    build_run_report,
    load_saved_run_artifacts,
    write_comparison_report_artifacts,
    write_report_artifacts,
)
from model_failure_lab.runner import execute_dataset_run, write_run_artifacts
from model_failure_lab.schemas import PromptCase

TEST_ADAPTER_ID = "analysis_test_adapter"
TEST_CLASSIFIER_ID = "analysis_test_classifier"


class AnalysisTestAdapter:
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


class AnalysisTestClassifier:
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
        register_model(TEST_ADAPTER_ID, AnalysisTestAdapter)
    except ValueError:
        pass
    try:
        register_classifier(TEST_CLASSIFIER_ID, AnalysisTestClassifier())
    except ValueError:
        pass


def _query_dataset() -> FailureDataset:
    return FailureDataset(
        dataset_id="analysis-fixture-v1",
        name="Analysis Fixture",
        cases=(
            PromptCase(id="case-stable", prompt="Stable no failure case", tags=("stable",)),
            PromptCase(id="case-improvement", prompt="Improvement case", tags=("delta",)),
            PromptCase(id="case-regression", prompt="Regression case", tags=("delta",)),
            PromptCase(id="case-swap", prompt="Swap case", tags=("delta",)),
        ),
    )


def _materialize_workspace(root: Path) -> None:
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


def test_case_insight_report_is_deterministic_and_grounded(tmp_path: Path) -> None:
    _materialize_workspace(tmp_path)
    rebuild_query_index(root=tmp_path)

    first = summarize_case_query(
        filters=QueryFilters(limit=10),
        root=tmp_path,
        sample_limit=10,
    )
    second = summarize_query_results(
        mode="cases",
        filters=QueryFilters(limit=10),
        root=tmp_path,
        sample_limit=10,
    )

    assert first.to_payload() == second.to_payload()
    assert first.analysis_mode == "heuristic"
    assert first.source_kind == "cases"
    assert any(pattern.kind == "failure_type" for pattern in first.patterns)
    assert any(pattern.kind == "prompt_cluster" for pattern in first.patterns)
    assert all(ref.kind == "run_case" for ref in first.evidence_links)
    assert all(ref.run_id and ref.case_id for ref in first.evidence_links)
    assert "Representative evidence covers all 4 matched cases." in first.summary


def test_delta_insight_report_is_grounded(tmp_path: Path) -> None:
    _materialize_workspace(tmp_path)
    rebuild_query_index(root=tmp_path)

    report = summarize_delta_query(
        filters=QueryFilters(limit=10),
        root=tmp_path,
        sample_limit=10,
    )

    assert report.source_kind == "deltas"
    assert any(pattern.kind == "delta_kind" for pattern in report.patterns)
    assert any(ref.kind == "comparison_case" for ref in report.evidence_links)
    assert "matched comparison deltas" in report.summary


def test_aggregate_insight_report_discloses_sampling_and_examples(tmp_path: Path) -> None:
    _materialize_workspace(tmp_path)
    rebuild_query_index(root=tmp_path)

    report = summarize_aggregate_query(
        group_by="failure_type",
        filters=QueryFilters(limit=10),
        root=tmp_path,
        sample_limit=1,
    )

    assert report.source_kind == "aggregates"
    assert report.sampling.truncated is True
    assert report.patterns
    assert report.patterns[0].evidence_refs
    assert all(ref.kind == "run_case" for ref in report.evidence_links)
