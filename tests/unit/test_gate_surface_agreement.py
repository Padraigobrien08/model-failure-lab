"""Every gate surface must reach the same PASS/FAIL on the same artifacts.

`compare --gate`, `failure-lab regressions gate` and the operator console's read-only
`gate` endpoint are three entry points to one decision. They previously were not: the
compare gate applied five checks (incompatible runs, regression verdict, execution-success
drop, classification-coverage drop, cases the candidate stopped running) while the governance
gate applied only the verdict. A candidate that deleted the cases it broke, or two runs
that were not comparable at all, therefore failed CI and showed a green PASS in the
console -- exactly the contradiction the console is supposed to make impossible.

These tests build the two adversarial workspaces that exposed it and assert the surfaces
agree. `evaluate_gate_conditions` is the single implementation both now call, so a future
change that re-forks the contract fails here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from model_failure_lab.cli import main
from model_failure_lab.governance.gates import evaluate_regression_gate

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_RUNS = PROJECT_ROOT / "examples" / "regression_demo" / "runs"


def _copy_run(source: Path, destination: Path, *, run_id: str) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    run = json.loads((source / "run.json").read_text(encoding="utf-8"))
    results = json.loads((source / "results.json").read_text(encoding="utf-8"))
    run["run_id"] = run_id
    results["run_id"] = run_id
    (destination / "run.json").write_text(json.dumps(run, indent=1, sort_keys=True))
    (destination / "results.json").write_text(json.dumps(results, indent=1, sort_keys=True))


def _workspace_dropping_failing_cases(root: Path) -> Path:
    """Baseline fails 4 of 8 cases; the candidate simply deletes those 4."""

    _copy_run(DEMO_RUNS / "candidate", root / "runs" / "base", run_id="base")
    _copy_run(DEMO_RUNS / "candidate", root / "runs" / "cand", run_id="cand")

    results_path = root / "runs" / "cand" / "results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    kept = [
        case
        for case in results["cases"]
        if (case.get("classification") or {}).get("failure_type") == "no_failure"
    ]
    assert len(kept) < len(results["cases"]), "fixture must actually drop failing cases"
    results["cases"] = kept
    results["total_cases"] = len(kept)
    results_path.write_text(json.dumps(results, indent=1, sort_keys=True))
    return root


def _workspace_dropping_the_cases_the_candidate_broke(root: Path) -> Path:
    """The other direction, and the one that matters.

    The fixture above deletes cases the *baseline* was already failing. A real regression
    is the opposite: the baseline passes a case and the candidate breaks it. Hiding *that*
    means deleting a case the baseline passed -- which for four audits was not checked by
    anything, because the only fixture exercising dropped cases used a baseline that fails
    four of eight, so the covered direction always fired first.

    Baseline = the demo baseline, which fails nothing. Candidate = the demo candidate with
    the four cases it broke removed. Every metric the gate reads is computed on the four
    shared cases, all of which are clean, so without a check on dropped cases this reads as
    `Gate: PASS (signal verdict: neutral)`.
    """

    _copy_run(DEMO_RUNS / "baseline", root / "runs" / "base", run_id="base")
    _copy_run(DEMO_RUNS / "candidate", root / "runs" / "cand", run_id="cand")

    baseline_results = json.loads(
        (root / "runs" / "base" / "results.json").read_text(encoding="utf-8")
    )
    assert all(
        (case.get("classification") or {}).get("failure_type") == "no_failure"
        for case in baseline_results["cases"]
    ), "fixture requires a baseline that fails nothing, or it tests the other direction"

    results_path = root / "runs" / "cand" / "results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    broke = {
        case["case_id"]
        for case in results["cases"]
        if (case.get("classification") or {}).get("failure_type") != "no_failure"
    }
    assert broke, "fixture must have cases the candidate broke"
    results["cases"] = [case for case in results["cases"] if case["case_id"] not in broke]
    results["total_cases"] = len(results["cases"])
    results_path.write_text(json.dumps(results, indent=1, sort_keys=True))
    return root


def _workspace_with_incompatible_runs(root: Path) -> Path:
    """Two runs over entirely different datasets, so nothing is comparable."""

    _copy_run(DEMO_RUNS / "baseline", root / "runs" / "base", run_id="base")
    _copy_run(DEMO_RUNS / "baseline", root / "runs" / "cand", run_id="cand")

    run_path = root / "runs" / "cand" / "run.json"
    run = json.loads(run_path.read_text(encoding="utf-8"))
    run["dataset"] = "totally-different-v1"
    run_path.write_text(json.dumps(run, indent=1, sort_keys=True))

    results_path = root / "runs" / "cand" / "results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    results["dataset_id"] = "totally-different-v1"
    for index, case in enumerate(results["cases"]):
        case["case_id"] = f"other-{index}"
        case["prompt"]["id"] = f"other-{index}"
    results_path.write_text(json.dumps(results, indent=1, sort_keys=True))
    return root


def _compare_gate_exit_code(root: Path) -> int:
    return main(["compare", "base", "cand", "--gate", "--root", str(root)])


def _governance_gate(root: Path):
    main(["index", "rebuild", "--root", str(root)])
    return evaluate_regression_gate(root=root)


@pytest.mark.parametrize(
    ("build_workspace", "expected_reason_fragment"),
    [
        (
            _workspace_dropping_failing_cases,
            "did not run 4 case(s) the baseline ran (4 already failing in the baseline)",
        ),
        (
            _workspace_dropping_the_cases_the_candidate_broke,
            "did not run 4 case(s) the baseline ran",
        ),
        (_workspace_with_incompatible_runs, "runs are not comparable"),
    ],
    ids=["dropped_failing_cases", "dropped_the_cases_it_broke", "incompatible_runs"],
)
def test_every_gate_surface_blocks_the_same_comparison(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    build_workspace,
    expected_reason_fragment: str,
) -> None:
    root = build_workspace(tmp_path / "workspace")

    # Surface 1: `compare --gate` -- the CI contract the bundled Action consumes.
    assert _compare_gate_exit_code(root) == 1
    assert expected_reason_fragment in capsys.readouterr().out

    # Surfaces 2 and 3: `regressions gate` and the console's `gate` endpoint both read
    # `evaluate_regression_gate`, so one assertion covers the pair.
    result = _governance_gate(root)
    assert result.blocked is True, "governance gate must not pass what CI fails"
    assert len(result.rows) == 1
    row = result.rows[0]
    assert row.blocked is True
    assert row.block_reason is not None
    assert expected_reason_fragment in row.block_reason
    # The reason travels into the payload the console renders, so the UI can say what CI
    # said instead of inventing its own explanation.
    assert expected_reason_fragment in str(row.to_payload()["block_reason"])


def test_every_gate_surface_passes_a_genuinely_clean_comparison(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Guard against the obvious over-correction: comparing a run against itself changes
    # nothing, and must stay green on every surface.
    root = tmp_path / "workspace"
    _copy_run(DEMO_RUNS / "baseline", root / "runs" / "base", run_id="base")
    _copy_run(DEMO_RUNS / "baseline", root / "runs" / "cand", run_id="cand")

    assert _compare_gate_exit_code(root) == 0
    assert "Gate: PASS" in capsys.readouterr().out

    result = _governance_gate(root)
    assert result.blocked is False
    assert [row.block_reason for row in result.rows] == [None]
