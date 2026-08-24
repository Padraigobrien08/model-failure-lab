"""`index validate` re-reads source artifacts through the strict contract checks.

The CLAUDE.md contract promises `failure-lab index validate` *validates contracts*.
It must therefore fail closed when a source run/report/comparison artifact violates
the contract, not merely confirm that the derived index tables exist.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from model_failure_lab.index.contracts import validate_artifact_contracts

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_RUNS = PROJECT_ROOT / "examples" / "regression_demo" / "runs"


def _seed_runs(root: Path) -> None:
    runs = root / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    for name in ("baseline", "candidate"):
        shutil.copytree(DEMO_RUNS / name, runs / name)


def test_validate_passes_on_wellformed_artifacts(tmp_path: Path) -> None:
    _seed_runs(tmp_path)

    result = validate_artifact_contracts(root=tmp_path)

    assert result.ok
    assert result.errors == ()


def test_validate_fails_closed_on_contract_violation(tmp_path: Path) -> None:
    _seed_runs(tmp_path)
    run_json = next((tmp_path / "runs").glob("*/run.json"))
    payload = json.loads(run_json.read_text(encoding="utf-8"))
    del payload["dataset"]  # a required field on the Run contract
    run_json.write_text(json.dumps(payload), encoding="utf-8")

    result = validate_artifact_contracts(root=tmp_path)

    assert not result.ok
    assert any("contract violation" in error for error in result.errors)
