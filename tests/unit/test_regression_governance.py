from __future__ import annotations

from pathlib import Path

from model_failure_lab.datasets import evolve_dataset_family, preview_regression_pack
from model_failure_lab.governance import (
    GovernancePolicy,
    apply_dataset_actions,
    list_dataset_family_health,
    recommend_dataset_action,
    review_dataset_actions,
)
from model_failure_lab.index import QueryFilters, query_comparison_signals
from model_failure_lab.testing import materialize_insight_fixture


def _pick_regression_comparison(root: Path, *, minimum_cases: int = 1) -> str:
    rows = query_comparison_signals(
        QueryFilters(limit=20),
        verdict="regression",
        root=root,
    )
    for row in rows:
        preview = preview_regression_pack(
            comparison_id=row["report_id"],
            root=root,
            top_n=max(minimum_cases, 1),
        )
        if preview.selected_case_count >= minimum_cases:
            return row["report_id"]
    raise AssertionError("expected at least one regression comparison in the fixture")


def _pick_improvement_comparison(root: Path) -> str:
    rows = query_comparison_signals(
        QueryFilters(limit=20),
        verdict="improvement",
        root=root,
    )
    assert rows
    return str(rows[0]["report_id"])


def test_preview_regression_pack_does_not_write_dataset_files(tmp_path: Path) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison_id = _pick_regression_comparison(workspace.root)
    before = sorted(
        path.relative_to(workspace.root).as_posix()
        for path in (workspace.root / "datasets").rglob("*.json")
    )

    preview = preview_regression_pack(
        comparison_id=comparison_id,
        root=workspace.root,
        top_n=2,
    )

    after = sorted(
        path.relative_to(workspace.root).as_posix()
        for path in (workspace.root / "datasets").rglob("*.json")
    )

    assert preview.selected_case_count > 0
    assert preview.preview_cases
    assert before == after


def test_recommend_dataset_action_returns_create_for_new_regression_family(
    tmp_path: Path,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison_id = _pick_regression_comparison(workspace.root)

    recommendation = recommend_dataset_action(comparison_id, root=workspace.root)

    assert recommendation.action == "create"
    assert recommendation.policy_rule == "new_family_required"
    assert recommendation.selected_case_count > 0
    assert recommendation.matched_family.exists is False
    assert recommendation.evidence_case_ids


def test_recommend_dataset_action_returns_evolve_when_existing_family_matches(
    tmp_path: Path,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    family_id = "fixture-governance-family"

    seed_comparison = _pick_regression_comparison(workspace.root, minimum_cases=2)
    evolve_dataset_family(
        family_id,
        comparison_id=seed_comparison,
        root=workspace.root,
        top_n=1,
    )

    evolved = recommend_dataset_action(
        seed_comparison,
        root=workspace.root,
        policy=GovernancePolicy(
            family_id=family_id,
            minimum_severity=0.0,
            top_n=3,
            max_duplicate_ratio=None,
        ),
    )

    assert evolved.action == "evolve"
    assert evolved.policy_rule == "existing_family_match"
    assert evolved.matched_family.exists is True
    assert evolved.matched_family.family_id == family_id
    assert evolved.matched_family.proposed_addition_count > 0


def test_recommend_dataset_action_ignores_non_regression_and_below_threshold_signals(
    tmp_path: Path,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    rows = query_comparison_signals(
        QueryFilters(limit=10),
        verdict=None,
        root=workspace.root,
    )
    non_regression = next(
        row for row in rows if row["signal_verdict"] in {"improvement", "neutral", "incompatible"}
    )

    first = recommend_dataset_action(non_regression["report_id"], root=workspace.root)
    second = recommend_dataset_action(
        _pick_regression_comparison(workspace.root),
        root=workspace.root,
        policy=GovernancePolicy(minimum_severity=1.0),
    )

    assert first.action == "ignore"
    assert first.policy_rule in {"non_regression_signal", "incompatible_signal"}
    assert second.action == "ignore"
    assert second.policy_rule == "below_minimum_severity"


def test_recommend_dataset_action_includes_recurring_cluster_context_when_available(
    tmp_path: Path,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")

    recommendation = recommend_dataset_action(
        _pick_improvement_comparison(workspace.root),
        root=workspace.root,
    )

    assert recommendation.action == "ignore"
    assert recommendation.cluster_context
    assert recommendation.history_context is not None
    assert recommendation.history_context.recurring_clusters == recommendation.cluster_context
    assert "Primary recurring cluster" in recommendation.rationale


def test_recommend_dataset_action_respects_family_cap_and_duplicate_growth_guards(
    tmp_path: Path,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison_id = _pick_regression_comparison(workspace.root, minimum_cases=1)
    family_id = "fixture-cap-guard-family"

    capped = recommend_dataset_action(
        comparison_id,
        root=workspace.root,
        policy=GovernancePolicy(family_id=family_id, family_case_cap=1),
    )

    evolve_dataset_family(
        family_id,
        comparison_id=comparison_id,
        root=workspace.root,
        top_n=1,
    )
    duplicate_guard = recommend_dataset_action(
        comparison_id,
        root=workspace.root,
        policy=GovernancePolicy(
            family_id=family_id,
            minimum_severity=0.0,
            top_n=2,
            max_duplicate_ratio=0.4,
            family_case_cap=20,
        ),
    )

    assert capped.action == "ignore"
    assert capped.policy_rule == "family_case_cap_reached"
    assert duplicate_guard.action == "ignore"
    assert duplicate_guard.policy_rule == "duplicate_growth_threshold_exceeded"
    assert duplicate_guard.matched_family.duplicate_ratio > 0.4
    assert duplicate_guard.matched_family.proposed_addition_count > 0


def test_recommend_dataset_action_is_deterministic(tmp_path: Path) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison_id = _pick_regression_comparison(workspace.root)
    policy = GovernancePolicy(minimum_severity=0.0, top_n=3)

    first = recommend_dataset_action(comparison_id, root=workspace.root, policy=policy)
    second = recommend_dataset_action(comparison_id, root=workspace.root, policy=policy)

    assert first.to_payload() == second.to_payload()


def test_list_dataset_family_health_reports_latest_family_state(tmp_path: Path) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison_id = _pick_regression_comparison(workspace.root)
    family_id = "fixture-health-family"

    evolve_dataset_family(
        family_id,
        comparison_id=comparison_id,
        root=workspace.root,
        top_n=1,
    )

    rows = list_dataset_family_health(root=workspace.root)
    health = next(row for row in rows if row.family_id == family_id)

    assert health.version_count == 1
    assert health.latest_dataset_id.endswith("-v1")
    assert health.latest_case_count > 0
    assert health.source_dataset_id == workspace.dataset_id


def test_review_and_apply_dataset_actions_use_deterministic_signal_order(tmp_path: Path) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    policy = GovernancePolicy(minimum_severity=0.0, top_n=2)

    review = review_dataset_actions(root=workspace.root, policy=policy)
    apply = apply_dataset_actions(root=workspace.root, policy=policy)
    second_apply = apply_dataset_actions(root=workspace.root, policy=policy)

    assert review
    assert any(entry.action in {"create", "evolve"} for entry in review)
    assert apply
    assert any(result.status in {"created", "evolved"} for result in apply)
    assert all(
        result.status == "skipped" or result.dataset_id is not None
        for result in apply
    )
    assert all(result.status == "skipped" for result in second_apply)
