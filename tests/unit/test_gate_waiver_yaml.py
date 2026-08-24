"""The regression-gate waiver file accepts YAML, matching the console remedy.

The Gate screen tells operators to run `failure-lab regressions gate --waivers
waivers.yml`; the loader must therefore parse YAML (and JSON, which is a YAML subset).
"""

from __future__ import annotations

from pathlib import Path

from model_failure_lab.governance.gates import (
    _load_waivers,
    default_policy_path,
    default_waiver_path,
    evaluate_regression_gate,
)


def test_load_waivers_accepts_yaml(tmp_path: Path) -> None:
    waiver_path = tmp_path / "waivers.yml"
    waiver_path.write_text(
        "waivers:\n"
        "  - comparison_id: compare_abc_to_def_0001\n"
        "    reason: tracked in TICKET-1\n"
        "    owner: qa\n"
        "    expires_at: '2999-01-01T00:00:00Z'\n",
        encoding="utf-8",
    )

    waivers = _load_waivers(root=tmp_path, waiver_path=waiver_path)

    assert set(waivers) == {"compare_abc_to_def_0001"}
    waiver = waivers["compare_abc_to_def_0001"]
    assert waiver.reason == "tracked in TICKET-1"
    assert waiver.owner == "qa"
    assert waiver.active is True


def test_load_waivers_still_accepts_json(tmp_path: Path) -> None:
    waiver_path = tmp_path / "waivers.json"
    waiver_path.write_text(
        '{"waivers": [{"comparison_id": "c1", "reason": "r"}]}',
        encoding="utf-8",
    )

    waivers = _load_waivers(root=tmp_path, waiver_path=waiver_path)

    assert set(waivers) == {"c1"}


def test_gate_discovers_conventional_files_so_console_matches_cli(tmp_path: Path) -> None:
    """The read-only console `gate` endpoint passes no waiver/policy path; it must
    still see a workspace's committed governance/policy.yml + governance/waivers.yml,
    exactly like the CLI default, so the two surfaces never disagree."""
    governance = tmp_path / "governance"
    governance.mkdir()
    (governance / "policy.yml").write_text("minimum_severity: 0.2\n", encoding="utf-8")
    (governance / "waivers.yml").write_text("waivers: []\n", encoding="utf-8")

    result = evaluate_regression_gate(root=tmp_path)

    assert result.policy.minimum_severity == 0.2
    assert result.policy_source == "governance/policy.yml"
    assert result.waiver_source == "governance/waivers.yml"


def test_gate_reports_default_sources_when_no_files_present(tmp_path: Path) -> None:
    result = evaluate_regression_gate(root=tmp_path)

    assert result.policy_source == "default"
    assert result.waiver_source is None
    assert default_policy_path(tmp_path) is None
    assert default_waiver_path(tmp_path) is None


def test_explicit_policy_argument_overrides_conventional_file(tmp_path: Path) -> None:
    from model_failure_lab.governance.policy import GovernancePolicy

    governance = tmp_path / "governance"
    governance.mkdir()
    (governance / "policy.yml").write_text("minimum_severity: 0.9\n", encoding="utf-8")

    result = evaluate_regression_gate(root=tmp_path, policy=GovernancePolicy(minimum_severity=0.1))

    assert result.policy.minimum_severity == 0.1
    assert result.policy_source == "argument"
