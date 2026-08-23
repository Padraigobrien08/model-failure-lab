"""heuristic_v1 declares an honest, tested subset of the failure taxonomy.

The full taxonomy defines eight failure types, but the baseline classifier can only emit
four (plus no_failure). This test pins that declared subset so the gap stays explicit
rather than silently over-claiming coverage across filters and governance.
"""

from __future__ import annotations

from model_failure_lab.adapters import ModelResult
from model_failure_lab.classifiers.contracts import ClassifierExpectations, ClassifierInput
from model_failure_lab.classifiers.heuristic import (
    HEURISTIC_V1_EMITTED_FAILURE_TYPES,
    heuristic_classifier,
)
from model_failure_lab.schemas.taxonomy import FAILURE_TYPES


def test_declared_subset_is_strict_and_documents_the_gap() -> None:
    full = set(FAILURE_TYPES)
    declared = set(HEURISTIC_V1_EMITTED_FAILURE_TYPES)
    assert declared < full  # strict subset
    # The types the baseline classifier cannot produce, called out explicitly.
    assert full - declared == {"retrieval", "safety", "format", "tool_use"}


def _classify(text: str, *, reference: str | None = None) -> str:
    expectations = (
        ClassifierExpectations(reference_answer=reference) if reference is not None else None
    )
    result = heuristic_classifier(
        ClassifierInput(output=ModelResult(text=text), expectations=expectations)
    )
    return result.failure_type


def test_emitted_types_stay_within_the_declared_subset() -> None:
    samples = [
        _classify("the answer is 42"),  # no_failure
        _classify("wrong", reference="the correct answer"),  # reasoning
        _classify("according to a study everything is fine"),  # hallucination
    ]
    for failure_type in samples:
        assert failure_type in HEURISTIC_V1_EMITTED_FAILURE_TYPES
