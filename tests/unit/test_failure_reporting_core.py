from __future__ import annotations

from datetime import datetime, timezone

from model_failure_lab.adapters import ModelMetadata, ModelRequest, ModelResult, register_model
from model_failure_lab.classifiers import ClassifierInput, ClassifierResult, register_classifier
from model_failure_lab.datasets import FailureDataset
from model_failure_lab.reporting.artifacts import write_report_artifacts
from model_failure_lab.reporting.core import build_run_report
from model_failure_lab.reporting.load import load_saved_run_artifacts
from model_failure_lab.runner import execute_dataset_run, write_run_artifacts
from model_failure_lab.schemas import PromptCase, Report
from model_failure_lab.storage import read_json


class ReportingTestAdapter:
    def generate(self, request: ModelRequest) -> ModelResult:
        prompt = request.prompt.lower()
        if "model fail" in prompt:
            raise TimeoutError("Request timed out")
        return ModelResult(
            text=f"model:{request.model}::{request.prompt}",
            metadata=ModelMetadata(model=request.model, latency_ms=12.0),
        )


class ReportingTestClassifier:
    def __call__(self, classifier_input: ClassifierInput) -> ClassifierResult:
        output_text = classifier_input.output.text.lower()
        if "trigger unclassified" in output_text:
            raise ValueError("Classification unavailable")
        if "hallucination" in output_text:
            return ClassifierResult(
                failure_type="hallucination",
                confidence=0.8,
                explanation="Unsupported factual framing detected.",
            )
        return ClassifierResult(
            failure_type="no_failure",
            confidence=0.2,
            explanation="No heuristic failure signal detected.",
        )


def test_build_run_report_uses_classified_cases_as_failure_denominator(tmp_path) -> None:
    register_model("unit-reporting-adapter", ReportingTestAdapter)
    register_classifier("unit-reporting-classifier", ReportingTestClassifier())

    dataset = FailureDataset(
        dataset_id="reasoning-basics-v1",
        cases=(
            PromptCase(id="case-001", prompt="clean success"),
            PromptCase(id="case-002", prompt="hallucination case"),
            PromptCase(id="case-003", prompt="model fail case"),
            PromptCase(id="case-004", prompt="trigger unclassified case"),
        ),
    )
    execution = execute_dataset_run(
        dataset=dataset,
        adapter_id="unit-reporting-adapter",
        classifier_id="unit-reporting-classifier",
        model="reporting-model",
        run_seed=11,
        now=datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc),
    )
    write_run_artifacts(execution, root=tmp_path)

    saved_run = load_saved_run_artifacts(execution.run.run_id, root=tmp_path)
    built = build_run_report(saved_run, now=datetime(2026, 3, 30, 12, 5, 0, tzinfo=timezone.utc))

    assert built.report.report_id == f"{execution.run.run_id}_report"
    assert built.report.failure_counts == {"hallucination": 1}
    assert built.report.failure_rates == {"hallucination": 0.5}
    assert built.report.metrics["attempted_case_count"] == 4
    assert built.report.metrics["classified_case_count"] == 2
    assert built.report.metrics["execution_error_count"] == 1
    assert built.report.metrics["unclassified_count"] == 1
    assert built.report.metrics["classification_coverage"] == 0.5
    assert built.report.metrics["execution_success_rate"] == 0.75
    assert built.report.status == {"overall": "completed_with_errors"}
    assert built.details["failure_type_breakdown"] == [
        {
            "failure_type": "hallucination",
            "count": 1,
            "rate": 0.5,
            "case_ids": ["case-002"],
        }
    ]
    assert built.details["execution_errors"] == [
        {
            "case_id": "case-003",
            "stage": "model_invoke",
            "type": "TimeoutError",
            "message": "Request timed out",
        }
    ]
    assert built.details["unclassified_cases"] == [
        {
            "case_id": "case-004",
            "stage": "classify",
            "type": "ValueError",
            "message": "Classification unavailable",
        }
    ]


def test_write_report_artifacts_persists_summary_and_detail_payloads(tmp_path) -> None:
    register_model("unit-reporting-adapter-write", ReportingTestAdapter)
    register_classifier("unit-reporting-classifier-write", ReportingTestClassifier())

    dataset = FailureDataset(
        dataset_id="reasoning-basics-v1",
        cases=(PromptCase(id="case-001", prompt="hallucination case"),),
    )
    execution = execute_dataset_run(
        dataset=dataset,
        adapter_id="unit-reporting-adapter-write",
        classifier_id="unit-reporting-classifier-write",
        model="reporting-model",
        run_seed=12,
        now=datetime(2026, 3, 30, 12, 15, 0, tzinfo=timezone.utc),
    )
    write_run_artifacts(execution, root=tmp_path)

    built = build_run_report(
        load_saved_run_artifacts(execution.run.run_id, root=tmp_path),
        now=datetime(2026, 3, 30, 12, 20, 0, tzinfo=timezone.utc),
    )
    report_path, details_path = write_report_artifacts(built.report, built.details, root=tmp_path)

    report_payload = read_json(report_path)
    details_payload = read_json(details_path)

    assert Report.from_payload(report_payload).report_id == built.report.report_id
    assert report_payload["metadata"]["detail_artifact"] == "report_details.json"
    assert details_payload["report_kind"] == "single_run"
    assert details_payload["source_run_id"] == execution.run.run_id
    assert details_payload["notable_cases"] == [
        {
            "case_id": "case-001",
            "failure_type": "hallucination",
            "confidence": 0.8,
            "explanation": "Unsupported factual framing detected.",
        }
    ]
