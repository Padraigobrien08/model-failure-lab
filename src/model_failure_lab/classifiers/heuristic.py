"""Baseline deterministic heuristic classifier."""

from __future__ import annotations

import re

from .contracts import ClassifierInput, ClassifierResult

_HALLUCINATION_MARKERS = (
    "according to a study",
    "research shows",
    "experts agree",
    "wikipedia says",
)


def heuristic_classifier(classifier_input: ClassifierInput) -> ClassifierResult:
    """Assign one baseline failure label using deterministic authored rules."""

    output_text = _normalize_text(classifier_input.output.text)
    expectations = classifier_input.expectations

    if expectations and expectations.reference_answer:
        reference = _normalize_text(expectations.reference_answer)
        if reference and reference not in output_text:
            return ClassifierResult(
                failure_type="reasoning",
                confidence=0.85,
                explanation="Output does not match the reference answer.",
            )

    if expectations and expectations.constraints:
        missing_constraints = [
            constraint
            for constraint in expectations.constraints
            if _normalize_text(constraint) not in output_text
        ]
        if missing_constraints:
            missing = missing_constraints[0]
            return ClassifierResult(
                failure_type="instruction",
                confidence=0.7,
                explanation=f"Output misses required constraint: {missing}.",
            )

    if any(marker in output_text for marker in _HALLUCINATION_MARKERS):
        return ClassifierResult(
            failure_type="hallucination",
            confidence=0.6,
            explanation="Output uses unsupported factual framing.",
        )

    if expectations and expectations.rubric:
        explanation = (
            "No heuristic failure signal detected under rubric: "
            f"{expectations.rubric[0]}."
        )
        return ClassifierResult(
            failure_type="no_failure",
            confidence=0.2,
            explanation=explanation,
        )

    return ClassifierResult(
        failure_type="no_failure",
        confidence=0.1,
        explanation="No heuristic failure signal detected.",
    )


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())
