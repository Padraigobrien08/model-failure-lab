"""The console's transition vocabulary must be the engine's.

DESIGN.md binds every screen: "Red (`bad`) means regression. Only regression." The engine
decides what a regression is, in `reporting/signals.py:REGRESSION_TRANSITION_TYPES`, which
deliberately excludes `error_stage_changed` -- a case that was already erroring and now
errors at a different stage is not a net-new failure and does not move the verdict.

The console had its own copy of that set and included `error_stage_changed`, so a comparison
whose only change was an error stage moving rendered a NEUTRAL banner and a green PASS
directly above a red, regression-tinted transition group. Two definitions of "regression"
for one artifact.

`tests/fixtures/contract/transitions.json` is now the shared definition: this test writes it
from the engine's own constants, and `frontend/src/lib/artifacts/__tests__/transitions.test.ts`
asserts the TypeScript sets match it. Changing one side alone fails the other.

Regenerate deliberately with:

    FAILURE_LAB_REGENERATE_BRIDGE_FIXTURES=1 python3 -m pytest \\
        tests/unit/test_transition_vocabulary_contract.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from model_failure_lab.reporting.compare import TRANSITION_LABELS, TRANSITION_ORDER
from model_failure_lab.reporting.signals import REGRESSION_TRANSITION_TYPES

FIXTURE_PATH = (
    Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "contract" / "transitions.json"
)

# The engine has no named constant for these two; they are the complement of the regression
# and improvement sets, and are asserted below to be exactly that.
IMPROVEMENT_TRANSITION_TYPES = frozenset({"failure_to_no_failure", "error_cleared"})
CHURN_TRANSITION_TYPES = frozenset({"failure_type_swap", "error_stage_changed"})


def _contract() -> dict[str, list[str]]:
    return {
        "all": sorted(TRANSITION_LABELS),
        "order": list(TRANSITION_ORDER),
        "regression": sorted(REGRESSION_TRANSITION_TYPES),
        "improvement": sorted(IMPROVEMENT_TRANSITION_TYPES),
        "churn": sorted(CHURN_TRANSITION_TYPES),
    }


def test_transition_sets_partition_the_taxonomy() -> None:
    contract = _contract()
    buckets = [set(contract[name]) for name in ("regression", "improvement", "churn")]
    everything = set(contract["all"])

    # Every transition lands in exactly one bucket. Without this, a transition added to the
    # engine would silently render neutral in the console and be classified nowhere.
    union: set[str] = set()
    for bucket in buckets:
        assert not (union & bucket), f"transition classified twice: {sorted(union & bucket)}"
        union |= bucket
    assert union == everything, (
        f"unclassified transitions: {sorted(everything - union)}; "
        f"unknown transitions: {sorted(union - everything)}"
    )


def test_error_stage_changed_is_not_a_regression() -> None:
    # The specific divergence this contract exists to prevent. Stated as its own test so the
    # intent survives a future refactor of the sets.
    assert "error_stage_changed" not in REGRESSION_TRANSITION_TYPES
    assert "error_stage_changed" in CHURN_TRANSITION_TYPES


def test_transition_contract_matches_the_committed_fixture() -> None:
    contract = _contract()
    serialized = json.dumps(contract, indent=2, sort_keys=True) + "\n"
    if os.environ.get("FAILURE_LAB_REGENERATE_BRIDGE_FIXTURES") == "1":
        FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE_PATH.write_text(serialized, encoding="utf-8")
    assert FIXTURE_PATH.is_file(), (
        "missing tests/fixtures/contract/transitions.json; regenerate with "
        "FAILURE_LAB_REGENERATE_BRIDGE_FIXTURES=1"
    )
    assert serialized == FIXTURE_PATH.read_text(encoding="utf-8"), (
        "the engine's transition vocabulary changed. Update "
        "frontend/src/lib/artifacts/transitions.ts in the same commit and regenerate this "
        "fixture -- the console renders red from these sets."
    )
