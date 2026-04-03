from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from model_failure_lab.adapters import ModelMetadata, ModelRequest, ModelResult, register_model
from model_failure_lab.classifiers import ClassifierInput, ClassifierResult, register_classifier
from model_failure_lab.cli import main
from model_failure_lab.datasets import FailureDataset
from model_failure_lab.index import rebuild_query_index
from model_failure_lab.reporting import (
    build_comparison_report,
    build_run_report,
    load_saved_run_artifacts,
    write_comparison_report_artifacts,
    write_report_artifacts,
)
from model_failure_lab.runner import execute_dataset_run, write_run_artifacts
from model_failure_lab.schemas import PromptCase

TEST_ADAPTER_ID = "cli_insight_test_adapter"
TEST_CLASSIFIER_ID = "cli_insight_test_classifier"
TEST_ANALYSIS_ADAPTER_ID = "cli_insight_llm"
TEST_UNGROUNDED_ANALYSIS_ADAPTER_ID = "cli_insight_llm_ungrounded"


class CliInsightAdapter:
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


class CliInsightClassifier:
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


class CliInsightLlmAdapter:
    def generate(self, request: ModelRequest) -> ModelResult:
        if '"source_kind": "comparison"' in request.prompt:
            payload = {
                "summary": "Regressions and improvements split the comparison, with regression still carrying the sharpest risk signal.",
                "patterns": [
                    {
                        "kind": "delta_kind",
                        "group_key": "regression",
                        "summary": "Regression remains the clearest comparison driver in the saved delta set.",
                    }
                ],
                "anomalies": [],
            }
        else:
            payload = {
                "summary": "Hallucination is still the dominant recurring failure signal in this filtered result set.",
                "patterns": [
                    {
                        "kind": "failure_type",
                        "group_key": "hallucination",
                        "summary": "Hallucination remains the dominant recurring failure mode across the selected runs.",
                    }
                ],
                "anomalies": [],
            }
        return ModelResult(
            text=json.dumps(payload),
            metadata=ModelMetadata(model=request.model, latency_ms=3.0),
        )


class CliInsightUngroundedLlmAdapter:
    def generate(self, request: ModelRequest) -> ModelResult:
        del request
        payload = {
            "summary": "case-999 is now the dominant unexplained issue in this result set.",
            "patterns": [
                {
                    "kind": "failure_type",
                    "group_key": "made_up_failure",
                    "summary": "A made-up failure group is now dominant.",
                }
            ],
            "anomalies": [],
        }
        return ModelResult(
            text=json.dumps(payload),
            metadata=ModelMetadata(model="ungrounded-llm", latency_ms=2.0),
        )


def _ensure_test_registry() -> None:
    for model_id, factory in (
        (TEST_ADAPTER_ID, CliInsightAdapter),
        (TEST_ANALYSIS_ADAPTER_ID, CliInsightLlmAdapter),
        (TEST_UNGROUNDED_ANALYSIS_ADAPTER_ID, CliInsightUngroundedLlmAdapter),
    ):
        try:
            register_model(model_id, factory)
        except ValueError:
            pass
    try:
        register_classifier(TEST_CLASSIFIER_ID, CliInsightClassifier())
    except ValueError:
        pass


def _dataset() -> FailureDataset:
    return FailureDataset(
        dataset_id="cli-insight-fixture-v1",
        name="CLI Insight Fixture",
        cases=(
            PromptCase(id="case-stable", prompt="Stable no failure case", tags=("stable",)),
            PromptCase(id="case-improvement", prompt="Improvement case", tags=("delta",)),
            PromptCase(id="case-regression", prompt="Regression case", tags=("delta",)),
            PromptCase(id="case-swap", prompt="Swap case", tags=("delta",)),
        ),
    )


def _materialize_workspace(root: Path) -> tuple[str, str]:
    _ensure_test_registry()
    dataset = _dataset()
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
    return baseline_execution.run.run_id, candidate_execution.run.run_id


def test_query_command_can_summarize_in_heuristic_json_mode(tmp_path: Path, capsys) -> None:
    _materialize_workspace(tmp_path)
    rebuild_query_index(root=tmp_path)

    exit_code = main(
        [
            "query",
            "--root",
            str(tmp_path),
            "--summarize",
            "--json",
            "--limit",
            "10",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["insight_report"]["analysis_mode"] == "heuristic"
    assert payload["insight_report"]["source_kind"] == "cases"
    assert payload["insight_report"]["patterns"]


def test_query_command_can_enrich_summaries_in_llm_mode(tmp_path: Path, capsys) -> None:
    _materialize_workspace(tmp_path)
    rebuild_query_index(root=tmp_path)

    exit_code = main(
        [
            "query",
            "--root",
            str(tmp_path),
            "--summarize",
            "--analysis-mode",
            "llm",
            "--analysis-model",
            f"{TEST_ANALYSIS_ADAPTER_ID}:analysis-model",
            "--json",
            "--limit",
            "10",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["insight_report"]["analysis_mode"] == "llm"
    assert payload["insight_report"]["generated_by"] == "llm_enriched_v1"
    assert "dominant recurring failure mode" in payload["insight_report"]["patterns"][0]["summary"]


def test_query_command_llm_mode_requires_analysis_model(tmp_path: Path, capsys) -> None:
    _materialize_workspace(tmp_path)
    rebuild_query_index(root=tmp_path)

    exit_code = main(
        [
            "query",
            "--root",
            str(tmp_path),
            "--summarize",
            "--analysis-mode",
            "llm",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "`--analysis-model` is required when `--analysis-mode llm`" in captured.err


def test_compare_command_can_explain_saved_comparison(tmp_path: Path, capsys) -> None:
    baseline_run_id, candidate_run_id = _materialize_workspace(tmp_path)

    exit_code = main(
        [
            "compare",
            baseline_run_id,
            candidate_run_id,
            "--root",
            str(tmp_path),
            "--explain",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Failure Lab Compare" in output
    assert "Failure Lab Insights" in output
    assert "matched comparison deltas" in output


def test_compare_command_can_explain_saved_comparison_in_llm_mode(
    tmp_path: Path, capsys
) -> None:
    baseline_run_id, candidate_run_id = _materialize_workspace(tmp_path)

    exit_code = main(
        [
            "compare",
            baseline_run_id,
            candidate_run_id,
            "--root",
            str(tmp_path),
            "--explain",
            "--analysis-mode",
            "llm",
            "--analysis-model",
            f"{TEST_ANALYSIS_ADAPTER_ID}:analysis-model",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Failure Lab Compare" in output
    assert "Failure Lab Insights" in output
    assert "Regressions and improvements split the comparison" in output


def test_query_command_rejects_ungrounded_llm_output(tmp_path: Path, capsys) -> None:
    _materialize_workspace(tmp_path)
    rebuild_query_index(root=tmp_path)

    exit_code = main(
        [
            "query",
            "--root",
            str(tmp_path),
            "--summarize",
            "--analysis-mode",
            "llm",
            "--analysis-model",
            f"{TEST_UNGROUNDED_ANALYSIS_ADAPTER_ID}:analysis-model",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "unsupported evidence identifier" in captured.err or "unsupported insight group" in captured.err
