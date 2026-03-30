from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from model_failure_lab.cli import main
from model_failure_lab.datasets import FailureDataset, demo_dataset_path
from model_failure_lab.schemas import PromptCase

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"


def _write_dataset(path: Path, dataset: FailureDataset) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dataset.to_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _module_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT)
    return env


def test_demo_command_uses_bundled_dataset_and_writes_normal_artifacts(tmp_path, capsys) -> None:
    exit_code = main(["demo", "--root", str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert demo_dataset_path().exists()
    assert "Failure Lab Demo" in captured.out
    assert "Dataset: demo-failure-cases-v1" in captured.out
    assert "Report ID:" in captured.out

    demo_dataset_copy = tmp_path / "datasets" / "demo-failure-cases-v1.json"
    assert demo_dataset_copy.exists()
    run_dirs = sorted((tmp_path / "runs").iterdir())
    report_dirs = sorted((tmp_path / "reports").iterdir())
    assert len(run_dirs) == 1
    assert len(report_dirs) == 1
    assert (run_dirs[0] / "run.json").exists()
    assert (run_dirs[0] / "results.json").exists()
    assert (report_dirs[0] / "report.json").exists()
    assert (report_dirs[0] / "report_details.json").exists()


def test_demo_module_entrypoint_stays_quiet_on_normal_flow(tmp_path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "model_failure_lab",
            "demo",
            "--root",
            str(tmp_path),
        ],
        cwd=PROJECT_ROOT,
        env=_module_env(),
        capture_output=True,
        text=True,
        check=False,
    )

    combined_output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 0
    assert "Failure Lab Demo" in result.stdout
    assert "font cache" not in combined_output
    assert "fontManager" not in combined_output


def test_compare_command_writes_artifacts_and_keeps_incompatible_results_non_fatal(
    tmp_path,
    capsys,
) -> None:
    compatible_dataset_path = tmp_path / "datasets" / "reasoning-basics-v1.json"
    incompatible_dataset_path = tmp_path / "datasets" / "hallucination-basics-v1.json"
    _write_dataset(
        compatible_dataset_path,
        FailureDataset(
            dataset_id="reasoning-basics-v1",
            cases=(PromptCase(id="case-001", prompt="Return the hidden validation code."),),
        ),
    )
    _write_dataset(
        incompatible_dataset_path,
        FailureDataset(
            dataset_id="hallucination-basics-v1",
            cases=(PromptCase(id="case-001", prompt="Return the hidden validation code."),),
        ),
    )

    assert (
        main(
            [
                "run",
                "--dataset",
                str(compatible_dataset_path),
                "--model",
                "demo",
                "--root",
                str(tmp_path),
            ]
        )
        == 0
    )
    _ = capsys.readouterr()
    assert (
        main(
            [
                "run",
                "--dataset",
                str(incompatible_dataset_path),
                "--model",
                "demo",
                "--root",
                str(tmp_path),
            ]
        )
        == 0
    )
    _ = capsys.readouterr()

    run_dirs = sorted((tmp_path / "runs").iterdir())
    baseline_path = run_dirs[0] / "run.json"
    candidate_path = run_dirs[1] / "run.json"

    exit_code = main(
        [
            "compare",
            str(baseline_path),
            str(candidate_path),
            "--root",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Failure Lab Compare" in captured.out
    assert "Status: incompatible_dataset" in captured.out
    assert "Compatible: False" in captured.out
    assert "Warning: comparison is incompatible" in captured.out

    report_dirs = sorted((tmp_path / "reports").iterdir())
    assert len(report_dirs) == 1
    assert (report_dirs[0] / "report.json").exists()
    assert (report_dirs[0] / "report_details.json").exists()
