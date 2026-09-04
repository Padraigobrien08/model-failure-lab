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

#: An operator edits *some* of the artifacts, not exactly one. The first version of this
#: grid made the run axis a pair, and the attack that got past it was an edit applied to
#: both: delete the case from the baseline and the candidate, and there is no
#: `baseline_only`, no `candidate_only`, and nothing in the comparison that could know a
#: test used to exist. Subsets, not elements -- so "both" is a cell rather than a discovery.
RUNS = ("baseline", "candidate")
RUN_TARGETS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("baseline", ("baseline",)),
    ("candidate", ("candidate",)),
    ("both runs", ("baseline", "candidate")),
)

#: The promoted pack is a third target and not a run at all. The product's sentence is that
#: a harvested regression becomes "a permanent test you can re-run forever", which is a
#: claim about `datasets/`, and no product over `runs/` reaches it.
PROMOTED_DATASET_ID = "permanent-regressions"


def _workspace(tmp_path: Path) -> Path:
    root = tmp_path / "ws"
    (root / "runs").mkdir(parents=True)
    for name in RUNS:
        shutil.copytree(DEMO_RUNS / name, root / "runs" / name)
    return root


def _promote_the_regressions(root: Path) -> None:
    """Run the loop the README sells, so the pack exists to be attacked."""

    assert main(["compare", "baseline", "candidate", "--root", str(root)]) == 0
    assert main(["index", "rebuild", "--root", str(root)]) == 0
    draft = "datasets/harvested/draft.json"
    assert (
        main(
            [
                "harvest",
                "--comparison",
                "compare_8ba8496a_to_dda18a0e_66320e7c",
                "--out",
                draft,
                "--root",
                str(root),
            ]
        )
        == 0
    )
    assert (
        main(
            ["dataset", "promote", draft, "--dataset-id", PROMOTED_DATASET_ID, "--root", str(root)]
        )
        == 0
    )


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
# The edits. Each takes a workspace and one run, and returns False when there is nothing in
# that run for it to change. `_across` lifts them to a set of runs, so "both" costs nothing
# to express and cannot be left out of the grid by an author thinking one run at a time.
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


def _across(edit: Callable[[Path, str], bool]) -> Callable[[Path, tuple[str, ...]], bool]:
    """Apply a single-run edit to every run in the target, reporting whether any took."""

    def apply(root: Path, runs: tuple[str, ...]) -> bool:
        # `any(...)` over a generator would short-circuit and leave the second run untouched.
        return any([edit(root, run) for run in runs])

    return apply


def _stop_running_the_regressions_everywhere(root: Path) -> None:
    """Remove the regressed cases from both runs -- what re-running a shrunken suite gives.

    The dataset edits below must do this too, or they assert nothing: the workspace is
    already red because the regression is still in the runs, so "still blocks" would hold
    no matter what happened to the pack. Removing the run-level evidence first is what
    leaves the promotion ledger as the only thing that can object -- which is the scenario,
    and the only shape in which these two cells can fail.
    """

    broke = _broke(root)
    for run in RUNS:
        _rewrite(root, run, [c for c in _cases(root, run) if c["case_id"] not in broke])


def _retire_the_tests_and_rerun(root: Path, _runs: tuple[str, ...]) -> bool:
    """"We retired those tests." Empty the permanent pack, then re-run both sides."""

    import json as _json

    path = root / "datasets" / f"{PROMOTED_DATASET_ID}.json"
    if not path.is_file():
        return False
    payload = _json.loads(path.read_text(encoding="utf-8"))
    payload["cases"] = []
    payload["metadata"].pop("integrity", None)
    payload.pop("lifecycle", None)
    path.write_text(_json.dumps(payload, indent=2), encoding="utf-8")
    _stop_running_the_regressions_everywhere(root)
    return True


def _delete_the_pack_and_rerun(root: Path, _runs: tuple[str, ...]) -> bool:
    """`rm datasets/<id>.json`, then re-run.

    The simplest attack on the two-witness scheme and the one it had nothing to say about:
    every other integrity check starts from a file that still exists, so deleting the pack
    outright left `index validate` reporting `ok`.
    """

    path = root / "datasets" / f"{PROMOTED_DATASET_ID}.json"
    if not path.is_file():
        return False
    path.unlink()
    _stop_running_the_regressions_everywhere(root)
    return True


