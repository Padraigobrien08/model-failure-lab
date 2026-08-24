"""A retired dataset family stops blocking the regression gate.

Before this, `dataset lifecycle apply --action retire` recorded an action that no
consumer honored. Now the gate treats a retired family's regressions as waived.
"""

from __future__ import annotations

from pathlib import Path

from model_failure_lab.governance.gates import evaluate_regression_gate
from model_failure_lab.governance.lifecycle import (
    LifecycleActionRecord,
    lifecycle_family_directory,
)
from model_failure_lab.governance.workflow import review_dataset_actions
from model_failure_lab.storage import write_json
from model_failure_lab.testing import materialize_insight_fixture


def _retire_family(family_id: str, root: Path) -> None:
    record = LifecycleActionRecord(
        action_id="retire-0001",
        family_id=family_id,
        action="retire",
        health_condition="manual",
        rationale="winding down",
        applied_at="2026-08-23T00:00:00Z",
        source="test",
        status="applied",
        target_family_id=None,
        related_family_ids=(),
        source_dataset_id=None,
        primary_failure_type=None,
        latest_dataset_id=None,
        version_count=None,
        evaluation_run_count=None,
        recent_fail_rate=None,
        projected_case_count=None,
        comparison_id=None,
        escalation_status=None,
        escalation_score=None,
    )
    family_dir = lifecycle_family_directory(family_id, root=root, create=True)
    write_json(family_dir / "retire-0001.json", record.to_payload())


def test_retire_action_unblocks_gate_for_that_family(tmp_path: Path) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fx")
    root = workspace.root

    blocking = [
        rec
        for rec in review_dataset_actions(root=root, include_ignored=True)
        if rec.action in {"create", "evolve"}
    ]
    assert blocking, "fixture should contain at least one blocking recommendation"
    comparison_id = blocking[0].comparison_id

    assert evaluate_regression_gate(root=root).blocked is True

    # Retire every family with a blocking recommendation so the gate fully unblocks;
    # the fixture can surface more than one blocking family.
    for family_id in {rec.matched_family.family_id for rec in blocking}:
        _retire_family(family_id, root)

    result = evaluate_regression_gate(root=root)
    assert result.blocked is False
    row = next(r for r in result.rows if r.comparison_id == comparison_id)
    assert row.blocked is False
    assert row.waived is True
    assert row.waiver is not None
    assert "retired" in row.waiver.reason
