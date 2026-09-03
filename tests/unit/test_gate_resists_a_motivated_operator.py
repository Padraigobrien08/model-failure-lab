"""Black-box attacks on the gate, generated rather than listed.

Every other test in this suite knows something about how the tool works: it imports
`evaluate_gate_conditions`, or asserts on a field of the report artifact, or compares three
surfaces to each other. That is how a gate that passed when a candidate deleted the cases it
broke survived four audits -- the surfaces all agreed, the conditions were all covered, and
nobody asked the question a user asks. So this file imports nothing from the engine but
`main`, touches no internal name, and knows only what an operator knows: a workspace of runs,
the CLI, and an exit code.

Going black-box was necessary and not sufficient. The first version of this file listed four
attacks and all four edited the *candidate*, written straight after fixing a candidate-side
hole -- so it could not see the mirror of the bug it existed for: deleting the same cases from
the *baseline* passed the gate on every surface. Removing the author's knowledge of the
implementation left their assumptions about the threat untouched.

So the attacks are a product, not a list. A comparison has two runs and a handful of things a
person can do to one, and the cross product covers both sides of every axis by construction:

    RUNS x EDITS  ->  the gate must still block

An edit that cannot apply to a run (there is nothing there to change) is skipped by name and
counted, so a silently inapplicable combination cannot masquerade as a passing one. The
combinations the gate genuinely does not stop are listed in `DOCUMENTED_GAPS` with a reason,
and the suite fails if one of them starts being caught -- the boundary cannot move in either
direction without somebody editing this file.

The invariant behind all of it: **no edit that removes or hides evidence may turn red into
green.** Only fixing the candidate's behaviour is allowed to do that, and the last test checks
that fixing it actually does -- a gate that blocks unconditionally would pass everything above.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from model_failure_lab.cli import main

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_RUNS = PROJECT_ROOT / "examples" / "regression_demo" / "runs"

BLOCKS = 1
PASSES = 0
RUNS = ("baseline", "candidate")


def _workspace(tmp_path: Path) -> Path:
    root = tmp_path / "ws"
    (root / "runs").mkdir(parents=True)
    for name in RUNS:
        shutil.copytree(DEMO_RUNS / name, root / "runs" / name)
    return root


def _cases(root: Path, run: str) -> list[dict]:
    return json.loads((root / "runs" / run / "results.json").read_text(encoding="utf-8"))["cases"]


def _rewrite(root: Path, run: str, cases: list[dict]) -> None:
    path = root / "runs" / run / "results.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["cases"] = cases
    payload["total_cases"] = len(cases)
    path.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")


def _failure_type(case: dict) -> str:
    return (case.get("classification") or {}).get("failure_type") or "no_failure"


def _broke(root: Path) -> set[str]:
    """Case ids the candidate fails and the baseline does not -- the actual regressions."""

    clean = {c["case_id"] for c in _cases(root, "baseline") if _failure_type(c) == "no_failure"}
    return {
        c["case_id"]
        for c in _cases(root, "candidate")
        if c["case_id"] in clean and _failure_type(c) != "no_failure"
    }


def _gate(root: Path) -> int:
    return main(["compare", "baseline", "candidate", "--gate", "--root", str(root)])


# --------------------------------------------------------------------------------------
# The edits. Each takes a workspace and the run to apply itself to, and returns False when
# there is nothing in that run for it to change.
# --------------------------------------------------------------------------------------


def _delete_the_regressed_cases(root: Path, run: str) -> bool:
    """"Those four were noisy, so I took them out of the suite.\""""

    broke = _broke(root)
    cases = _cases(root, run)
    kept = [c for c in cases if c["case_id"] not in broke]
    if len(kept) == len(cases):
        return False
    _rewrite(root, run, kept)
    return True


def _delete_one_regressed_case(root: Path, run: str) -> bool:
    """"Only one of them was flaky." One is enough: it is still a regression nobody sees."""

    broke = sorted(_broke(root))
    cases = _cases(root, run)
    kept = [c for c in cases if c["case_id"] != broke[0]]
    if len(kept) == len(cases):
        return False
    _rewrite(root, run, kept)
    return True