RUN_EDITS: dict[str, Callable[[Path, str], bool]] = {
    "delete the regressed cases": _delete_the_regressed_cases,
    "delete one regressed case": _delete_one_regressed_case,
    "run half the suite": _run_half_the_suite,
    "pad with easy passing cases": _pad_with_easy_passing_cases,
    "relabel failures as passes": _relabel_failures_as_passes,
    "relabel passes as failures": _relabel_passes_as_failures,
}

#: Edits to the promoted pack rather than to a run. Same grid, a target that is not a run.
DATASET_EDITS: dict[str, Callable[[Path, tuple[str, ...]], bool]] = {
    "retire the tests and re-run": _retire_the_tests_and_rerun,
    "delete the pack and re-run": _delete_the_pack_and_rerun,
}

#: (edit, target) pairs the gate does not stop, with the reason. Recorded here so the
#: boundary is something a reader finds rather than something a user discovers in
#: production. All of these are forged run artifacts, upstream of anything a gate can check.
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
    ("relabel failures as passes", "both runs"): (
        "relabelling both runs is the candidate-side forgery plus a no-op on a baseline "
        "that fails nothing -- same missing run-artifact digest"
    ),
    ("relabel passes as failures", "both runs"): (
        "found by widening the grid to subsets: marking the regressed cases as failing in "
        "*both* runs makes them read as pre-existing, and pre-existing failures are "
        "correctly not a regression. Same missing run-artifact digest as the other three"
    ),
}

#: The grid: every edit against every target. Run edits are lifted across their target's
#: runs; dataset edits ignore the run set and act on the promoted pack. Built as a product
#: so a target added here is exercised by every edit without anybody remembering to.
CASES: list[tuple[str, str]] = [
    *((edit, target) for edit in RUN_EDITS for target, _ in RUN_TARGETS),
    *((edit, "promoted pack") for edit in DATASET_EDITS),
]
TARGET_RUNS = dict(RUN_TARGETS)


def _apply(edit: str, target: str, root: Path) -> bool:
    if edit in DATASET_EDITS:
        return DATASET_EDITS[edit](root, ())
    return _across(RUN_EDITS[edit])(root, TARGET_RUNS[target])


def test_the_untouched_workspace_actually_regresses(tmp_path: Path) -> None:
    # Without this, every assertion below could pass on a workspace with nothing wrong.
    root = _workspace(tmp_path)
    assert _broke(root), "the demo fixture stopped containing a regression"
    assert _gate(root) == BLOCKS


def test_the_attack_grid_covers_every_target() -> None:
    """The property this file exists for, and the one it failed twice.

    First it enumerated candidate-side edits only. Then it became a product over the two
    runs -- and an edit applied to *both* was still unreachable, which is exactly how the
    promoted pack got deleted with the gate green. The grid is asserted, not trusted.
    """

    targets = {target for target, _ in RUN_TARGETS}
    for edit in RUN_EDITS:
        assert {t for e, t in CASES if e == edit} == targets, edit
    for edit in DATASET_EDITS:
        assert ("promoted pack" in {t for e, t in CASES if e == edit}), edit
    assert len(CASES) == len(RUN_EDITS) * len(RUN_TARGETS) + len(DATASET_EDITS)
    # "both" has to be a target, not an afterthought: it is the one that got past the grid.
    assert ("baseline", "candidate") in {runs for _, runs in RUN_TARGETS}


@pytest.mark.parametrize(("edit", "target"), CASES, ids=[f"{e} in {t}" for e, t in CASES])
def test_hiding_the_evidence_never_turns_the_gate_green(
    edit: str, target: str, tmp_path: Path
) -> None:
    root = _workspace(tmp_path)
    # Every scenario promotes the regressions first: that is the loop the README sells, and
    # the dataset attacks have nothing to aim at without it.
    _promote_the_regressions(root)
    assert _gate(root) == BLOCKS, "the workspace must start red"

    if not _apply(edit, target, root):
        pytest.skip(f"'{edit}' has nothing to change in {target}")

    gap = DOCUMENTED_GAPS.get((edit, target))
    if gap is not None:
        assert _gate(root) == PASSES, (
            f"'{edit}' in {target} now blocks. That is an improvement -- delete its entry "
            f"from DOCUMENTED_GAPS. It was recorded as not covered because: {gap}"
        )
        return

    assert _gate(root) == BLOCKS, (
        f"an operator who did this -- {edit}, in {target} -- gets a green build over a real "
        "regression. The gate's job is to make the cheapest path to green be fixing it."
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
