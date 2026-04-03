from __future__ import annotations

from model_failure_lab.index import (
    QueryFilters,
    artifact_overview_summary,
    list_comparison_inventory,
    list_run_inventory,
    query_case_deltas,
    query_cases,
)
from model_failure_lab.testing import materialize_insight_fixture


def test_materialize_insight_fixture_creates_queryable_workspace(tmp_path) -> None:
    summary = materialize_insight_fixture(tmp_path)

    assert summary.dataset_id == "insight-fixture-v1"
    assert summary.dataset_path.exists()
    assert summary.query_index.path.exists()
    assert len(summary.runs) == 4
    assert len(summary.comparisons) == 3

    overview = artifact_overview_summary(root=tmp_path)
    assert overview == {
        "run_count": 4,
        "comparison_count": 3,
        "case_count": 18,
        "delta_count": 16,
    }

    run_inventory = list_run_inventory(root=tmp_path)
    assert [row["model"] for row in run_inventory] == [
        "stable-model",
        "noisy-model",
        "candidate-model",
        "baseline-model",
    ]

    comparison_inventory = list_comparison_inventory(root=tmp_path)
    assert len(comparison_inventory) == 3

    hallucinations = query_cases(
        QueryFilters(failure_type="hallucination", limit=50),
        root=tmp_path,
    )
    assert len(hallucinations) == 8
    assert any(row["model"] == "candidate-model" for row in hallucinations)
    assert any(row["model"] == "noisy-model" for row in hallucinations)

    regressions = query_case_deltas(
        QueryFilters(delta="regression", limit=50),
        root=tmp_path,
    )
    improvements = query_case_deltas(
        QueryFilters(delta="improvement", limit=50),
        root=tmp_path,
    )
    swaps = query_case_deltas(
        QueryFilters(delta="swap", limit=50),
        root=tmp_path,
    )

    assert len(regressions) == 5
    assert len(improvements) == 9
    assert len(swaps) == 2
    assert any(row["report_id"] == summary.comparisons[0].report_id for row in regressions)


def test_materialize_insight_fixture_can_reuse_existing_workspace(tmp_path) -> None:
    first = materialize_insight_fixture(tmp_path)
    second = materialize_insight_fixture(tmp_path, reuse_existing=True)

    assert first.dataset_path == second.dataset_path
    assert [run.run_id for run in first.runs] == [run.run_id for run in second.runs]
    assert [comparison.report_id for comparison in first.comparisons] == [
        comparison.report_id for comparison in second.comparisons
    ]
