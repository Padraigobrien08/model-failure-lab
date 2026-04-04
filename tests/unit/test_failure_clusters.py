from __future__ import annotations

from pathlib import Path

from model_failure_lab.clusters import (
    get_failure_cluster_detail,
    list_clusters_for_comparison,
    list_failure_clusters,
)
from model_failure_lab.index import QueryFilters, rebuild_query_index
from model_failure_lab.testing import materialize_insight_fixture


def _comparison_id_for_models(
    workspace,
    *,
    baseline_model: str,
    candidate_model: str,
) -> str:
    return next(
        comparison.report_id
        for comparison in workspace.comparisons
        if comparison.baseline_model == baseline_model
        and comparison.candidate_model == candidate_model
    )


def test_list_failure_clusters_is_deterministic_and_recurring_only(tmp_path: Path) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")

    first = list_failure_clusters(QueryFilters(limit=20), root=workspace.root)
    rebuild_query_index(root=workspace.root)
    second = list_failure_clusters(QueryFilters(limit=20), root=workspace.root)

    assert first
    assert [row.to_payload() for row in first] == [row.to_payload() for row in second]
    assert all(row.scope_count >= 2 for row in first)
    assert any(
        row.cluster_kind == "run_case"
        and row.failure_types == ("hallucination",)
        and row.scope_count >= 3
        for row in first
    )
    assert any(
        row.cluster_kind == "comparison_delta"
        and row.transition_types == ("failure_to_no_failure",)
        for row in first
    )


def test_cluster_detail_exposes_ordered_occurrences_and_evidence(tmp_path: Path) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    summary = next(
        row
        for row in list_failure_clusters(
            QueryFilters(limit=20),
            cluster_kind="comparison_delta",
            root=workspace.root,
        )
        if row.failure_types == ("instruction_following",)
    )

    detail = get_failure_cluster_detail(summary.cluster_id, root=workspace.root, limit=10)

    assert detail.summary.to_payload() == summary.to_payload()
    assert len(detail.occurrences) == summary.occurrence_count == 2
    assert [row.created_at for row in detail.occurrences] == sorted(
        (row.created_at for row in detail.occurrences),
        reverse=True,
    )
    assert {row.report_id for row in detail.occurrences} == {
        _comparison_id_for_models(
            workspace,
            baseline_model="baseline-model",
            candidate_model="candidate-model",
        ),
        _comparison_id_for_models(
            workspace,
            baseline_model="baseline-model",
            candidate_model="stable-model",
        ),
    }
    assert all(row.evidence_ref.kind == "comparison_case" for row in detail.occurrences)
    assert all(row.transition_type == "failure_to_no_failure" for row in detail.occurrences)


def test_list_clusters_for_comparison_returns_recurring_context(tmp_path: Path) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison_id = _comparison_id_for_models(
        workspace,
        baseline_model="baseline-model",
        candidate_model="stable-model",
    )

    clusters = list_clusters_for_comparison(comparison_id, root=workspace.root, limit=5)

    assert clusters
    assert all(cluster.cluster_kind == "comparison_delta" for cluster in clusters)
    assert all(cluster.scope_count >= 2 for cluster in clusters)
    assert all(
        any(reference.report_id == comparison_id for reference in cluster.representative_evidence)
        for cluster in clusters
    )
