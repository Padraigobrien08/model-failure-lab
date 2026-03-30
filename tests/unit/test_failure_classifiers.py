from __future__ import annotations

import pytest

from model_failure_lab.adapters import ModelResult
from model_failure_lab.classifiers import (
    ClassifierExpectations,
    ClassifierInput,
    ClassifierResult,
    UnknownClassifierError,
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


def test_resolve_classifier_rejects_unknown_id() -> None:
    with pytest.raises(UnknownClassifierError, match="unknown classifier"):
        resolve_classifier("missing-classifier")
