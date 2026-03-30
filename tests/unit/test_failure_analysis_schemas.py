from __future__ import annotations

from model_failure_lab.schemas import PromptCase, Report, Result, Run


def test_prompt_case_to_payload_is_json_safe() -> None:
    case = PromptCase(
        id="reasoning_001",
        prompt="Solve the equation.",
        expected_failure="reasoning",
        tags=("multi-step", "algebra"),
        metadata={"source": "demo"},
    )

    assert case.to_payload() == {
        "id": "reasoning_001",
        "prompt": "Solve the equation.",
        "expected_failure": "reasoning",
        "tags": ["multi-step", "algebra"],
        "metadata": {"source": "demo"},
    }


def test_run_to_payload_keeps_execution_metadata() -> None:
    run = Run(
        run_id="run_001",
        model="gpt-4",
        dataset="reasoning.json",
        created_at="2026-03-30T12:00:00Z",
        config={"temperature": 0},
        metadata={"classifier": "heuristic_v1"},
    )

    assert run.to_payload() == {
        "run_id": "run_001",
        "model": "gpt-4",
        "dataset": "reasoning.json",
        "created_at": "2026-03-30T12:00:00Z",
        "config": {"temperature": 0},
        "metadata": {"classifier": "heuristic_v1"},
    }


def test_result_to_payload_includes_optional_analysis_fields() -> None:
    result = Result(
        prompt_id="reasoning_001",
        output="The answer is 7.",
        failure_type="reasoning",
        score=0.8,
        confidence=0.6,
        explanation="Arithmetic step skipped.",
        metadata={"seed": 13},
    )

    assert result.to_payload() == {
        "prompt_id": "reasoning_001",
        "output": "The answer is 7.",
        "failure_type": "reasoning",
        "score": 0.8,
        "confidence": 0.6,
        "explanation": "Arithmetic step skipped.",
        "metadata": {"seed": 13},
    }


def test_report_to_payload_supports_aggregate_metrics() -> None:
    report = Report(
        report_id="report_001",
        run_ids=("run_001",),
        created_at="2026-03-30T12:05:00Z",
        total_cases=20,
        failure_counts={"reasoning": 10, "hallucination": 4},
        failure_rates={"reasoning": 0.5, "hallucination": 0.2},
        metadata={"summary": "demo"},
    )

    assert report.to_payload() == {
        "report_id": "report_001",
        "run_ids": ["run_001"],
        "created_at": "2026-03-30T12:05:00Z",
        "total_cases": 20,
        "failure_counts": {"reasoning": 10, "hallucination": 4},
        "failure_rates": {"reasoning": 0.5, "hallucination": 0.2},
        "metadata": {"summary": "demo"},
    }
