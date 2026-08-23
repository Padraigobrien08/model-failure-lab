"""The regression-gate waiver file accepts YAML, matching the console remedy.

The Gate screen tells operators to run `failure-lab regressions gate --waivers
waivers.yml`; the loader must therefore parse YAML (and JSON, which is a YAML subset).
"""

from __future__ import annotations

from pathlib import Path

from model_failure_lab.governance.gates import _load_waivers


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
