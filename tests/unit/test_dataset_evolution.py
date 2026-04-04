from __future__ import annotations

import json
from pathlib import Path

from model_failure_lab.cli import main
from model_failure_lab.datasets import (
    evolve_dataset_family,
    generate_regression_pack,
    list_dataset_versions,
)
from model_failure_lab.index import list_run_inventory
from model_failure_lab.testing import materialize_insight_fixture
from model_failure_lab.testing.insight_fixture import (
    FIXTURE_ADAPTER_ID,
    FIXTURE_CLASSIFIER_ID,
)


def test_generate_regression_pack_builds_signal_driven_draft_dataset(tmp_path: Path) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison = workspace.comparisons[0]

    summary = generate_regression_pack(
        comparison_id=comparison.report_id,
        root=workspace.root,
        top_n=2,
    )

    assert summary.dataset.lifecycle == "draft"
    assert summary.dataset.source["origin"] == "regression_signal_pack"
    assert summary.dataset.source["comparison_report_id"] == comparison.report_id
    assert summary.selected_case_count == len(summary.preview_cases)
    assert summary.selected_case_count > 0
    assert summary.output_path.exists()
    assert summary.preview_cases
    assert all("regression-pack" in case.tags for case in summary.dataset.cases)
    assert all(
        case.metadata["harvest"]["source_kind"] == "comparison_signal"
        for case in summary.dataset.cases
    )


def test_dataset_evolve_creates_version_history_and_keeps_ids_stable(tmp_path: Path) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    family_id = "fixture-regression-family"

    first = evolve_dataset_family(
        family_id,
        comparison_id=workspace.comparisons[0].report_id,
        root=workspace.root,
        top_n=2,
    )

    second = None
    for comparison in workspace.comparisons[1:]:
        try:
            second = evolve_dataset_family(
                family_id,
                comparison_id=comparison.report_id,
                root=workspace.root,
                top_n=3,
            )
            break
        except ValueError:
            continue

    assert second is not None
    versions = list_dataset_versions(family_id, root=workspace.root)

    assert first.dataset.dataset_id.endswith("-v1")
    assert second.dataset.dataset_id.endswith("-v2")
    assert second.parent_dataset_id == first.dataset.dataset_id
    assert len(versions) == 2
    assert versions[0].dataset_id == first.dataset.dataset_id
    assert versions[1].dataset_id == second.dataset.dataset_id
    assert {case.id for case in first.dataset.cases}.issubset(
        {case.id for case in second.dataset.cases}
    )


def test_cli_regression_pack_and_dataset_version_commands_surface_json(
    tmp_path: Path,
    capsys,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison = workspace.comparisons[1]

    generate_exit = main(
        [
            "regressions",
            "generate",
            "--comparison",
            comparison.report_id,
            "--root",
            str(workspace.root),
            "--json",
        ]
    )
    generate_payload = json.loads(capsys.readouterr().out)

    evolve_exit = main(
        [
            "dataset",
            "evolve",
            "fixture-regression-family",
            "--from-comparison",
            comparison.report_id,
            "--root",
            str(workspace.root),
            "--json",
        ]
    )
    evolve_payload = json.loads(capsys.readouterr().out)

    versions_exit = main(
        [
            "dataset",
            "versions",
            "fixture-regression-family",
            "--root",
            str(workspace.root),
            "--json",
        ]
    )
    versions_payload = json.loads(capsys.readouterr().out)

    assert generate_exit == 0
    assert generate_payload["comparison_id"] == comparison.report_id
    assert generate_payload["dataset_id"].endswith("-draft")
    assert generate_payload["suggested_family_id"].startswith("regression-")
    assert evolve_exit == 0
    assert evolve_payload["dataset_id"].endswith("-v1")
    assert evolve_payload["family_id"] == "fixture-regression-family"
    assert versions_exit == 0
    assert len(versions_payload["versions"]) == 1


def test_evolved_regression_dataset_replays_through_standard_loop(
    tmp_path: Path,
    capsys,
) -> None:
    workspace = materialize_insight_fixture(tmp_path / "fixture")
    comparison = workspace.comparisons[1]
    family_id = "fixture-regression-family"

    evolve_exit = main(
        [
            "dataset",
            "evolve",
            family_id,
            "--from-comparison",
            comparison.report_id,
            "--root",
            str(workspace.root),
        ]
    )
    evolve_output = capsys.readouterr().out

    assert evolve_exit == 0
    assert "Failure Lab Dataset Evolution" in evolve_output

    versioned_dataset_id = list_dataset_versions(family_id, root=workspace.root)[-1].dataset_id

    rerun_ids: dict[str, str] = {}
    for model_name in ("candidate-model", "stable-model"):
        run_exit = main(
            [
                "run",
                "--dataset",
                versioned_dataset_id,
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
        if row["dataset"] == versioned_dataset_id and row["model"] in {
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
            "--summary",
        ]
    )
    compare_output = capsys.readouterr().out

    assert compare_exit == 0
    assert "Failure Lab Signal Summary" in compare_output
