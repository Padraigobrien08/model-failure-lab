from __future__ import annotations

import json
from pathlib import Path

from model_failure_lab.cli import main
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
