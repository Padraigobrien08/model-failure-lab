from __future__ import annotations

import json
from pathlib import Path

from model_failure_lab.cli import main
from model_failure_lab.datasets import evolve_dataset_family, list_dataset_versions
from model_failure_lab.governance import GovernancePolicy, recommend_dataset_action
from model_failure_lab.history import query_history_snapshot
from model_failure_lab.index import QueryFilters, query_comparison_signals
from model_failure_lab.testing import materialize_insight_fixture
from model_failure_lab.testing.insight_fixture import (
    FIXTURE_ADAPTER_ID,
    FIXTURE_CLASSIFIER_ID,
)


def _run_id_for_model(workspace, model: str) -> str:
    return next(run.run_id for run in workspace.runs if run.model == model)


def _report_id_for_regression(root: Path) -> str:
    rows = query_comparison_signals(QueryFilters(limit=20), verdict="regression", root=root)
    return str(rows[0]["report_id"])


def _create_regression_comparison(
    workspace,
    *,
    baseline_model: str,
    candidate_model: str,
) -> str:
    baseline_run_id = _run_id_for_model(workspace, baseline_model)
    candidate_run_id = _run_id_for_model(workspace, candidate_model)
    exit_code = main(
        [
            "compare",
            baseline_run_id,
            candidate_run_id,
            "--root",
            str(workspace.root),
        ]
    )
    assert exit_code == 0
    rows = query_comparison_signals(QueryFilters(limit=20), verdict="regression", root=workspace.root)
    matching = [
        row
        for row in rows
        if row["baseline_run_id"] == baseline_run_id and row["candidate_run_id"] == candidate_run_id
    ]
    assert matching
    return str(matching[0]["report_id"])


def _run_versioned_dataset(workspace_root: Path, dataset_id: str, model: str) -> None:
    exit_code = main(
        [
            "run",
            "--dataset",
            dataset_id,
            "--model",
            f"{FIXTURE_ADAPTER_ID}:{model}",
            "--classifier",
            FIXTURE_CLASSIFIER_ID,
            "--root",
            str(workspace_root),
        ]
    )
    assert exit_code == 0


def test_query_history_snapshot_returns_ordered_dataset_history(tmp_path: Path) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")

    snapshot = query_history_snapshot(
        dataset=workspace.dataset_id,
        root=workspace.root,
        limit=10,
    )

    assert snapshot.scope_kind == "dataset"
    assert snapshot.scope_value == workspace.dataset_id
    assert len(snapshot.run_history) == len(workspace.runs)
    assert len(snapshot.comparison_history) == len(workspace.comparisons)
    assert [row.created_at for row in snapshot.run_history] == sorted(
        row.created_at for row in snapshot.run_history
    )
    assert [row.created_at for row in snapshot.comparison_history] == sorted(
        row.created_at for row in snapshot.comparison_history
    )
    assert snapshot.run_trend is not None
    assert snapshot.run_trend.label != "insufficient_history"
    assert snapshot.comparison_trend is not None
    assert snapshot.comparison_trend.label != "insufficient_history"
    assert snapshot.recurring_clusters
    assert snapshot.recurring_clusters[0].scope_count >= 2


def test_history_aware_governance_can_override_low_severity_ignore(tmp_path: Path) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison_id = _create_regression_comparison(
        workspace,
        baseline_model="stable-model",
        candidate_model="candidate-model",
    )

    recommendation = recommend_dataset_action(
        comparison_id,
        root=workspace.root,
        policy=GovernancePolicy(
            minimum_severity=1.0,
            recurrence_window=10,
            recurrence_threshold=2,
            max_duplicate_ratio=None,
        ),
    )

    assert recommendation.action == "create"
    assert recommendation.policy_rule == "recurring_regression_override"
    assert recommendation.history_context is not None
    assert recommendation.history_context.recent_regression_count >= 2
    assert recommendation.history_context.comparison_trend.label != "insufficient_history"


def test_family_history_reports_dataset_health_from_multiple_versions(tmp_path: Path) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    family_id = "fixture-timeline-family"
    first_regression = _report_id_for_regression(workspace.root)
    second_regression = _create_regression_comparison(
        workspace,
        baseline_model="stable-model",
        candidate_model="candidate-model",
    )

    first = evolve_dataset_family(
        family_id,
        comparison_id=first_regression,
        root=workspace.root,
        top_n=2,
    )
    for model in ("candidate-model", "stable-model"):
        _run_versioned_dataset(workspace.root, first.dataset.dataset_id, model)

    second = evolve_dataset_family(
        family_id,
        comparison_id=second_regression,
        root=workspace.root,
        top_n=3,
    )
    for model in ("candidate-model", "stable-model"):
        _run_versioned_dataset(workspace.root, second.dataset.dataset_id, model)

    snapshot = query_history_snapshot(
        family_id=family_id,
        root=workspace.root,
        limit=20,
    )

    assert len(list_dataset_versions(family_id, root=workspace.root)) == 2
    assert len(snapshot.dataset_versions) == 2
    assert snapshot.dataset_health is not None
    assert snapshot.dataset_health.version_count == 2
    assert snapshot.dataset_health.evaluation_run_count >= 4
    assert snapshot.dataset_health.recent_fail_rate is not None
    assert snapshot.dataset_health.previous_fail_rate is not None
    assert snapshot.dataset_health.health_label in {"stable", "improving", "degrading", "volatile"}


def test_cli_history_json_surfaces_temporal_snapshot(tmp_path: Path, capsys) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")

    exit_code = main(
        [
            "history",
            "--dataset",
            workspace.dataset_id,
            "--root",
            str(workspace.root),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["scope_kind"] == "dataset"
    assert payload["scope_value"] == workspace.dataset_id
    assert len(payload["run_history"]) == len(workspace.runs)
    assert len(payload["comparison_history"]) == len(workspace.comparisons)
    assert payload["run_trend"]["label"] != "insufficient_history"
