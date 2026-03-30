from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from model_failure_lab.adapters import ModelMetadata, ModelRequest, ModelResult, register_model
from model_failure_lab.classifiers import ClassifierInput, ClassifierResult, register_classifier
from model_failure_lab.datasets import FailureDataset
from model_failure_lab.runner import execute_dataset_run, write_run_artifacts
from model_failure_lab.schemas import PromptCase, Run
from model_failure_lab.storage import read_json


class SelectiveFailAdapter:
    def generate(self, request: ModelRequest) -> ModelResult:
        if "fail invoke" in request.prompt.lower():
            raise TimeoutError("Request timed out")
        return ModelResult(
            text=f"adapter:{request.prompt}",
            metadata=ModelMetadata(model=request.model, latency_ms=25.0),
        )


class PassThroughClassifier:
    def __call__(self, classifier_input: ClassifierInput) -> ClassifierResult:
        if "fail classify" in classifier_input.output.text.lower():
            raise ValueError("Classifier exploded")
        return ClassifierResult(
            failure_type="no_failure",
            confidence=0.2,
            explanation="No heuristic failure signal detected.",
        )


def test_execute_dataset_run_completes_successfully_with_builtins() -> None:
    dataset = FailureDataset(
        dataset_id="reasoning-basics-v1",
        name="Reasoning Basics",
        cases=(PromptCase(id="case-001", prompt="Explain why 2 + 2 = 4."),),
    )

    run_execution = execute_dataset_run(
        dataset=dataset,
        adapter_id="demo",
        classifier_id="heuristic_v1",
        model="demo-model",
        run_seed=13,
        now=datetime(2026, 3, 30, 11, 30, 0, tzinfo=timezone.utc),
    )

    assert run_execution.status == "completed"
    assert run_execution.total_cases == 1
    assert run_execution.error_count == 0
    assert Run.from_payload(run_execution.run.to_payload()) == run_execution.run
    assert run_execution.case_results[0].output is not None
    assert run_execution.case_results[0].classification is not None
    assert run_execution.case_results[0].error is None


def test_execute_dataset_run_records_model_invoke_errors_per_case() -> None:
    register_model("unit-selective-fail-adapter", SelectiveFailAdapter)
    register_classifier("unit-pass-through-classifier", PassThroughClassifier())

    dataset = FailureDataset(
        dataset_id="reasoning-basics-v1",
        cases=(
            PromptCase(id="case-001", prompt="This succeeds."),
            PromptCase(id="case-002", prompt="Please fail invoke."),
        ),
    )

    run_execution = execute_dataset_run(
        dataset=dataset,
        adapter_id="unit-selective-fail-adapter",
        classifier_id="unit-pass-through-classifier",
        model="demo-model",
        run_seed=13,
    )

    assert run_execution.status == "completed_with_errors"
    assert run_execution.error_count == 1
    assert run_execution.case_results[0].error is None
    assert run_execution.case_results[1].error is not None
    assert run_execution.case_results[1].error.stage == "model_invoke"
    assert run_execution.case_results[1].classification is None


def test_execute_dataset_run_records_classifier_errors_per_case() -> None:
    register_model("unit-success-adapter", SelectiveFailAdapter)
    register_classifier("unit-failing-classifier", PassThroughClassifier())

    dataset = FailureDataset(
        dataset_id="reasoning-basics-v1",
        cases=(PromptCase(id="case-003", prompt="Please fail classify."),),
    )

    run_execution = execute_dataset_run(
        dataset=dataset,
        adapter_id="unit-success-adapter",
        classifier_id="unit-failing-classifier",
        model="demo-model",
        run_seed=99,
    )

    assert run_execution.status == "completed_with_errors"
    assert run_execution.case_results[0].output is not None
    assert run_execution.case_results[0].classification is None
    assert run_execution.case_results[0].error is not None
    assert run_execution.case_results[0].error.stage == "classify"


def test_write_run_artifacts_persists_run_and_results_payloads(tmp_path) -> None:
    dataset = FailureDataset(
        dataset_id="reasoning-basics-v1",
        cases=(PromptCase(id="case-001", prompt="Explain why 2 + 2 = 4."),),
    )
    run_execution = execute_dataset_run(
        dataset=dataset,
        adapter_id="demo",
        classifier_id="heuristic_v1",
        model="demo-model",
        run_seed=13,
        now=datetime(2026, 3, 30, 11, 45, 0, tzinfo=timezone.utc),
    )

    run_path, results_path = write_run_artifacts(run_execution, root=tmp_path)

    run_payload = read_json(run_path)
    results_payload = read_json(results_path)

    assert run_payload["run_id"] == run_execution.run.run_id
    assert run_payload["metadata"]["status"] == "completed"
    assert results_payload["run_id"] == run_execution.run.run_id
    assert results_payload["status"] == "completed"
    assert results_payload["total_cases"] == 1
    assert results_payload["cases"][0]["prompt"]["id"] == "case-001"
    assert results_payload["cases"][0]["execution"]["run_seed"] == 13


def test_write_run_artifacts_fails_fast_on_existing_artifact_paths(tmp_path) -> None:
    dataset = FailureDataset(
        dataset_id="reasoning-basics-v1",
        cases=(PromptCase(id="case-001", prompt="Explain why 2 + 2 = 4."),),
    )
    original_execution = execute_dataset_run(
        dataset=dataset,
        adapter_id="demo",
        classifier_id="heuristic_v1",
        model="demo-model",
        run_seed=13,
        now=datetime(2026, 3, 30, 11, 45, 0, tzinfo=timezone.utc),
    )
    run_path, _ = write_run_artifacts(original_execution, root=tmp_path)

    preserved_payload = read_json(run_path)
    preserved_payload["model"] = "preserved-model"
    run_path.write_text(
        json.dumps(preserved_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    colliding_execution = replace(
        original_execution,
        run=replace(original_execution.run, model="replacement-model"),
    )

    with pytest.raises(FileExistsError, match="run artifacts already exist"):
        write_run_artifacts(colliding_execution, root=tmp_path)

    assert read_json(run_path)["model"] == "preserved-model"


def test_execute_dataset_run_uses_model_and_config_in_run_identity() -> None:
    dataset = FailureDataset(
        dataset_id="reasoning-basics-v1",
        cases=(PromptCase(id="case-001", prompt="Explain why 2 + 2 = 4."),),
    )
    current_time = datetime(2026, 3, 30, 11, 46, 0, tzinfo=timezone.utc)

    baseline = execute_dataset_run(
        dataset=dataset,
        adapter_id="demo",
        classifier_id="heuristic_v1",
        model="demo-model",
        run_seed=13,
        run_config={"temperature": 0.1},
        now=current_time,
    )
    different_model = execute_dataset_run(
        dataset=dataset,
        adapter_id="demo",
        classifier_id="heuristic_v1",
        model="demo-model-v2",
        run_seed=13,
        run_config={"temperature": 0.1},
        now=current_time,
    )
    different_config = execute_dataset_run(
        dataset=dataset,
        adapter_id="demo",
        classifier_id="heuristic_v1",
        model="demo-model",
        run_seed=13,
        run_config={"temperature": 0.2},
        now=current_time,
    )

    assert baseline.run.run_id != different_model.run.run_id
    assert baseline.run.run_id != different_config.run.run_id
