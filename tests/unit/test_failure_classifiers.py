from __future__ import annotations

import pytest

from model_failure_lab.adapters import ModelResult
from model_failure_lab.classifiers import (
    ClassifierExpectations,
    ClassifierInput,
    ClassifierResult,
    UnknownClassifierError,
    heuristic_classifier,
    register_classifier,
    resolve_classifier,
)


def passthrough_classifier(classifier_input: ClassifierInput) -> ClassifierResult:
    reference = (
        classifier_input.expectations.reference_answer
        if classifier_input.expectations
        else None
    )
    explanation = f"reference={reference}" if reference else "no reference"
    return ClassifierResult(failure_type="no_failure", confidence=0.2, explanation=explanation)


def test_classifier_expectations_accept_string_or_list_rubric() -> None:
    single = ClassifierExpectations.from_payload({"rubric": "Check factuality"})
    multiple = ClassifierExpectations.from_payload(
        {"rubric": ["Check factuality", "Check reasoning"], "constraints": ["cite sources"]}
    )

    assert single.rubric == ("Check factuality",)
    assert multiple.rubric == ("Check factuality", "Check reasoning")
    assert multiple.constraints == ("cite sources",)


def test_classifier_result_round_trips_optional_fields() -> None:
    result = ClassifierResult(
        failure_type="reasoning",
        confidence=0.8,
        explanation="Output contradicts the expected answer.",
    )

    assert ClassifierResult.from_payload(result.to_payload()) == result


def test_register_classifier_resolves_named_callable() -> None:
    register_classifier("unit-test-classifier", passthrough_classifier)

    classifier = resolve_classifier("unit-test-classifier")
    result = classifier(
        ClassifierInput(
            output=ModelResult(text="Answer"),
            expectations=ClassifierExpectations(reference_answer="42"),
        )
    )

    assert result.failure_type == "no_failure"
    assert result.confidence == 0.2
    assert result.explanation == "reference=42"


def test_heuristic_classifier_is_registered_by_default() -> None:
    classifier = resolve_classifier("heuristic_v1")

    assert classifier is heuristic_classifier


def test_heuristic_classifier_flags_reference_mismatch_as_reasoning() -> None:
    result = heuristic_classifier(
        ClassifierInput(
            output=ModelResult(text="The answer is 13."),
            expectations=ClassifierExpectations(reference_answer="42"),
        )
    )

    assert result == ClassifierResult(
        failure_type="reasoning",
        confidence=0.85,
        explanation="Output does not match the reference answer.",
    )


def test_heuristic_classifier_uses_constraints_before_falling_back() -> None:
    result = heuristic_classifier(
        ClassifierInput(
            output=ModelResult(text="This response is brief."),
            expectations=ClassifierExpectations(constraints=("cite sources",)),
        )
    )

    assert result.failure_type == "instruction"
    assert result.confidence == 0.7
    assert result.explanation == "Output misses required constraint: cite sources."


def test_heuristic_classifier_detects_hallucination_markers() -> None:
    result = heuristic_classifier(
        ClassifierInput(output=ModelResult(text="According to a study, this always works."))
    )

    assert result.failure_type == "hallucination"
    assert result.confidence == 0.6
    assert result.explanation == "Output uses unsupported factual framing."


def test_heuristic_classifier_is_pure_and_deterministic() -> None:
    classifier_input = ClassifierInput(
        output=ModelResult(text="A careful answer."),
        expectations=ClassifierExpectations(rubric=("check consistency",)),
    )

    first = heuristic_classifier(classifier_input)
    second = heuristic_classifier(classifier_input)

    assert first == second
    assert first.failure_type == "no_failure"
    assert first.confidence == 0.2


def test_resolve_classifier_rejects_unknown_id() -> None:
    with pytest.raises(UnknownClassifierError, match="unknown classifier"):
        resolve_classifier("missing-classifier")
