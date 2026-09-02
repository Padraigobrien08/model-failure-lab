"""Black-box attacks on the gate, written from outside the engine.

Every other test in this suite knows something about how the tool works: it imports
`evaluate_gate_conditions`, or asserts on `dropped_baseline_failure_case_ids`, or compares
three surfaces to each other. That is how a gate that passed when a candidate deleted the
cases it broke survived four audits -- the surfaces all agreed, the conditions were all
covered, and nobody asked the question a user asks.

So this file imports nothing from the engine but `main`, touches no internal name, and
knows only what an operator knows: a workspace of runs, the CLI, and an exit code. Each
test corrupts the workspace the way a person under deadline pressure actually would, then
asserts CI still goes red.

The rule for adding here: describe the attack in the words the person would use ("I just
stopped running the flaky one"), never in the words the implementation uses. If a test
needs to name a field of a report artifact to express itself, it belongs in one of the
contract tests instead.
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


def _workspace(tmp_path: Path) -> Path:
    root = tmp_path / "ws"
    (root / "runs").mkdir(parents=True)
    for name in ("baseline", "candidate"):
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


def _broke(root: Path) -> set[str]:
    """Case ids the candidate fails and the baseline does not -- the actual regressions."""

    clean = {
        case["case_id"]
        for case in _cases(root, "baseline")
        if (case.get("classification") or {}).get("failure_type") == "no_failure"
    }
    return {
        case["case_id"]
        for case in _cases(root, "candidate")
        if case["case_id"] in clean
        and (case.get("classification") or {}).get("failure_type") != "no_failure"
    }


def _gate(root: Path) -> int:
    return main(["compare", "baseline", "candidate", "--gate", "--root", str(root)])


# --------------------------------------------------------------------------------------
# The attacks. Each takes a workspace with a real regression in it and tries to get a 0.
# --------------------------------------------------------------------------------------


def _stop_running_the_cases_that_broke(root: Path) -> None:
    """"Those four were noisy, so I took them out of the suite.\""""

    broke = _broke(root)
    _rewrite(root, "candidate", [c for c in _cases(root, "candidate") if c["case_id"] not in broke])


def _stop_running_one_case_that_broke(root: Path) -> None:
    """"Only one was flaky." One is enough: it is still a regression nobody will see."""

    victim = sorted(_broke(root))[0]
    _rewrite(root, "candidate", [c for c in _cases(root, "candidate") if c["case_id"] != victim])


