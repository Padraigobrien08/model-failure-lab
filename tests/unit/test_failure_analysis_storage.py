from __future__ import annotations

from model_failure_lab.storage import (
    dataset_file,
    report_directory,
    report_file,
    reports_root,
    results_file,
    run_directory,
    run_file,
    runs_root,
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
