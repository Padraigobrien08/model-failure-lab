from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone

import pytest

import model_failure_lab.adapters.anthropic_adapter as anthropic_adapter_module
import model_failure_lab.adapters.ollama_adapter as ollama_adapter_module
from model_failure_lab.adapters import ModelMetadata, ModelRequest, ModelResult, register_model
from model_failure_lab.classifiers import ClassifierInput, ClassifierResult, register_classifier
from model_failure_lab.datasets import FailureDataset
from model_failure_lab.runner import execute_dataset_run, write_run_artifacts
from model_failure_lab.schemas import PromptCase, PromptExpectations, Run
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
        cases=(
            PromptCase(
                id="case-001",
                prompt="Explain why 2 + 2 = 4.",
                tags=("core", "numerical"),
                expectations=PromptExpectations(expected_failure="no_failure"),
            ),
        ),
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
    assert run_execution.case_results[0].expectation.expectation_verdict == "no_failure_as_expected"


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
        cases=(
            PromptCase(
                id="case-001",
                prompt="Explain why 2 + 2 = 4.",
                tags=("core", "numerical"),
                expectations=PromptExpectations(expected_failure="no_failure"),
            ),
        ),
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
    assert results_payload["cases"][0]["prompt"]["tags"] == ["core", "numerical"]
    assert results_payload["cases"][0]["execution"]["run_seed"] == 13
    assert results_payload["cases"][0]["expectation"] == {
        "expected_failure": {"failure_type": "no_failure"},
        "observed_failure": {"failure_type": "no_failure"},
        "expectation_verdict": "no_failure_as_expected",
    }


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


def test_execute_dataset_run_persists_builtin_ollama_artifacts(tmp_path, monkeypatch) -> None:
    register_classifier("unit-ollama-pass-through-classifier", PassThroughClassifier())
    ollama_calls: list[dict[str, object]] = []

    def fake_post_json(base_url: str, payload: dict[str, object], timeout_seconds: float | None):
        ollama_calls.append(
            {
                "base_url": base_url,
                "payload": dict(payload),
                "timeout_seconds": timeout_seconds,
            }
        )
        return {
            "model": str(payload["model"]),
            "response": f"ollama:{payload['model']}::{payload['prompt']}",
            "done": True,
            "prompt_eval_count": 6,
            "eval_count": 4,
        }

    monkeypatch.setattr(ollama_adapter_module, "_post_json", fake_post_json)

    dataset = FailureDataset(
        dataset_id="reasoning-basics-v1",
        cases=(PromptCase(id="case-001", prompt="Explain why 2 + 2 = 4."),),
    )
    run_execution = execute_dataset_run(
        dataset=dataset,
        adapter_id="ollama",
        classifier_id="unit-ollama-pass-through-classifier",
        model="llama3.2",
        run_seed=13,
        run_config={
            "system_prompt": "Be concise.",
            "model_options": {
                "temperature": 0,
                "base_url": "http://127.0.0.1:11434",
                "timeout_seconds": 3,
            },
        },
        now=datetime(2026, 4, 3, 7, 25, 0, tzinfo=timezone.utc),
    )

    run_path, results_path = write_run_artifacts(run_execution, root=tmp_path)
    run_payload = read_json(run_path)
    results_payload = read_json(results_path)

    assert run_execution.adapter_id == "ollama"
    assert run_execution.status == "completed"
    assert ollama_calls == [
        {
            "base_url": "http://127.0.0.1:11434",
            "payload": {
                "model": "llama3.2",
                "prompt": "Explain why 2 + 2 = 4.",
                "system": "Be concise.",
                "stream": False,
                "options": {
                    "temperature": 0,
                    "seed": run_execution.case_results[0].execution.case_seed,
                },
            },
            "timeout_seconds": 3.0,
        }
    ]
    assert run_payload["metadata"]["adapter_id"] == "ollama"
    assert results_payload["cases"][0]["execution"]["adapter_id"] == "ollama"
    assert results_payload["cases"][0]["execution"]["model"] == "llama3.2"
    assert results_payload["cases"][0]["execution"]["usage"] == {
        "prompt_tokens": 6,
        "completion_tokens": 4,
        "total_tokens": 10,
    }
    assert results_payload["cases"][0]["output"] == {
        "text": "ollama:llama3.2::Explain why 2 + 2 = 4."
    }


def test_execute_dataset_run_persists_builtin_anthropic_artifacts(tmp_path, monkeypatch) -> None:
    register_classifier("unit-anthropic-pass-through-classifier", PassThroughClassifier())
    anthropic_base_urls: list[str | None] = []
    anthropic_calls: list[dict[str, object]] = []

    class FakeAnthropicMessagesAPI:
        def create(self, **kwargs: object) -> dict[str, object]:
            anthropic_calls.append(dict(kwargs))
            return {
                "id": "msg_123",
                "type": "message",
                "role": "assistant",
                "model": str(kwargs["model"]),
                "content": [
                    {
                        "type": "text",
                        "text": f"anthropic:{kwargs['model']}::{kwargs['messages'][0]['content']}",
                    }
                ],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 6, "output_tokens": 4},
            }

    class FakeAnthropicClient:
        def __init__(self) -> None:
            self.messages = FakeAnthropicMessagesAPI()

    def fake_client_factory(base_url: str | None):
        anthropic_base_urls.append(base_url)
        return FakeAnthropicClient()

    monkeypatch.setattr(anthropic_adapter_module, "_default_client_factory", fake_client_factory)

    dataset = FailureDataset(
        dataset_id="reasoning-basics-v1",
        cases=(PromptCase(id="case-001", prompt="Explain why 2 + 2 = 4."),),
    )
    run_execution = execute_dataset_run(
        dataset=dataset,
        adapter_id="anthropic",
        classifier_id="unit-anthropic-pass-through-classifier",
        model="claude-sonnet-4-0",
        run_seed=13,
        run_config={
            "system_prompt": "Be concise.",
            "model_options": {
                "max_tokens": 256,
                "temperature": 0,
                "base_url": "http://127.0.0.1:8000",
            },
        },
        now=datetime(2026, 4, 3, 11, 45, 0, tzinfo=timezone.utc),
    )

    run_path, results_path = write_run_artifacts(run_execution, root=tmp_path)
    run_payload = read_json(run_path)
    results_payload = read_json(results_path)

    assert run_execution.adapter_id == "anthropic"
    assert run_execution.status == "completed"
    assert anthropic_base_urls == ["http://127.0.0.1:8000"]
    assert anthropic_calls == [
        {
            "model": "claude-sonnet-4-0",
            "messages": [{"role": "user", "content": "Explain why 2 + 2 = 4."}],
            "system": "Be concise.",
            "max_tokens": 256,
            "temperature": 0,
        }
    ]
    assert run_payload["metadata"]["adapter_id"] == "anthropic"
    assert results_payload["cases"][0]["execution"]["adapter_id"] == "anthropic"
    assert results_payload["cases"][0]["execution"]["model"] == "claude-sonnet-4-0"
    assert results_payload["cases"][0]["execution"]["usage"] == {
        "prompt_tokens": 6,
        "completion_tokens": 4,
        "total_tokens": 10,
    }
    assert results_payload["cases"][0]["output"] == {
        "text": "anthropic:claude-sonnet-4-0::Explain why 2 + 2 = 4."
    }
