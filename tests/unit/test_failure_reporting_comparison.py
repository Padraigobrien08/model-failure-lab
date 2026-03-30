from __future__ import annotations

from datetime import datetime, timezone

from model_failure_lab.adapters import ModelMetadata, ModelRequest, ModelResult, register_model
from model_failure_lab.classifiers import ClassifierInput, ClassifierResult, register_classifier
from model_failure_lab.datasets import FailureDataset
from model_failure_lab.reporting.artifacts import write_comparison_report_artifacts
from model_failure_lab.reporting.compare import build_comparison_report
from model_failure_lab.reporting.load import load_saved_run_artifacts
from model_failure_lab.runner import execute_dataset_run, write_run_artifacts
from model_failure_lab.schemas import PromptCase, Report
from model_failure_lab.storage import read_json


class ComparisonAdapter:
    def generate(self, request: ModelRequest) -> ModelResult:
        return ModelResult(
            text=f"model:{request.model}::{request.prompt}",
            metadata=ModelMetadata(model=request.model, latency_ms=7.0),
        )


class ComparisonClassifier:
    def __call__(self, classifier_input: ClassifierInput) -> ClassifierResult:
        output = classifier_input.output.text.lower()
        if "shared improvement" in output and "baseline-model" in output:
            return ClassifierResult(failure_type="reasoning", confidence=0.8)
        if "shared stable failure" in output:
            return ClassifierResult(failure_type="hallucination", confidence=0.7)
        return ClassifierResult(failure_type="no_failure", confidence=0.2)


class ComparisonFailingAdapter:
    def generate(self, request: ModelRequest) -> ModelResult:
        if "shared flaky" in request.prompt.lower() and request.model == "baseline-model":
            raise TimeoutError("Request timed out")
        return ModelResult(
            text=f"model:{request.model}::{request.prompt}",
            metadata=ModelMetadata(model=request.model, latency_ms=7.0),
        )


def test_build_comparison_report_surfaces_shared_and_missing_case_accounting(tmp_path) -> None:
    adapter_id = "unit-comparison-adapter-main"
    classifier_id = "unit-comparison-classifier-main"
    register_model(adapter_id, ComparisonAdapter)
    register_classifier(classifier_id, ComparisonClassifier())

    baseline_run_id = _write_saved_run(
        tmp_path,
        dataset=FailureDataset(
            dataset_id="reasoning-basics-v1",
            cases=(
                PromptCase(id="case-001", prompt="baseline only"),
                PromptCase(id="case-002", prompt="shared improvement"),
                PromptCase(id="case-003", prompt="shared stable failure"),
            ),
        ),
        model="baseline-model",
        seed=21,
        suffix_minutes=0,
        adapter_id=adapter_id,
        classifier_id=classifier_id,
    )
    candidate_run_id = _write_saved_run(
        tmp_path,
        dataset=FailureDataset(
            dataset_id="reasoning-basics-v1",
            cases=(
                PromptCase(id="case-002", prompt="shared improvement"),
                PromptCase(id="case-003", prompt="shared stable failure"),
                PromptCase(id="case-004", prompt="candidate only"),
            ),
        ),
        model="candidate-model",
        seed=22,
        suffix_minutes=1,
        adapter_id=adapter_id,
        classifier_id=classifier_id,
    )

    built = build_comparison_report(
        load_saved_run_artifacts(baseline_run_id, root=tmp_path),
        load_saved_run_artifacts(candidate_run_id, root=tmp_path),
        now=datetime(2026, 3, 30, 12, 45, 0, tzinfo=timezone.utc),
    )

    assert built.report.comparison == {
        "baseline_run_id": baseline_run_id,
        "candidate_run_id": candidate_run_id,
        "dataset_id": "reasoning-basics-v1",
        "compatible": True,
        "shared_case_count": 2,
        "baseline_only_case_count": 1,
        "candidate_only_case_count": 1,
        "metrics_computed_on": "shared_cases_only",
    }
    assert built.report.total_cases == 2
    assert built.report.failure_counts["reasoning"] == -1
    assert built.report.failure_rates["reasoning"] == -0.5
    assert built.report.metrics["baseline"]["failure_rate"] == 1.0
    assert built.report.metrics["candidate"]["failure_rate"] == 0.5
    assert built.report.metrics["delta"]["failure_rate"] == -0.5
    assert built.report.status == {"overall": "improved"}
    assert built.details["baseline_only_case_ids"] == ["case-001"]
    assert built.details["candidate_only_case_ids"] == ["case-004"]
    assert built.details["case_transition_counts"] == {
        "improvements": 1,
        "regressions": 0,
        "failure_type_swaps": 0,
        "error_changes": 0,
    }
    assert built.details["case_transition_summary"] == [
        {
            "transition_type": "failure_to_no_failure",
            "label": "failure -> no_failure",
            "count": 1,
            "case_ids": ["case-002"],
        }
    ]
    assert built.details["case_deltas"] == [
        {
            "case_id": "case-002",
            "prompt": "shared improvement",
            "tags": [],
            "transition_type": "failure_to_no_failure",
            "transition_label": "failure -> no_failure",
            "baseline_failure_type": "reasoning",
            "candidate_failure_type": "no_failure",
            "baseline_expectation_verdict": None,
            "candidate_expectation_verdict": None,
            "baseline_error_stage": None,
            "candidate_error_stage": None,
            "baseline_explanation": None,
            "candidate_explanation": None,
            "changed": True,
        }
    ]


