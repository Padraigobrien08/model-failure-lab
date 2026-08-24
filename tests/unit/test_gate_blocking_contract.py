"""The regression gate blocks on the signal verdict, not the dataset-governance action.

`compare --gate` fails on any regression verdict, but the governance/console gate used
to derive `blocked` from the create/evolve recommendation, which is severity-gated. That
let a below-minimum-severity regression pass the governance gate while failing
`compare --gate` on the same runs. Blocking is now a verdict decision on every surface;
the severity floor governs only whether to create/evolve a dataset family.
"""

from __future__ import annotations

from pathlib import Path

from model_failure_lab.governance.gates import evaluate_regression_gate
from model_failure_lab.governance.policy import GovernancePolicy
from model_failure_lab.testing import materialize_insight_fixture


def test_below_minimum_severity_regression_still_blocks_the_gate(tmp_path: Path) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fx")

    # minimum_severity above every comparison's severity, so governance would "ignore"
    # each regression (no dataset family created). recurrence override disabled so the
    # only thing that can block is the verdict itself.
    result = evaluate_regression_gate(
        root=workspace.root,
        policy=GovernancePolicy(minimum_severity=1.0, recurrence_threshold=None),
    )

    regression_rows = [row for row in result.rows if row.verdict == "regression"]
    assert regression_rows, "fixture should contain at least one regression comparison"

    # Every regression blocks CI even though governance declines to act on it.
    for row in regression_rows:
        assert row.action == "ignore"
        assert row.policy_rule == "below_minimum_severity"
        assert row.blocked is True
    assert result.blocked is True

    # Non-regression comparisons never block.
    for row in result.rows:
        if row.verdict != "regression":
            assert row.blocked is False


def test_non_regression_comparisons_do_not_block(tmp_path: Path) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fx")

    result = evaluate_regression_gate(
        root=workspace.root,
        policy=GovernancePolicy(minimum_severity=1.0, recurrence_threshold=None),
    )

    for row in result.rows:
        if row.verdict in {"improvement", "neutral", "incompatible"}:
            assert row.blocked is False