def _run_half_the_suite(root: Path, run: str) -> bool:
    """"The full suite is slow in CI, so that job runs a subset.\""""

    cases = _cases(root, run)
    if len(cases) < 2:
        return False
    _rewrite(root, run, cases[: len(cases) // 2])
    return True


def _pad_with_easy_passing_cases(root: Path, run: str) -> bool:
    """"I added coverage." The failure *rate* falls; the same cases are still broken."""

    cases = _cases(root, run)
    template = next((c for c in cases if _failure_type(c) == "no_failure"), None)
    if template is None:
        return False
    padding = []
    for index in range(24):
        clone = json.loads(json.dumps(template))
        clone["case_id"] = f"easy-{index}"
        if isinstance(clone.get("prompt"), dict):
            clone["prompt"]["id"] = f"easy-{index}"
        padding.append(clone)
    _rewrite(root, run, cases + padding)
    return True


def _relabel_failures_as_passes(root: Path, run: str) -> bool:
    """"The classifier was wrong about these." Editing the verdict, not the behaviour."""

    cases = _cases(root, run)
    changed = False
    for case in cases:
        if _failure_type(case) == "no_failure":
            continue
        case["classification"] = {
            "confidence": 0.1,
            "explanation": "reviewed, not a real failure",
            "failure_type": "no_failure",
        }
        expectation = case.get("expectation")
        if isinstance(expectation, dict):
            expectation["observed_failure"] = {"failure_type": "no_failure"}
            expectation["expectation_verdict"] = "no_failure_as_expected"
        changed = True
    if changed:
        _rewrite(root, run, cases)
    return changed


def _relabel_passes_as_failures(root: Path, run: str) -> bool:
    """"They were always broken." Backdating the damage so the delta reads as zero."""

    broke = _broke(root)
    cases = _cases(root, run)
    changed = False
    for case in cases:
        if case["case_id"] not in broke or _failure_type(case) != "no_failure":
            continue
        case["classification"] = {
            "confidence": 0.9,
            "explanation": "known issue",
            "failure_type": "reasoning",
        }
        expectation = case.get("expectation")
        if isinstance(expectation, dict):
            expectation["observed_failure"] = {"failure_type": "reasoning"}
            expectation["expectation_verdict"] = "unexpected_failure"
        changed = True
    if changed:
        _rewrite(root, run, cases)
    return changed


EDITS: dict[str, Callable[[Path, str], bool]] = {
    "delete the regressed cases": _delete_the_regressed_cases,
    "delete one regressed case": _delete_one_regressed_case,
    "run half the suite": _run_half_the_suite,
    "pad with easy passing cases": _pad_with_easy_passing_cases,
    "relabel failures as passes": _relabel_failures_as_passes,
    "relabel passes as failures": _relabel_passes_as_failures,
}

#: (edit, run) pairs the gate does not stop, with the reason. Recorded here so the boundary
#: is something a reader finds rather than something a user discovers in production. Both
#: entries are the same gap seen from its two sides, and neither is a defect in the gate's
#: conditions -- they are forged inputs, upstream of anything a gate over two runs can check.
DOCUMENTED_GAPS: dict[tuple[str, str], str] = {
    ("relabel failures as passes", "candidate"): (
        "run artifacts carry no content digest. A promoted dataset does -- stamped, and "
        "witnessed in governance/promotions.json -- but runs/, which is what the gate "
        "decides on, is unprotected, so an edited classification is indistinguishable from "
        "a real one. Closing this means digesting run results at write time"
    ),
    ("relabel passes as failures", "baseline"): (
        "the same missing digest, from the other side: backdating the failure into the "
        "baseline makes a real regression read as pre-existing, and pre-existing failures "
        "are correctly not a regression"
    ),
}

CASES = [(edit, run) for edit in EDITS for run in RUNS]


def test_the_untouched_workspace_actually_regresses(tmp_path: Path) -> None:
    # Without this, every assertion below could pass on a workspace with nothing wrong.
    root = _workspace(tmp_path)
    assert _broke(root), "the demo fixture stopped containing a regression"
    assert _gate(root) == BLOCKS


def test_the_attack_grid_covers_both_runs() -> None:
    # The property this file exists for: no edit is checked against one run only.
    for edit in EDITS:
        assert {run for name, run in CASES if name == edit} == set(RUNS), edit
    assert len(CASES) == len(EDITS) * len(RUNS)


@pytest.mark.parametrize(("edit", "run"), CASES, ids=[f"{e} in {r}" for e, r in CASES])
def test_hiding_the_evidence_never_turns_the_gate_green(
    edit: str, run: str, tmp_path: Path
) -> None:
    root = _workspace(tmp_path)
    assert _gate(root) == BLOCKS, "the workspace must start red"

    applied = EDITS[edit](root, run)
    if not applied:
        pytest.skip(f"'{edit}' has nothing to change in {run}")

    gap = DOCUMENTED_GAPS.get((edit, run))
    if gap is not None:
        assert _gate(root) == PASSES, (
            f"'{edit}' in {run} now blocks. That is an improvement -- delete its entry from "
            f"DOCUMENTED_GAPS. It was recorded as not covered because: {gap}"
        )
        return

    assert _gate(root) == BLOCKS, (
        f"an operator who did this -- {edit}, in the {run} run -- gets a green build over a "
        "real regression. The gate's job is to make the cheapest path to green be fixing it."
    )


def test_actually_fixing_the_candidate_turns_the_gate_green(tmp_path: Path) -> None:
    """The positive control. A gate that blocked unconditionally would pass everything above.

    This is the one edit that is allowed to turn red into green, because it is the only one
    that changes what the candidate *did* rather than what the workspace *records*.
    """

    root = _workspace(tmp_path)
    assert _gate(root) == BLOCKS

    broke = _broke(root)
    cases = _cases(root, "candidate")
    for case in cases:
        if case["case_id"] not in broke:
            continue
        baseline_case = next(c for c in _cases(root, "baseline") if c["case_id"] == case["case_id"])
        case["classification"] = baseline_case["classification"]
        case["expectation"] = baseline_case["expectation"]
        case["output"] = baseline_case["output"]
    _rewrite(root, "candidate", cases)

    assert _gate(root) == PASSES, "fixing every regressed case must clear the gate"
