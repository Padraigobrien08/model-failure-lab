"""`scripts/query_bridge.py` payloads are a committed contract, not an implicit one.

The operator console's typed validators live in TypeScript and are exercised only against
hand-written fixtures declared to follow "what each validator actually reads". That makes
the contract circular: when the Python producer renamed or dropped a field, every vitest
test stayed green. It happened -- the `gate` handler hand-picked its response fields and
silently omitted `policy_source` / `waiver_source`, so the gate screen reported
"built-in defaults / waivers: none" while a committed `governance/policy.yml` was in force.

`tests/fixtures/bridge/*.json` is now the single shared contract, pinned from both sides:

* this test proves the **producer** still emits exactly those payloads, and
* `frontend/src/lib/artifacts/__tests__/bridgeContract.test.ts` proves the **consumer**
  validators accept them.

A rename therefore fails here, and a field the console needs but the bridge stopped
sending fails there. Regenerate deliberately with:

    FAILURE_LAB_REGENERATE_BRIDGE_FIXTURES=1 python3 -m pytest \\
        tests/unit/test_bridge_payload_contract.py

and review the diff -- it is the console's contract changing.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from model_failure_lab.datasets import evolve_dataset_family
from model_failure_lab.governance import upsert_baseline
from model_failure_lab.harvest import harvest_artifact_cases
from model_failure_lab.index import QueryFilters
from model_failure_lab.testing import materialize_insight_fixture

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures" / "bridge"
BRIDGE = PROJECT_ROOT / "scripts" / "query_bridge.py"
WORKSPACE_PLACEHOLDER = "{WORKSPACE}"


# A regression comparison from the insight fixture, used to seed a harvested draft and an
# evolved dataset family so the families/drafts endpoints carry real rows instead of [].
SEED_COMPARISON_ID = "compare_66f669a9_to_df4f8650_1094b97e"
SEED_FAMILY_ID = "insight-fixture-regressions"
FIXED_TIMESTAMP = datetime(2026, 4, 2, 9, 30, tzinfo=timezone.utc)
SEED_BASELINE_RUN_ID = (
    "20260402_090000_000000_insight_fixture_v1_insight_fixture_v1"
    "_insight_fixture_classifier_v1_baseline_model_seed_13_9cd76f23"
)

# One entry per read-only bridge endpoint, including the id-taking ones.
#
# This list used to stop at the navigation endpoints and defer the rest to "the console's
# own page tests" -- which feed `factories.ts`, the mirror-of-the-reader fixtures this file
# exists to escape. That deferral re-asserted the circularity for five endpoints.
#
# `comparison-detail` and `run-detail` are absent for a different reason: they are not
# produced by this bridge at all. The vite middleware composes them in TypeScript straight
# from `run.json` / `results.json` / `report_details.json`, so the contract that can drift
# there is the Python *writer* against that reader.
# `frontend/server/__tests__/artifactBridge.test.ts` pins both sides of it by running the
# console's own validators over real bridge output.
#
# `cluster-detail` needs a cluster id discovered from a built index, which is not stable
# enough to pin as a byte-for-byte golden file; the console's explorer test covers its shape.
BRIDGE_COMMANDS: dict[str, list[str]] = {
    "overview": ["overview"],
    "runs": ["runs"],
    "comparisons": ["comparisons"],
    "gate": ["gate"],
    "dataset-families": ["dataset-families"],
    "dataset-drafts": ["dataset-drafts"],
    "baselines": ["baselines"],
    "dataset-versions": ["dataset-versions", "--dataset-family", SEED_FAMILY_ID],
    "history": ["history", "--family-id", SEED_FAMILY_ID],
}


def _build_workspace(root: Path) -> Path:
    """Deterministic workspace exercising every endpoint's non-empty shape."""

    workspace = materialize_insight_fixture(root)
    artifact_root = Path(workspace.root)

    # A harvested draft awaiting promotion -> `dataset-drafts` has a row.
    harvest_artifact_cases(
        filters=QueryFilters(report_id=SEED_COMPARISON_ID, delta="regression", limit=200),
        output_path="datasets/harvested/contract-draft.json",
        root=artifact_root,
        comparison_id=SEED_COMPARISON_ID,
        mode="deltas",
        now=FIXED_TIMESTAMP,
    )
    # An evolved family with one immutable version -> `dataset-families` has a row.
    evolve_dataset_family(
        SEED_FAMILY_ID,
        comparison_id=SEED_COMPARISON_ID,
        root=artifact_root,
        now=FIXED_TIMESTAMP,
    )
    # A registered baseline -> `baselines` has a row.
    upsert_baseline(
        "contract-baseline",
        run_id=SEED_BASELINE_RUN_ID,
        root=artifact_root,
        # Pinned clock: the registry timestamp is the only wall-clock value in any bridge
        # payload, and the contract has to be byte-stable.
        now=FIXED_TIMESTAMP,
    )
    return artifact_root


