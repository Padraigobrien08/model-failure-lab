from __future__ import annotations

import json
from pathlib import Path

from model_failure_lab.cli import main
from model_failure_lab.datasets import evolve_dataset_family, list_dataset_versions
from model_failure_lab.governance import recommend_dataset_action
from model_failure_lab.index import QueryFilters, query_comparison_signals
from model_failure_lab.testing import materialize_insight_fixture


def _pick_regression_report_id(root: Path) -> str:
    rows = query_comparison_signals(
        QueryFilters(limit=20),
        verdict="regression",
        root=root,
    )
    assert rows
    return str(rows[0]["report_id"])


def test_cli_governance_recommend_review_apply_and_family_health(
    tmp_path: Path,
    capsys,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison_id = _pick_regression_report_id(workspace.root)

    recommend_exit = main(
        [
            "regressions",
            "recommend",
            "--comparison",
            comparison_id,
            "--root",
            str(workspace.root),
            "--min-severity",
            "0",
            "--json",
        ]
    )
    recommend_payload = json.loads(capsys.readouterr().out)

    review_exit = main(
        [
            "regressions",
            "review",
            "--root",
            str(workspace.root),
            "--min-severity",
            "0",
            "--json",
        ]
    )
    review_payload = json.loads(capsys.readouterr().out)

    apply_exit = main(
        [
            "regressions",
            "apply",
            "--root",
            str(workspace.root),
            "--min-severity",
            "0",
            "--json",
        ]
    )
    apply_payload = json.loads(capsys.readouterr().out)

    families_exit = main(
        [
            "dataset",
            "families",
            "--root",
            str(workspace.root),
            "--json",
        ]
    )
    families_payload = json.loads(capsys.readouterr().out)

    assert recommend_exit == 0
    assert recommend_payload["comparison_id"] == comparison_id
    assert recommend_payload["action"] in {"create", "evolve", "ignore"}
    assert recommend_payload["matched_family"]["family_id"].startswith("regression-")
    assert recommend_payload["escalation"]["status"] in {
        "suppressed",
        "watch",
        "elevated",
        "critical",
    }
    assert recommend_payload["lifecycle_recommendation"]["action"] in {
        "keep",
        "prune",
        "merge_candidate",
        "retire",
    }

    assert review_exit == 0
    assert review_payload["query_kind"] == "governance_review"
    assert review_payload["rows"]
    assert all(row["action"] in {"create", "evolve"} for row in review_payload["rows"])

    assert apply_exit == 0
    assert apply_payload["query_kind"] == "governance_apply"
    assert apply_payload["rows"]
    assert any(row["status"] in {"created", "evolved"} for row in apply_payload["rows"])

    assert families_exit == 0
    assert families_payload["query_kind"] == "dataset_family_health"
    assert families_payload["rows"]


def test_cli_dataset_lifecycle_review_and_apply(
    tmp_path: Path,
    capsys,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison_id = _pick_regression_report_id(workspace.root)
    family_id = "fixture-lifecycle-family"

    evolve_exit = main(
        [
            "dataset",
            "evolve",
            family_id,
            "--from-comparison",
            comparison_id,
            "--root",
            str(workspace.root),
            "--json",
        ]
    )
    _ = json.loads(capsys.readouterr().out)

    review_exit = main(
        [
            "dataset",
            "lifecycle-review",
            family_id,
            "--include-keep",
            "--root",
            str(workspace.root),
            "--json",
        ]
    )
    review_payload = json.loads(capsys.readouterr().out)

    apply_exit = main(
        [
            "dataset",
            "lifecycle-apply",
            family_id,
            "--root",
            str(workspace.root),
            "--json",
        ]
    )
    apply_payload = json.loads(capsys.readouterr().out)

    families_exit = main(
        [
            "dataset",
            "families",
            "--root",
            str(workspace.root),
            "--json",
        ]
    )
    families_payload = json.loads(capsys.readouterr().out)

    assert evolve_exit == 0
    assert review_exit == 0
    assert review_payload["query_kind"] == "dataset_lifecycle_review"
    assert review_payload["rows"]
    assert review_payload["rows"][0]["family_id"] == family_id

    assert apply_exit == 0
    assert apply_payload["family_id"] == family_id
    assert apply_payload["status"] in {"applied", "already_applied"}
    assert apply_payload["record"]["action"] in {"keep", "prune", "merge_candidate", "retire"}

    assert families_exit == 0
    family_row = next(row for row in families_payload["rows"] if row["family_id"] == family_id)
    assert family_row["active_lifecycle_action"] == apply_payload["record"]["action"]


def test_cli_dataset_portfolio_and_saved_plan_workflow(
    tmp_path: Path,
    capsys,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison_id = _pick_regression_report_id(workspace.root)
    suggested_family_id = recommend_dataset_action(
        comparison_id,
        root=workspace.root,
    ).matched_family.family_id
    related_family_id = "fixture-related-family"

    for family_id in (suggested_family_id, related_family_id):
        evolve_dataset_family(
            family_id,
            comparison_id=comparison_id,
            root=workspace.root,
            top_n=1,
        )

    portfolio_exit = main(
        [
            "dataset",
            "portfolio",
            "--root",
            str(workspace.root),
            "--actionability",
            "actionable",
            "--json",
        ]
    )
    portfolio_payload = json.loads(capsys.readouterr().out)

    single_exit = main(
        [
            "dataset",
            "portfolio",
            "--root",
            str(workspace.root),
            "--family",
            suggested_family_id,
            "--json",
        ]
    )
    single_payload = json.loads(capsys.readouterr().out)

    units_exit = main(
        [
            "dataset",
            "planning-units",
            "--root",
            str(workspace.root),
            "--actionability",
            "actionable",
            "--json",
        ]
    )
    units_payload = json.loads(capsys.readouterr().out)

    plan_create_exit = main(
        [
            "dataset",
            "plan-create",
            "--root",
            str(workspace.root),
            "--include-keep",
            "--json",
        ]
    )
    plan_create_payload = json.loads(capsys.readouterr().out)
    plan_id = plan_create_payload["plan"]["plan_id"]
    priority_band = plan_create_payload["plan"]["priority_bands"][0]

    plans_exit = main(
        [
            "dataset",
            "plans",
            "--root",
            str(workspace.root),
            "--dataset",
            workspace.dataset_id,
            "--model",
            "candidate-model",
            "--priority-band",
            priority_band,
            "--json",
        ]
    )
    plans_payload = json.loads(capsys.readouterr().out)

    plan_show_exit = main(
        [
            "dataset",
            "plan-show",
            plan_id,
            "--root",
            str(workspace.root),
            "--json",
        ]
    )
    plan_show_payload = json.loads(capsys.readouterr().out)

    plan_promote_exit = main(
        [
            "dataset",
            "plan-promote",
            plan_id,
            suggested_family_id,
            "--root",
            str(workspace.root),
            "--json",
        ]
    )
    plan_promote_payload = json.loads(capsys.readouterr().out)

    assert portfolio_exit == 0
    assert portfolio_payload["query_kind"] == "dataset_portfolio"
    assert len(portfolio_payload["rows"]) >= 2
    assert all(row["actionability"] == "actionable" for row in portfolio_payload["rows"])

    assert single_exit == 0
    assert len(single_payload["rows"]) == 1
    assert single_payload["rows"][0]["family_id"] == suggested_family_id

    assert units_exit == 0
    assert units_payload["query_kind"] == "dataset_planning_units"
    assert any(
        set(unit["family_ids"]) == {suggested_family_id, related_family_id}
        for unit in units_payload["rows"]
    )

    assert plan_create_exit == 0
    assert plan_create_payload["status"] in {"saved", "already_exists"}
    assert plan_create_payload["plan"]["actions"]
    assert any(
        action["family_id"] == suggested_family_id
        for action in plan_create_payload["plan"]["actions"]
    )

    assert plans_exit == 0
    assert plans_payload["query_kind"] == "dataset_portfolio_plans"
    assert any(row["plan_id"] == plan_id for row in plans_payload["rows"])

    assert plan_show_exit == 0
    assert plan_show_payload["plan_id"] == plan_id
    assert len(plan_show_payload["actions"]) == len(plan_create_payload["plan"]["actions"])

    assert plan_promote_exit == 0
    assert plan_promote_payload["plan_id"] == plan_id
    assert plan_promote_payload["family_id"] == suggested_family_id
    assert plan_promote_payload["result"]["record"]["source"].startswith("portfolio-plan:")


def test_cli_dataset_plan_execution_workflow(
    tmp_path: Path,
    capsys,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison_id = _pick_regression_report_id(workspace.root)
    suggested_family_id = recommend_dataset_action(
        comparison_id,
        root=workspace.root,
    ).matched_family.family_id
    related_family_id = "fixture-related-family"

    for family_id in (suggested_family_id, related_family_id):
        evolve_dataset_family(
            family_id,
            comparison_id=comparison_id,
            root=workspace.root,
            top_n=1,
        )

    plan_create_exit = main(
        [
            "dataset",
            "plan-create",
            "--root",
            str(workspace.root),
            "--include-keep",
            "--json",
        ]
    )
    plan_create_payload = json.loads(capsys.readouterr().out)
    plan_id = plan_create_payload["plan"]["plan_id"]

    preflight_exit = main(
        [
            "dataset",
            "plan-preflight",
            plan_id,
            "--root",
            str(workspace.root),
            "--json",
        ]
    )
    preflight_payload = json.loads(capsys.readouterr().out)

    execute_exit = main(
        [
            "dataset",
            "plan-execute",
            plan_id,
            "--root",
            str(workspace.root),
            "--mode",
            "stepwise",
            "--json",
        ]
    )
    execute_payload = json.loads(capsys.readouterr().out)
    execution_id = execute_payload["execution"]["execution_id"]

    executions_exit = main(
        [
            "dataset",
            "executions",
            "--root",
            str(workspace.root),
            "--plan",
            plan_id,
            "--json",
        ]
    )
    executions_payload = json.loads(capsys.readouterr().out)

    show_exit = main(
        [
            "dataset",
            "execution-show",
            execution_id,
            "--root",
            str(workspace.root),
            "--json",
        ]
    )
    show_payload = json.loads(capsys.readouterr().out)

    assert plan_create_exit == 0
    assert preflight_exit == 0
    assert preflight_payload["status"] == "ready"
    assert preflight_payload["ready_actions"] >= 1

    assert execute_exit == 0
    assert execute_payload["status"] in {"checkpointed", "executed"}
    assert Path(execute_payload["output_path"]).exists()
    assert execute_payload["execution"]["mode"] == "stepwise"
    assert execute_payload["execution"]["receipts"]
    assert execute_payload["execution"]["receipts"][0]["follow_up"]["status"] == "prepared"
    assert (
        execute_payload["execution"]["receipts"][0]["after_snapshot"]["active_lifecycle_action"]
        == execute_payload["execution"]["receipts"][0]["action"]
    )

    assert executions_exit == 0
    assert executions_payload["query_kind"] == "dataset_portfolio_plan_executions"
    assert any(row["execution_id"] == execution_id for row in executions_payload["rows"])

    assert show_exit == 0
    assert show_payload["execution_id"] == execution_id
    assert show_payload["preflight"]["plan_id"] == plan_id
    assert show_payload["receipts"][0]["rollback_guidance"]


def test_cli_dataset_plan_preflight_blocks_when_family_history_is_missing(
    tmp_path: Path,
    capsys,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison_id = _pick_regression_report_id(workspace.root)
    family_id = recommend_dataset_action(
        comparison_id,
        root=workspace.root,
    ).matched_family.family_id

    evolve_dataset_family(
        family_id,
        comparison_id=comparison_id,
        root=workspace.root,
        top_n=1,
    )

    plan_create_exit = main(
        [
            "dataset",
            "plan-create",
            "--root",
            str(workspace.root),
            "--include-keep",
            "--json",
        ]
    )
    plan_create_payload = json.loads(capsys.readouterr().out)
    plan_id = plan_create_payload["plan"]["plan_id"]

    for version in list_dataset_versions(family_id, root=workspace.root):
        version.path.unlink()

    preflight_exit = main(
        [
            "dataset",
            "plan-preflight",
            plan_id,
            "--root",
            str(workspace.root),
            "--family",
            family_id,
            "--json",
        ]
    )
    preflight_payload = json.loads(capsys.readouterr().out)

    assert plan_create_exit == 0
    assert any(
        action["family_id"] == family_id
        for action in plan_create_payload["plan"]["actions"]
    )
    assert preflight_exit == 0
    assert preflight_payload["status"] == "blocked"
    assert preflight_payload["blocked_actions"] == 1
    assert "no longer" in preflight_payload["checks"][0]["summary"].lower()
