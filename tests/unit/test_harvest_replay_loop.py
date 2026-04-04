from __future__ import annotations

import json
from pathlib import Path

from model_failure_lab.cli import main
from model_failure_lab.index import list_run_inventory
from model_failure_lab.testing import materialize_insight_fixture
from model_failure_lab.testing.insight_fixture import (
    FIXTURE_ADAPTER_ID,
    FIXTURE_CLASSIFIER_ID,
)


def test_harvested_dataset_replays_through_compare_and_insight(
    tmp_path: Path,
    capsys,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    source_comparison = workspace.comparisons[0]
    draft_path = workspace.root / "datasets" / "harvested" / "regression-pack.json"
    curated_dataset_id = "fixture-regression-pack-v1"

    harvest_exit = main(
        [
            "harvest",
            "--root",
            str(workspace.root),
            "--comparison",
            source_comparison.report_id,
            "--delta",
            "regression",
            "--out",
            str(draft_path),
        ]
    )
    harvest_output = capsys.readouterr().out

    review_exit = main(["dataset", "review", str(draft_path)])
    review_output = capsys.readouterr().out

    promote_exit = main(
        [
            "dataset",
            "promote",
            str(draft_path),
            "--dataset-id",
            curated_dataset_id,
            "--root",
            str(workspace.root),
        ]
    )
    promote_output = capsys.readouterr().out

    list_exit = main(["datasets", "list", "--root", str(workspace.root)])
    list_output = capsys.readouterr().out

    assert harvest_exit == 0
    assert "Failure Lab Harvest" in harvest_output
    assert "Mode: deltas" in harvest_output
    assert review_exit == 0
    assert "Failure Lab Dataset Review" in review_output
    assert promote_exit == 0
    assert "Failure Lab Dataset Promotion" in promote_output
    assert list_exit == 0
    assert curated_dataset_id in list_output

    rerun_ids: dict[str, str] = {}
    for model_name in ("candidate-model", "stable-model"):
        run_exit = main(
            [
                "run",
                "--dataset",
                curated_dataset_id,
                "--model",
                f"{FIXTURE_ADAPTER_ID}:{model_name}",
                "--classifier",
                FIXTURE_CLASSIFIER_ID,
                "--root",
                str(workspace.root),
            ]
        )
        run_output = capsys.readouterr().out
        assert run_exit == 0
        assert "Failure Lab Run" in run_output

    for row in list_run_inventory(root=workspace.root):
        if row["dataset"] == curated_dataset_id and row["model"] in {
            "candidate-model",
            "stable-model",
        }:
            rerun_ids[row["model"]] = row["run_id"]

    assert set(rerun_ids) == {"candidate-model", "stable-model"}

    for run_id in rerun_ids.values():
        report_exit = main(["report", "--run", run_id, "--root", str(workspace.root)])
        report_output = capsys.readouterr().out
        assert report_exit == 0
        assert "Failure Lab Report" in report_output

    compare_exit = main(
        [
            "compare",
            rerun_ids["candidate-model"],
            rerun_ids["stable-model"],
            "--root",
            str(workspace.root),
            "--explain",
        ]
    )
    compare_output = capsys.readouterr().out

    assert compare_exit == 0
    assert "Failure Lab Compare" in compare_output
    assert "Failure Lab Insights" in compare_output

    query_exit = main(
        [
            "query",
            "--root",
            str(workspace.root),
            "--dataset",
            curated_dataset_id,
            "--summarize",
            "--json",
            "--limit",
            "10",
        ]
    )
    query_payload = json.loads(capsys.readouterr().out)

    assert query_exit == 0
    assert query_payload["insight_report"]["analysis_mode"] == "heuristic"
    assert query_payload["insight_report"]["source_kind"] == "cases"
    assert query_payload["rows"]
