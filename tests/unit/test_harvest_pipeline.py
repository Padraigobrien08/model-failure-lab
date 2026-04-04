from __future__ import annotations

from pathlib import Path

from model_failure_lab.cli import main
from model_failure_lab.datasets import load_dataset
from model_failure_lab.harvest import harvest_artifact_cases
from model_failure_lab.index import QueryFilters
from model_failure_lab.storage import read_json
from model_failure_lab.testing import materialize_insight_fixture


def test_harvest_artifact_cases_builds_draft_dataset_from_query_filters(
    tmp_path: Path,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")

    summary = harvest_artifact_cases(
        filters=QueryFilters(failure_type="hallucination", last_n=4, limit=10),
        output_path="datasets/harvested/hallucination_recent.json",
        root=workspace.root,
    )

    assert summary.mode == "cases"
    assert summary.output_path.exists()
    assert summary.dataset.dataset_id == "hallucination-recent"
    assert summary.dataset.lifecycle == "draft"
    assert summary.dataset.source["type"] == "artifact_harvest"
    assert summary.dataset.source["mode"] == "cases"
    assert summary.dataset.source["filters"] == {
        "failure_type": "hallucination",
        "model": None,
        "dataset": None,
        "run_id": None,
        "prompt_id": None,
        "report_id": None,
        "baseline_run_id": None,
        "candidate_run_id": None,
        "delta": None,
        "last_n": 4,
        "since": None,
        "until": None,
        "limit": 10,
    }
    assert summary.selected_case_count == len(summary.dataset.cases)
    assert summary.selected_case_count > 0

    harvested_case = summary.dataset.cases[0]
    harvest_metadata = harvested_case.metadata["harvest"]
    assert harvested_case.expectations is not None
    assert "harvested" in harvested_case.tags
    assert harvest_metadata["source_kind"] == "run_case"
    assert harvest_metadata["source_run_id"]
    assert harvest_metadata["source_case_id"]
    assert harvest_metadata["source_prompt_id"]
    assert harvest_metadata["normalized_prompt_hash"]
    assert harvest_metadata["draft_case_id"] == harvested_case.id

    loaded = load_dataset(summary.output_path)
    assert loaded.created_at == summary.dataset.created_at
    assert loaded.lifecycle == "draft"
    assert loaded.source["type"] == "artifact_harvest"


def test_harvest_artifact_cases_builds_delta_pack_from_comparison_filters(
    tmp_path: Path,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison = workspace.comparisons[0]

    summary = harvest_artifact_cases(
        filters=QueryFilters(delta="regression", limit=10),
        comparison_id=comparison.report_id,
        output_path="datasets/harvested/regressions.json",
        root=workspace.root,
    )

    assert summary.mode == "deltas"
    assert summary.selected_case_count == len(summary.dataset.cases)
    assert summary.selected_case_count >= 1

    harvested_case = summary.dataset.cases[0]
    harvest_metadata = harvested_case.metadata["harvest"]
    assert "harvested" in harvested_case.tags
    assert "delta-regression" in harvested_case.tags
    assert harvest_metadata["source_kind"] == "comparison_delta"
    assert harvest_metadata["source_report_id"] == comparison.report_id
    assert harvest_metadata["baseline_run_id"]
    assert harvest_metadata["candidate_run_id"]
    assert harvest_metadata["delta_kind"] == "regression"
    assert harvest_metadata["transition_type"] == "no_failure_to_failure"
    assert harvest_metadata["source_case_id"]
    assert harvested_case.expectations is not None

    payload = read_json(summary.output_path)
    assert payload["lifecycle"] == "draft"
    assert payload["source"]["filters"]["report_id"] == comparison.report_id
    assert payload["source"]["filters"]["delta"] == "regression"


def test_cli_harvest_command_writes_draft_dataset_pack(tmp_path: Path, capsys) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison = workspace.comparisons[0]
    output_path = workspace.root / "datasets" / "harvested" / "comparison_regressions.json"

    exit_code = main(
        [
            "harvest",
            "--root",
            str(workspace.root),
            "--comparison",
            comparison.report_id,
            "--delta",
            "regression",
            "--out",
            str(output_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Failure Lab Harvest" in captured.out
    assert "Lifecycle: draft" in captured.out
    assert output_path.exists()

    harvested = load_dataset(output_path)
    assert harvested.lifecycle == "draft"
    assert harvested.source["type"] == "artifact_harvest"
    assert harvested.source["filters"]["report_id"] == comparison.report_id
