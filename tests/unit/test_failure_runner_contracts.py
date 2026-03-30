from __future__ import annotations

from datetime import datetime, timezone

from model_failure_lab.adapters import ModelMetadata, ModelResult, ModelUsage
from model_failure_lab.classifiers import ClassifierExpectations, ClassifierResult
from model_failure_lab.runner import (
    CaseClassification,
    CaseError,
    CaseExecution,
    CaseExpectationAssessment,
    CaseOutput,
    ExecutionMetadata,
    PromptSnapshot,
    build_run_id,
    derive_case_seed,
)
from model_failure_lab.schemas import (
    FailureLabel,
    PromptCase,
    PromptContextExpectations,
    PromptExpectations,
)


def test_derive_case_seed_is_stable_and_order_independent() -> None:
    first = derive_case_seed(
        run_seed=13,
        dataset_id="reasoning-basics-v1",
        case_id="case-001",
        adapter_id="demo",
    )
    second = derive_case_seed(
        run_seed=13,
        dataset_id="reasoning-basics-v1",
        case_id="case-001",
        adapter_id="demo",
    )
    different = derive_case_seed(
        run_seed=13,
        dataset_id="reasoning-basics-v1",
        case_id="case-002",
        adapter_id="demo",
    )

    assert first == second
    assert first != different


def test_build_run_id_is_readable_and_deterministic_for_fixed_inputs() -> None:
    run_id = build_run_id(
        dataset_id="Reasoning Basics",
        adapter_id="demo",
        classifier_id="heuristic_v1",
        model="demo-model",
        run_seed=13,
        run_config={"temperature": 0.1},
        now=datetime(2026, 3, 30, 11, 15, 0, tzinfo=timezone.utc),
    )

    assert (
        run_id
        == "20260330_111500_000000_reasoning_basics_demo_heuristic_v1_demo_model_seed_13_426a6d0f"
    )


def test_build_run_id_changes_for_model_and_config_variants_under_same_time() -> None:
    current_time = datetime(2026, 3, 30, 11, 15, 0, tzinfo=timezone.utc)

    base = build_run_id(
        dataset_id="Reasoning Basics",
        adapter_id="demo",
        classifier_id="heuristic_v1",
        model="demo-model",
        run_seed=13,
        run_config={"temperature": 0.1},
        now=current_time,
    )
    different_model = build_run_id(
        dataset_id="Reasoning Basics",
        adapter_id="demo",
        classifier_id="heuristic_v1",
        model="demo-model-v2",
        run_seed=13,
        run_config={"temperature": 0.1},
        now=current_time,
    )
    different_config = build_run_id(
        dataset_id="Reasoning Basics",
        adapter_id="demo",
        classifier_id="heuristic_v1",
        model="demo-model",
        run_seed=13,
        run_config={"temperature": 0.2},
        now=current_time,
    )

    assert base != different_model
    assert base != different_config


def test_prompt_snapshot_extracts_authored_expectations_from_prompt_case() -> None:
    snapshot = PromptSnapshot.from_prompt_case(
        PromptCase(
            id="case-001",
            prompt="What is the answer?",
            tags=("core", "numerical"),
            expectations=PromptExpectations(
                expected_failure="reasoning",
                reference_answer="42",
                rubric=("show reasoning",),
                constraints=("be concise",),
                context=PromptContextExpectations(
                    context="Math worksheet",
                    evidence_items=("2 + 2",),
                ),
            ),
        )
    )

    assert snapshot == PromptSnapshot(
        id="case-001",
        prompt="What is the answer?",
        tags=("core", "numerical"),
        expectations=PromptExpectations(
            expected_failure="reasoning",
            reference_answer="42",
            rubric=("show reasoning",),
            constraints=("be concise",),
            context=PromptContextExpectations(
                context="Math worksheet",
                evidence_items=("2 + 2",),
            ),
        ),
    )
    assert snapshot.to_classifier_expectations() == ClassifierExpectations(
        reference_answer="42",
        rubric=("show reasoning",),
        constraints=("be concise",),
        context="Math worksheet",
        evidence_items=("2 + 2",),
    )
    assert snapshot.expected_failure_label() == FailureLabel("reasoning")


def test_case_execution_round_trips_with_compact_sections() -> None:
    model_result = ModelResult(
        text="The answer is 42.",
        metadata=ModelMetadata(
            model="gpt-4.1-mini",
            latency_ms=120.0,
            usage=ModelUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        ),
    )
    execution = ExecutionMetadata.from_model_result(
        adapter_id="openai",
        classifier_id="heuristic_v1",
        run_seed=13,
        case_seed=99,
        result=model_result,
    )
    record = CaseExecution(
        case_id="case-001",
        prompt=PromptSnapshot(
            id="case-001",
            prompt="What is the answer?",
            tags=("core",),
            expectations=PromptExpectations(
                expected_failure="no_failure",
                reference_answer="42",
            ),
        ),
        execution=execution,
        output=CaseOutput.from_model_result(model_result),
        classification=CaseClassification.from_classifier_result(
            ClassifierResult(
                failure_type="no_failure",
                confidence=0.2,
                explanation="No heuristic failure signal detected.",
            )
        ),
    )

    assert CaseExecution.from_payload(record.to_payload()) == record
    assert record.expectation == CaseExpectationAssessment(
        expected_failure=FailureLabel("no_failure"),
        observed_failure=FailureLabel("no_failure"),
        expectation_verdict="no_failure_as_expected",
    )


def test_case_execution_derives_expectation_verdicts_directionally() -> None:
    record = CaseExecution(
        case_id="case-001",
        prompt=PromptSnapshot(
            id="case-001",
            prompt="What is the answer?",
            tags=("core",),
            expectations=PromptExpectations(expected_failure="reasoning"),
        ),
        execution=ExecutionMetadata(
            adapter_id="demo",
            model="demo-model",
            classifier_id="heuristic_v1",
            run_seed=13,
            case_seed=99,
        ),
        output=CaseOutput(text="According to a study, the answer is blue."),
        classification=CaseClassification(
            failure_type="hallucination",
            confidence=0.6,
        ),
    )

    assert record.expectation == CaseExpectationAssessment(
        expected_failure=FailureLabel("reasoning"),
        observed_failure=FailureLabel("hallucination"),
        expectation_verdict="unexpected_failure",
    )


def test_case_error_from_exception_captures_stage_type_and_message() -> None:
    error = CaseError.from_exception(stage="model_invoke", exc=TimeoutError("Request timed out"))

    assert error.to_payload() == {
        "stage": "model_invoke",
        "type": "TimeoutError",
        "message": "Request timed out",
    }
