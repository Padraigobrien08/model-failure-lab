from __future__ import annotations

from model_failure_lab.schemas import Run
from model_failure_lab.storage import (
    dataset_file,
    read_json,
    report_directory,
    report_file,
    reports_root,
    results_file,
    run_directory,
    run_file,
    runs_root,
    write_json,
)


def test_storage_layout_paths_are_deterministic() -> None:
    assert dataset_file("Reasoning Failures").as_posix().endswith(
        "datasets/reasoning_failures.json"
    )
    assert run_directory("Run 001").as_posix().endswith("runs/run_001")
    assert run_file("Run 001").as_posix().endswith("runs/run_001/run.json")
    assert results_file("Run 001").as_posix().endswith("runs/run_001/results.json")
    assert report_directory("Final Verdict").as_posix().endswith("reports/final_verdict")
    assert report_file("Final Verdict").as_posix().endswith("reports/final_verdict/report.json")


def test_storage_roots_and_run_paths_can_create_directories(tmp_path) -> None:
    assert not runs_root(root=tmp_path).exists()
    assert not reports_root(root=tmp_path).exists()

    run_path = run_file("Run 001", root=tmp_path, create=True)
    report_path = report_file("Final Verdict", root=tmp_path, create=True)

    assert run_path.parent.is_dir()
    assert report_path.parent.is_dir()


def test_json_artifacts_round_trip_canonical_run_payload(tmp_path) -> None:
    run = Run(
        run_id="run_001",
        model="gpt-4",
        dataset="reasoning.json",
        created_at="2026-03-30T12:00:00Z",
        config={"temperature": 0},
        metadata={"classifier": "heuristic_v1"},
    )

    artifact_path = run_file("run_001", root=tmp_path, create=True)
    write_json(artifact_path, run.to_payload())

    assert Run.from_payload(read_json(artifact_path)) == run