def test_build_comparison_report_surfaces_error_state_changes(tmp_path) -> None:
    adapter_id = "unit-comparison-adapter-errors"
    classifier_id = "unit-comparison-classifier-errors"
    register_model(adapter_id, ComparisonFailingAdapter)
    register_classifier(classifier_id, ComparisonClassifier())

    baseline_run_id = _write_saved_run(
        tmp_path,
        dataset=FailureDataset(
            dataset_id="reasoning-basics-v1",
            cases=(PromptCase(id="case-001", prompt="shared flaky"),),
        ),
        model="baseline-model",
        seed=51,
        suffix_minutes=0,
        adapter_id=adapter_id,
        classifier_id=classifier_id,
    )
    candidate_run_id = _write_saved_run(
        tmp_path,
        dataset=FailureDataset(
            dataset_id="reasoning-basics-v1",
            cases=(PromptCase(id="case-001", prompt="shared flaky"),),
        ),
        model="candidate-model",
        seed=52,
        suffix_minutes=1,
        adapter_id=adapter_id,
        classifier_id=classifier_id,
    )

    built = build_comparison_report(
        load_saved_run_artifacts(baseline_run_id, root=tmp_path),
        load_saved_run_artifacts(candidate_run_id, root=tmp_path),
        now=datetime(2026, 3, 30, 12, 47, 0, tzinfo=timezone.utc),
    )

    assert built.details["case_transition_counts"] == {
        "improvements": 0,
        "regressions": 0,
        "failure_type_swaps": 0,
        "error_changes": 1,
    }
    assert built.details["case_transition_summary"] == [
        {
            "transition_type": "error_cleared",
            "label": "error cleared",
            "count": 1,
            "case_ids": ["case-001"],
        }
    ]
    assert built.details["case_deltas"][0]["transition_type"] == "error_cleared"
    assert built.details["case_deltas"][0]["baseline_error_stage"] == "model_invoke"
    assert built.details["case_deltas"][0]["candidate_error_stage"] is None


