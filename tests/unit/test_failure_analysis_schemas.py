from __future__ import annotations

import pytest

from model_failure_lab.schemas import PayloadValidationError, PromptCase, Report, Result, Run
from model_failure_lab.storage import report_details_file


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


def test_report_to_payload_supports_structured_summary_sections() -> None:
    report = Report(
        report_id="report_002",
        run_ids=("run_a", "run_b"),
        created_at="2026-03-30T12:10:00Z",
        total_cases=10,
        failure_counts={"reasoning": 1},
        failure_rates={"reasoning": 0.1},
        comparison={"baseline_run_id": "run_a", "candidate_run_id": "run_b"},
        metrics={"classification_coverage": 0.9},
        status={"overall": "improved"},
    )

    assert report.to_payload() == {
        "report_id": "report_002",
        "run_ids": ["run_a", "run_b"],
        "created_at": "2026-03-30T12:10:00Z",
        "total_cases": 10,
        "failure_counts": {"reasoning": 1},
        "failure_rates": {"reasoning": 0.1},
        "comparison": {"baseline_run_id": "run_a", "candidate_run_id": "run_b"},
        "metrics": {"classification_coverage": 0.9},
        "status": {"overall": "improved"},
    }


def test_prompt_case_from_payload_round_trips() -> None:
    payload = {
        "id": "reasoning_001",
        "prompt": "Solve the equation.",
        "expected_failure": "reasoning",
        "tags": ["multi-step", "algebra"],
        "metadata": {"source": "demo"},
    }

    assert PromptCase.from_payload(payload).to_payload() == payload


def test_run_from_payload_round_trips() -> None:
    payload = {
        "run_id": "run_001",
        "model": "gpt-4",
        "dataset": "reasoning.json",
        "created_at": "2026-03-30T12:00:00Z",
        "config": {"temperature": 0},
        "metadata": {"classifier": "heuristic_v1"},
    }

    assert Run.from_payload(payload).to_payload() == payload


def test_result_from_payload_round_trips() -> None:
    payload = {
        "prompt_id": "reasoning_001",
        "output": "The answer is 7.",
        "failure_type": "reasoning",
        "score": 0.8,
        "confidence": 0.6,
        "explanation": "Arithmetic step skipped.",
        "metadata": {"seed": 13},
    }

    assert Result.from_payload(payload).to_payload() == payload


def test_report_from_payload_round_trips() -> None:
    payload = {
        "report_id": "report_001",
        "run_ids": ["run_001"],
        "created_at": "2026-03-30T12:05:00Z",
        "total_cases": 20,
        "failure_counts": {"reasoning": 10, "hallucination": 4},
        "failure_rates": {"reasoning": 0.5, "hallucination": 0.2},
        "metadata": {"summary": "demo"},
    }

    assert Report.from_payload(payload).to_payload() == payload


def test_report_from_payload_round_trips_with_structured_sections() -> None:
    payload = {
        "report_id": "report_002",
        "run_ids": ["run_a", "run_b"],
        "created_at": "2026-03-30T12:10:00Z",
        "total_cases": 10,
        "failure_counts": {"reasoning": 1},
        "failure_rates": {"reasoning": 0.1},
        "comparison": {"baseline_run_id": "run_a", "candidate_run_id": "run_b"},
        "metrics": {"classification_coverage": 0.9},
        "status": {"overall": "improved"},
    }

    assert Report.from_payload(payload).to_payload() == payload


def test_prompt_case_from_payload_rejects_missing_required_fields() -> None:
    with pytest.raises(PayloadValidationError, match="prompt must be a non-empty string"):
        PromptCase.from_payload({"id": "reasoning_001", "prompt": ""})


def test_report_from_payload_rejects_non_numeric_rates() -> None:
    payload = {
        "report_id": "report_001",
        "run_ids": ["run_001"],
        "created_at": "2026-03-30T12:05:00Z",
        "total_cases": 20,
        "failure_counts": {"reasoning": 10},
        "failure_rates": {"reasoning": "high"},
    }

    with pytest.raises(PayloadValidationError, match="failure_rates"):
        Report.from_payload(payload)


def test_report_details_file_uses_report_directory(tmp_path) -> None:
    path = report_details_file("Report 001", root=tmp_path, create=True)

    assert path == tmp_path / "reports" / "report_001" / "report_details.json"