def _invoke_bridge(command: list[str], *, root: Path) -> dict | list:
    completed = subprocess.run(
        [sys.executable, str(BRIDGE), *command, "--root", str(root)],
        capture_output=True,
        text=True,
        check=True,
        cwd=PROJECT_ROOT,
        env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")},
    )
    # The workspace path is the only machine-specific value in any payload; everything
    # else must be byte-stable or the artifact contract is not deterministic.
    return json.loads(completed.stdout.replace(str(root), WORKSPACE_PLACEHOLDER))


def _serialize(payload: dict | list) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


@pytest.fixture(scope="module")
def bridge_payloads(tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict | list]:
    root = _build_workspace(tmp_path_factory.mktemp("bridge-contract") / "workspace")
    payloads = {
        name: _invoke_bridge(command, root=root) for name, command in BRIDGE_COMMANDS.items()
    }
    if os.environ.get("FAILURE_LAB_REGENERATE_BRIDGE_FIXTURES") == "1":
        FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
        for name, payload in payloads.items():
            (FIXTURE_DIR / f"{name}.json").write_text(_serialize(payload), encoding="utf-8")
    return payloads


@pytest.mark.parametrize("name", sorted(BRIDGE_COMMANDS))
def test_bridge_payload_matches_the_committed_contract(
    name: str,
    bridge_payloads: dict[str, dict | list],
) -> None:
    golden_path = FIXTURE_DIR / f"{name}.json"
    assert golden_path.is_file(), (
        f"missing golden payload for `{name}`; regenerate with "
        "FAILURE_LAB_REGENERATE_BRIDGE_FIXTURES=1"
    )
    assert _serialize(bridge_payloads[name]) == golden_path.read_text(encoding="utf-8"), (
        f"`query_bridge.py {name}` no longer matches tests/fixtures/bridge/{name}.json. "
        "If the change is intended, regenerate the fixtures and update the console's "
        "validators in the same commit."
    )


def test_every_endpoint_returns_a_non_empty_shape(
    bridge_payloads: dict[str, dict | list],
) -> None:
    # An all-empty fixture would make the contract vacuous: `[]` validates against almost
    # any row schema, so drift inside a row would go unnoticed.
    assert bridge_payloads["runs"], "runs endpoint must return rows"
    assert bridge_payloads["comparisons"], "comparisons endpoint must return rows"
    for name, key in (
        ("gate", "rows"),
        ("dataset-families", "families"),
        ("dataset-drafts", "drafts"),
        ("baselines", "baselines"),
    ):
        payload = bridge_payloads[name]
        assert isinstance(payload, dict)
        assert payload[key], f"{name} endpoint must return at least one {key} row"


def test_gate_payload_carries_the_policy_provenance(
    bridge_payloads: dict[str, dict | list],
) -> None:
    # The specific regression this contract exists to prevent: the console cannot report
    # which policy and waivers CI used unless the bridge sends them.
    gate = bridge_payloads["gate"]
    assert isinstance(gate, dict)
    assert "policy_source" in gate
    assert "waiver_source" in gate
    for row in gate["rows"]:
        assert "block_reason" in row, "each gate decision must explain why it blocks"
