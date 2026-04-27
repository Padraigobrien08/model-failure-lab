from __future__ import annotations

from pathlib import Path

from model_failure_lab.clusters import FailureClusterSummary
from model_failure_lab.datasets import evolve_dataset_family, preview_regression_pack
from model_failure_lab.governance import (
    GovernancePolicy,
    apply_dataset_actions,
    apply_dataset_lifecycle_action,
    attest_portfolio_execution_outcome,
    create_saved_portfolio_plan,
    describe_dataset_family_lifecycle,
    execute_saved_portfolio_plan,
    link_portfolio_execution_outcome_evidence,
    list_dataset_family_health,
    list_dataset_lifecycle_actions,
    list_dataset_planning_units,
    list_dataset_portfolio,
    recommend_dataset_action,
    review_dataset_actions,
    summarize_portfolio_outcomes_for_family,
)
from model_failure_lab.governance.policy import (
    GovernanceFamilyMatch,
    LifecycleRecommendation,
    _build_escalation,
    _recommend_lifecycle_action,
)
from model_failure_lab.history import DatasetHealthSummary, MetricTrend, SignalHistoryContext
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


def _metric_trend(
    *,
    label: str = "stable",
    delta: float | None = 0.0,
    volatility_label: str = "low",
) -> MetricTrend:
    return MetricTrend(
        label=label,
        delta=delta,
        sample_count=3,
        first_value=0.1,
        last_value=0.1 if delta is None else 0.1 + delta,
        volatility=0.0 if volatility_label == "low" else 0.2,
        volatility_label=volatility_label,
    )


def _cluster_summary() -> FailureClusterSummary:
    return FailureClusterSummary(
        cluster_id="cd_fixture",
        cluster_kind="comparison_delta",
        label="fixture cluster",
        summary="fixture cluster summary",
        occurrence_count=2,
        scope_count=2,
        first_seen_at="2026-04-05T10:00:00Z",
        last_seen_at="2026-04-05T11:00:00Z",
        datasets=("fixture",),
        models=("baseline→candidate",),
        failure_types=("reasoning",),
        transition_types=("no_failure_to_failure",),
        recent_severity=0.25,
        representative_evidence=(),
    )


def _family_match() -> GovernanceFamilyMatch:
    return GovernanceFamilyMatch(
        family_id="fixture-family",
        match_kind="existing_exact",
        exists=True,
        version_count=2,
        latest_dataset_id="fixture-family-v2",
        current_case_count=4,
        proposed_addition_count=1,
        duplicate_case_count=0,
        duplicate_ratio=0.0,
        projected_case_count=5,
        family_case_cap=20,
        cap_reached=False,
        duplicate_ratio_exceeded=False,
    )


def _history_context(
    *,
    recent_regression_count: int,
    clusters: tuple[FailureClusterSummary, ...] = (),
    family_health: DatasetHealthSummary | None = None,
) -> SignalHistoryContext:
    return SignalHistoryContext(
        scope_kind="dataset",
        scope_value="fixture-dataset",
        recent_comparison_count=max(recent_regression_count, 1),
        recent_regression_count=recent_regression_count,
        comparison_trend=_metric_trend(),
        candidate_run_trend=None,
        recurring_failures=(),
        recurring_clusters=clusters,
        recent_comparisons=(),
        family_health=family_health,
    )


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
    assert first.escalation is not None
    assert first.lifecycle_recommendation is not None
    assert first.lifecycle_recommendation.projected_case_count is not None


def test_escalation_status_bands_cover_suppressed_watch_elevated_and_critical() -> None:
    family_match = _family_match()
    keep = LifecycleRecommendation(
        family_id="fixture-family",
        action="keep",
        health_condition="keepable",
        rationale="keep the family active",
    )

    suppressed = _build_escalation(
        action="ignore",
        signal_verdict="neutral",
        severity=0.0,
        family_match=family_match,
        history_context=_history_context(recent_regression_count=0),
        cluster_context=(),
        lifecycle_recommendation=keep,
    )
    watch = _build_escalation(
        action="create",
        signal_verdict="regression",
        severity=0.1,
        family_match=family_match,
        history_context=_history_context(recent_regression_count=0),
        cluster_context=(),
        lifecycle_recommendation=keep,
    )
    elevated = _build_escalation(
        action="create",
        signal_verdict="regression",
        severity=0.23,
        family_match=family_match,
        history_context=_history_context(recent_regression_count=0),
        cluster_context=(),
        lifecycle_recommendation=keep,
    )
    critical = _build_escalation(
        action="create",
        signal_verdict="regression",
        severity=0.25,
        family_match=family_match,
        history_context=_history_context(
            recent_regression_count=2,
            clusters=(_cluster_summary(),),
        ),
        cluster_context=(_cluster_summary(),),
        lifecycle_recommendation=keep,
    )

    assert suppressed.status == "suppressed"
    assert watch.status == "watch"
    assert elevated.status == "elevated"
    assert critical.status == "critical"


