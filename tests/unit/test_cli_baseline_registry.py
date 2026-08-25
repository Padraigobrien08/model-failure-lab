"""The baseline registry is load-bearing: `set` validates, `compare` can consume it."""

from __future__ import annotations

import shutil
from pathlib import Path

from model_failure_lab.cli import main

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_RUNS = PROJECT_ROOT / "examples" / "regression_demo" / "runs"


def _seed_runs(root: Path) -> None:
    runs = root / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    for name in ("baseline", "candidate"):
        shutil.copytree(DEMO_RUNS / name, runs / name)


def test_baselines_set_rejects_unknown_run(tmp_path: Path, capsys) -> None:
    _seed_runs(tmp_path)
    exit_code = main(
        ["baselines", "--root", str(tmp_path), "set", "--name", "x", "--run", "nope"]
    )
    assert exit_code == 1
    # The old assertion matched the raw OS "No such file" text. The message now names the
    # run and what to do about it, which is the contract worth pinning.
    error = capsys.readouterr().err
    assert "'nope' is not saved in this workspace" in error
    assert "--root" in error


def test_baselines_set_backfills_model_and_dataset_from_run(tmp_path: Path, capsys) -> None:
    _seed_runs(tmp_path)
    exit_code = main(
        ["baselines", "--root", str(tmp_path), "set", "--name", "main", "--run", "baseline"]
    )
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "support-assistant-v1" in output  # model backfilled from the run
    assert "support-regression-demo-v1" in output  # dataset backfilled from the run


def test_compare_resolves_baseline_from_registry(tmp_path: Path, capsys) -> None:
    _seed_runs(tmp_path)
    main(["baselines", "--root", str(tmp_path), "set", "--name", "main", "--run", "baseline"])
    capsys.readouterr()

    exit_code = main(
        ["compare", "--root", str(tmp_path), "--baseline-name", "main", "candidate", "--gate"]
    )
    output = capsys.readouterr().out
    assert exit_code == 1  # the demo candidate regresses
    assert "Gate: FAIL (signal verdict: regression)" in output


def test_compare_rejects_unknown_baseline_name(tmp_path: Path, capsys) -> None:
    _seed_runs(tmp_path)
    exit_code = main(
        ["compare", "--root", str(tmp_path), "--baseline-name", "ghost", "candidate"]
    )
    assert exit_code == 1
    assert "baseline name not found in registry" in capsys.readouterr().err


def test_compare_rejects_both_positional_and_name(tmp_path: Path, capsys) -> None:
    _seed_runs(tmp_path)
    main(["baselines", "--root", str(tmp_path), "set", "--name", "main", "--run", "baseline"])
    capsys.readouterr()

    exit_code = main(
        ["compare", "--root", str(tmp_path), "--baseline-name", "main", "baseline", "candidate"]
    )
    assert exit_code == 1
    assert "not both" in capsys.readouterr().err


def test_legacy_entry_without_timestamp_yields_null_not_empty_string(tmp_path: Path) -> None:
    """A hand-edited/legacy registry row without `updated_at` must serialize as
    null, not "" — the console's baselines validator rejects empty strings, so an
    empty string would crash the whole panel on one bad row."""
    from model_failure_lab.governance.baselines import list_baselines

    registry = tmp_path / ".failure_lab" / "baseline_registry.json"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        '{"baselines": [{"name": "legacy", "run_id": "run-x"}]}',
        encoding="utf-8",
    )

    entry = list_baselines(root=tmp_path)[0]

    assert entry.updated_at is None
    assert entry.to_payload()["updated_at"] is None