def test_build_comparison_report_flags_incompatible_datasets(tmp_path) -> None:
    adapter_id = "unit-comparison-adapter-incompatible"
    classifier_id = "unit-comparison-classifier-incompatible"
    register_model(adapter_id, ComparisonAdapter)
    register_classifier(classifier_id, ComparisonClassifier())

    baseline_run_id = _write_saved_run(
        tmp_path,
        dataset=FailureDataset(
            dataset_id="reasoning-basics-v1",
            cases=(PromptCase(id="case-001", prompt="shared improvement"),),
        ),
        model="baseline-model",
        seed=31,
        suffix_minutes=0,
        adapter_id=adapter_id,
        classifier_id=classifier_id,
    )
    candidate_run_id = _write_saved_run(
        tmp_path,
        dataset=FailureDataset(
            dataset_id="hallucination-basics-v1",
            cases=(PromptCase(id="case-001", prompt="shared improvement"),),
        ),
        model="candidate-model",
        seed=32,
        suffix_minutes=1,
        adapter_id=adapter_id,
        classifier_id=classifier_id,
    )

    built = build_comparison_report(
        load_saved_run_artifacts(baseline_run_id, root=tmp_path),
        load_saved_run_artifacts(candidate_run_id, root=tmp_path),
        now=datetime(2026, 3, 30, 12, 50, 0, tzinfo=timezone.utc),
    )

    assert built.report.comparison["compatible"] is False
    assert built.report.comparison["reason"] == "dataset_mismatch"
    assert built.report.status == {"overall": "incompatible_dataset"}
    assert built.details["compatibility"]["baseline_dataset_id"] == "reasoning-basics-v1"
    assert built.details["compatibility"]["candidate_dataset_id"] == "hallucination-basics-v1"


def test_write_comparison_report_artifacts_persists_summary_and_detail_payloads(tmp_path) -> None:
    adapter_id = "unit-comparison-adapter-write"
    classifier_id = "unit-comparison-classifier-write"
    register_model(adapter_id, ComparisonAdapter)
    register_classifier(classifier_id, ComparisonClassifier())

    baseline_run_id = _write_saved_run(
        tmp_path,
        dataset=FailureDataset(
            dataset_id="reasoning-basics-v1",
            cases=(
                PromptCase(id="case-001", prompt="shared improvement"),
                PromptCase(id="case-002", prompt="shared stable failure"),
            ),
        ),
        model="baseline-model",
        seed=41,
        suffix_minutes=0,
        adapter_id=adapter_id,
        classifier_id=classifier_id,
    )
    candidate_run_id = _write_saved_run(
        tmp_path,
        dataset=FailureDataset(
            dataset_id="reasoning-basics-v1",
            cases=(
                PromptCase(id="case-001", prompt="shared improvement"),
                PromptCase(id="case-002", prompt="shared stable failure"),
            ),
        ),
        model="candidate-model",
        seed=42,
        suffix_minutes=1,
        adapter_id=adapter_id,
        classifier_id=classifier_id,
    )

    built = build_comparison_report(
        load_saved_run_artifacts(baseline_run_id, root=tmp_path),
        load_saved_run_artifacts(candidate_run_id, root=tmp_path),
        now=datetime(2026, 3, 30, 12, 55, 0, tzinfo=timezone.utc),
    )
    assert len(built.report.report_id) < 64
    report_path, details_path = write_comparison_report_artifacts(
        built.report,
        built.details,
        root=tmp_path,
    )

    report_payload = read_json(report_path)
    details_payload = read_json(details_path)

    assert Report.from_payload(report_payload).comparison["baseline_run_id"] == baseline_run_id
    assert report_payload["status"]["overall"] == "improved"
    assert details_payload["comparison_mode"] == "baseline_to_candidate"
    assert details_payload["compatibility"]["shared_case_count"] == 2
    assert details_payload["case_transition_counts"]["improvements"] == 1


def _write_saved_run(
    root,
    *,
    dataset: FailureDataset,
    model: str,
    seed: int,
    suffix_minutes: int,
    adapter_id: str,
    classifier_id: str,
) -> str:
    execution = execute_dataset_run(
        dataset=dataset,
        adapter_id=adapter_id,
        classifier_id=classifier_id,
        model=model,
        run_seed=seed,
        now=datetime(2026, 3, 30, 12, suffix_minutes, 0, tzinfo=timezone.utc),
    )
    write_run_artifacts(execution, root=root)
    return execution.run.run_id