def test_lifecycle_action_rules_cover_prune_retire_and_keep(tmp_path: Path) -> None:
    overgrown = _recommend_lifecycle_action(
        family_id="fixture-family",
        health_summary=DatasetHealthSummary(
            family_id="fixture-family",
            health_label="degrading",
            trend=_metric_trend(label="degrading", delta=0.1, volatility_label="high"),
            version_count=4,
            evaluation_run_count=4,
            recent_fail_rate=0.25,
            previous_fail_rate=0.15,
            latest_dataset_id="fixture-family-v4",
            latest_version_tag="v4",
            latest_created_at="2026-04-05T10:00:00Z",
            source_dataset_id="fixture-dataset",
            primary_failure_type="reasoning",
        ),
        latest_case_count=12,
        projected_case_count=40,
        latest_dataset_id="fixture-family-v4",
        root=tmp_path,
    )
    retire = _recommend_lifecycle_action(
        family_id="fixture-family",
        health_summary=DatasetHealthSummary(
            family_id="fixture-family",
            health_label="stable",
            trend=_metric_trend(label="stable", delta=0.0, volatility_label="low"),
            version_count=2,
            evaluation_run_count=3,
            recent_fail_rate=0.02,
            previous_fail_rate=0.03,
            latest_dataset_id="fixture-family-v2",
            latest_version_tag="v2",
            latest_created_at="2026-04-05T10:00:00Z",
            source_dataset_id="fixture-dataset",
            primary_failure_type="reasoning",
        ),
        latest_case_count=8,
        projected_case_count=8,
        latest_dataset_id="fixture-family-v2",
        root=tmp_path,
    )
    keep = _recommend_lifecycle_action(
        family_id="fixture-family",
        health_summary=DatasetHealthSummary(
            family_id="fixture-family",
            health_label="volatile",
            trend=_metric_trend(label="stable", delta=0.0, volatility_label="medium"),
            version_count=2,
            evaluation_run_count=2,
            recent_fail_rate=0.12,
            previous_fail_rate=0.1,
            latest_dataset_id="fixture-family-v2",
            latest_version_tag="v2",
            latest_created_at="2026-04-05T10:00:00Z",
            source_dataset_id="fixture-dataset",
            primary_failure_type="reasoning",
        ),
        latest_case_count=8,
        projected_case_count=8,
        latest_dataset_id="fixture-family-v2",
        root=tmp_path,
    )

    assert overgrown.action == "prune"
    assert retire.action == "retire"
    assert keep.action == "keep"