def _keep_the_ids_but_run_half_the_suite(root: Path) -> None:
    """"The full suite is slow in CI, so the candidate job runs a subset.\""""

    cases = _cases(root, "candidate")
    _rewrite(root, "candidate", cases[: len(cases) // 2])


def _add_easy_cases_to_dilute_the_rate(root: Path) -> None:
    """"I added coverage." The failure *rate* falls; the same cases are still broken."""

    cases = _cases(root, "candidate")
    template = next(
        c for c in cases if (c.get("classification") or {}).get("failure_type") == "no_failure"
    )
    padding = []
    for index in range(24):
        clone = json.loads(json.dumps(template))
        clone["case_id"] = f"easy-{index}"
        if isinstance(clone.get("prompt"), dict):
            clone["prompt"]["id"] = f"easy-{index}"
        padding.append(clone)
    _rewrite(root, "candidate", cases + padding)


def _relabel_the_failures_as_passes(root: Path) -> None:
    """"The classifier was wrong about these." Editing the verdict, not the behaviour."""

    cases = _cases(root, "candidate")
    for case in cases:
        if (case.get("classification") or {}).get("failure_type") != "no_failure":
            case["classification"] = {
                "confidence": 0.1,
                "explanation": "reviewed, not a real failure",
                "failure_type": "no_failure",
            }
            expectation = case.get("expectation")
            if isinstance(expectation, dict):
                expectation["observed_failure"] = {"failure_type": "no_failure"}
                expectation["expectation_verdict"] = "no_failure_as_expected"
    _rewrite(root, "candidate", cases)


def _compare_the_candidate_against_itself(root: Path) -> None:
    """"Rerun the baseline job." A candidate compared to a copy of itself never regresses."""

    shutil.rmtree(root / "runs" / "baseline")
    shutil.copytree(root / "runs" / "candidate", root / "runs" / "baseline")
    path = root / "runs" / "baseline" / "results.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["run_id"] = "baseline"
    path.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")
    run_path = root / "runs" / "baseline" / "run.json"
    run = json.loads(run_path.read_text(encoding="utf-8"))
    run["run_id"] = "baseline"
    run_path.write_text(json.dumps(run, indent=1, sort_keys=True), encoding="utf-8")


#: Attacks that must not produce a green build.
MUST_BLOCK: tuple[tuple[str, Callable[[Path], None]], ...] = (
    ("delete every case the candidate broke", _stop_running_the_cases_that_broke),
    ("delete one case the candidate broke", _stop_running_one_case_that_broke),
    ("run only half the suite in the candidate job", _keep_the_ids_but_run_half_the_suite),
    # Padding was written as a documented gap and turned out to block: the verdict is
    # computed on shared cases, so cases the baseline never ran cannot dilute it. Promoted
    # here so the property is asserted rather than assumed.
    ("pad the candidate with easy passing cases", _add_easy_cases_to_dilute_the_rate),
)

#: Attacks the gate does *not* stop. Recorded here, with the reason, so the boundary is
#: something a reader can find rather than something a user discovers in production. Both
#: of these are outside what a gate over two runs can decide; neither is a defect in the
#: conditions. If either starts blocking, the test below says so.
KNOWN_UNBLOCKED: tuple[tuple[str, Callable[[Path], None], str], ...] = (
    (
        "edit the candidate's results to relabel its failures as passes",
        _relabel_the_failures_as_passes,
        "run artifacts carry no content digest. A promoted dataset does -- stamped, and "
        "witnessed in governance/promotions.json -- but runs/, which is what the gate "
        "actually decides on, is unprotected, so an edited classification is "
        "indistinguishable from a real one. Closing this means digesting run results at "
        "write time, which is a larger change than the gate",
    ),
    (
        "compare the candidate against a copy of itself",
        _compare_the_candidate_against_itself,
        "two identical runs genuinely have no delta; catching this needs a known-good "
        "baseline, which `failure-lab baselines set` records and the gate does not consult",
    ),
)


def test_the_untouched_workspace_actually_regresses(tmp_path: Path) -> None:
    # Without this, every assertion below could pass on a workspace with nothing wrong.
    root = _workspace(tmp_path)
    assert _broke(root), "the demo fixture stopped containing a regression"
    assert _gate(root) == BLOCKS


@pytest.mark.parametrize(("name", "attack"), MUST_BLOCK, ids=[n for n, _ in MUST_BLOCK])
def test_the_gate_still_blocks(name: str, attack: Callable[[Path], None], tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    assert _gate(root) == BLOCKS, "the workspace must start red"
    attack(root)
    assert _gate(root) == BLOCKS, (
        f"an operator who did this -- {name} -- gets a green build over a real regression. "
        "The gate's job is to make the cheapest path to green be fixing the regression."
    )


@pytest.mark.parametrize(
    ("name", "attack", "why"), KNOWN_UNBLOCKED, ids=[n for n, _, _ in KNOWN_UNBLOCKED]
)
def test_the_documented_gaps_are_still_exactly_these(
    name: str, attack: Callable[[Path], None], why: str, tmp_path: Path
) -> None:
    """Pin the boundary in both directions.

    If one of these starts blocking, that is good news and this test says so rather than
    failing silently into a stronger guarantee nobody wrote down.
    """

    root = _workspace(tmp_path)
    attack(root)
    assert _gate(root) == PASSES, (
        f"'{name}' now blocks. That is an improvement -- move it into MUST_BLOCK. "
        f"It was documented as not covered because: {why}"
    )