def test_dataset_portfolio_ranks_existing_family_with_deterministic_evidence(
    tmp_path: Path,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison_id = _pick_regression_comparison(workspace.root, minimum_cases=2)
    recommendation = recommend_dataset_action(comparison_id, root=workspace.root)
    family_id = recommendation.matched_family.family_id

    evolve_dataset_family(
        family_id,
        comparison_id=comparison_id,
        root=workspace.root,
        top_n=2,
    )

    first = list_dataset_portfolio(root=workspace.root)
    second = list_dataset_portfolio(root=workspace.root)

    assert first
    assert first[0].family_id == family_id
    assert first[0].priority_rank == 1
    assert first[0].comparison_refs
    assert first[0].comparison_refs[0].comparison_id == comparison_id
    assert first[0].escalation_status in {"watch", "elevated", "critical", "suppressed"}
    assert "lifecycle=" in first[0].rationale
    assert [row.to_payload() for row in first] == [row.to_payload() for row in second]


def test_dataset_portfolio_includes_outcome_feedback_from_attested_follow_up(
    tmp_path: Path,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    regression_comparison_id = _pick_regression_comparison(workspace.root, minimum_cases=2)
    family_id = recommend_dataset_action(
        regression_comparison_id,
        root=workspace.root,
    ).matched_family.family_id

    evolve_dataset_family(
        family_id,
        comparison_id=regression_comparison_id,
        root=workspace.root,
        top_n=2,
    )

    plan = create_saved_portfolio_plan(root=workspace.root, include_keep=True)
    execution = execute_saved_portfolio_plan(
        plan.plan.plan_id,
        root=workspace.root,
        mode="stepwise",
    )
    receipt = execution.execution.receipts[0]
    follow_up_comparison_id = _pick_improvement_comparison(workspace.root)

    link_portfolio_execution_outcome_evidence(
        execution.execution.execution_id,
        receipt.checkpoint_index,
        root=workspace.root,
        comparison_ids=(follow_up_comparison_id,),
        note="Linked deterministic follow-up comparison.",
    )
    attest_portfolio_execution_outcome(
        execution.execution.execution_id,
        receipt.checkpoint_index,
        root=workspace.root,
        note="Outcome attested from saved comparison evidence.",
    )

    summary = summarize_portfolio_outcomes_for_family(family_id, root=workspace.root)
    portfolio_rows = list_dataset_portfolio(root=workspace.root)
    portfolio_row = next(row for row in portfolio_rows if row.family_id == family_id)

    assert summary is not None
    assert summary.attested_count == 1
    assert summary.latest_state == "attested"
    assert summary.latest_verdict in {"improved", "regressed", "inconclusive", "no_signal"}
    assert (
        summary.improved_count
        + summary.regressed_count
        + summary.inconclusive_count
        + summary.no_signal_count
        == 1
    )
    assert portfolio_row.outcome_feedback is not None
    assert portfolio_row.outcome_feedback.latest_verdict == summary.latest_verdict
    assert f"latest_outcome={summary.latest_verdict}" in portfolio_row.rationale


def test_dataset_planning_units_group_merge_candidates_together(tmp_path: Path) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison_id = _pick_regression_comparison(workspace.root, minimum_cases=2)
    family_ids = ("fixture-related-family-a", "fixture-related-family-b")

    for family_id in family_ids:
        evolve_dataset_family(
            family_id,
            comparison_id=comparison_id,
            root=workspace.root,
            top_n=1,
        )

    portfolio_rows = list_dataset_portfolio(root=workspace.root)
    related_rows = [row for row in portfolio_rows if row.family_id in family_ids]
    units = list_dataset_planning_units(root=workspace.root)
    merge_unit = next(
        unit
        for unit in units
        if set(family_ids).issubset(set(unit.family_ids))
    )

    assert len(related_rows) == 2
    assert all(row.lifecycle_action == "merge_candidate" for row in related_rows)
    assert merge_unit.unit_kind == "merge_review"
    assert set(merge_unit.family_ids) == set(family_ids)


def test_describe_dataset_family_lifecycle_surfaces_merge_candidates_and_provenance(
    tmp_path: Path,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison_id = _pick_regression_comparison(workspace.root)

    evolve_dataset_family(
        "fixture-merge-a",
        comparison_id=comparison_id,
        root=workspace.root,
        top_n=1,
    )
    evolve_dataset_family(
        "fixture-merge-b",
        comparison_id=comparison_id,
        root=workspace.root,
        top_n=1,
    )

    recommendation = describe_dataset_family_lifecycle("fixture-merge-a", root=workspace.root)

    assert recommendation is not None
    assert recommendation.action == "merge_candidate"
    assert recommendation.target_family_id == "fixture-merge-b"
    assert recommendation.source_dataset_id == workspace.dataset_id
    assert recommendation.primary_failure_type is not None
    assert recommendation.latest_dataset_id == "fixture-merge-a-v1"


def test_comparison_to_lifecycle_apply_updates_family_state(tmp_path: Path) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison_id = _pick_regression_comparison(workspace.root)
    family_id = "fixture-lifecycle-loop"

    evolve_dataset_family(
        family_id,
        comparison_id=comparison_id,
        root=workspace.root,
        top_n=1,
    )
    recommendation = recommend_dataset_action(
        comparison_id,
        root=workspace.root,
        policy=GovernancePolicy(family_id=family_id, minimum_severity=0.0),
    )
    lifecycle = describe_dataset_family_lifecycle(family_id, root=workspace.root)
    assert recommendation.history_context is not None
    assert recommendation.escalation is not None
    assert lifecycle is not None

    result = apply_dataset_lifecycle_action(family_id, root=workspace.root, action=lifecycle.action)

    assert result.status in {"applied", "already_applied"}
    assert list_dataset_lifecycle_actions(family_id, root=workspace.root)
    health = next(
        row for row in list_dataset_family_health(root=workspace.root) if row.family_id == family_id
    )
    assert health.active_lifecycle_action == lifecycle.action


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
