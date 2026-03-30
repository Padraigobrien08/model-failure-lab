from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
import importlib
from pathlib import Path

from model_failure_lab.cli import main
from model_failure_lab.datasets import FailureDataset
from model_failure_lab.schemas import PromptCase

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"


def _module_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT)
    return env


def _purge_modules(*prefixes: str) -> None:
    for name in list(sys.modules):
        if any(name == prefix or name.startswith(f"{prefix}.") for prefix in prefixes):
            sys.modules.pop(name, None)


def _write_dataset(path: Path, dataset: FailureDataset) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dataset.to_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_pyproject_exposes_canonical_and_compatibility_entrypoints() -> None:
    payload = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = payload["project"]["scripts"]

    assert scripts["failure-lab"] == "model_failure_lab.cli:main"
    assert scripts["model-failure-lab"] == "model_failure_lab.cli:main"


def test_python_module_entrypoint_prints_new_help_surface_without_args() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "model_failure_lab"],
        cwd=PROJECT_ROOT,
        env=_module_env(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "usage: failure-lab" in result.stdout
    assert "run" in result.stdout
    assert "report" in result.stdout
    assert "compare" in result.stdout
    assert "demo" in result.stdout
    assert "run-baseline" not in result.stdout


def test_cli_module_import_does_not_load_matplotlib() -> None:
    _purge_modules("model_failure_lab.cli", "model_failure_lab.reporting", "matplotlib")

    importlib.import_module("model_failure_lab.cli")

    assert "matplotlib" not in sys.modules


def test_run_command_supports_direct_dataset_paths_and_writes_artifacts(tmp_path, capsys) -> None:
    dataset_path = tmp_path / "external" / "ad_hoc_cases.json"
    _write_dataset(
        dataset_path,
        FailureDataset(
            dataset_id="reasoning-basics-v1",
            name="Reasoning Basics",
            cases=(PromptCase(id="case-001", prompt="Explain why 2 + 2 = 4."),),
        ),
    )

    exit_code = main(
        [
            "run",
            "--dataset",
            str(dataset_path),
            "--model",
            "demo",
            "--root",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Failure Lab Run" in captured.out
    assert "Dataset: reasoning-basics-v1" in captured.out
    assert "Failure rate:" in captured.out
    run_dirs = sorted((tmp_path / "runs").iterdir())
    assert len(run_dirs) == 1
    assert (run_dirs[0] / "run.json").exists()
    assert (run_dirs[0] / "results.json").exists()


def test_run_and_report_support_canonical_id_and_path_resolution(tmp_path, capsys) -> None:
    dataset_root = tmp_path / "datasets"
    dataset_path = dataset_root / "reasoning-basics-v1.json"
    _write_dataset(
        dataset_path,
        FailureDataset(
            dataset_id="reasoning-basics-v1",
            name="Reasoning Basics",
            cases=(PromptCase(id="case-001", prompt="Explain why 2 + 2 = 4."),),
        ),
    )

    run_exit = main(
        [
            "run",
            "--dataset",
            "reasoning-basics-v1",
            "--model",
            "demo",
            "--root",
            str(tmp_path),
        ]
    )
    run_output = capsys.readouterr().out
    run_dirs = sorted((tmp_path / "runs").iterdir())
    run_dir = run_dirs[0]
    run_id = run_dir.name

    report_exit = main(
        [
            "report",
            "--run",
            str(run_dir / "run.json"),
            "--root",
            str(tmp_path),
        ]
    )
    report_output = capsys.readouterr().out

    assert run_exit == 0
    assert report_exit == 0
    assert f"Run ID: {run_id}" in run_output
    assert "Failure Lab Report" in report_output
    assert f"Run ID: {run_id}" in report_output
    assert "Classification coverage:" in report_output
    report_dirs = sorted((tmp_path / "reports").iterdir())
    assert len(report_dirs) == 1
    assert (report_dirs[0] / "report.json").exists()
    assert (report_dirs[0] / "report_details.json").exists()
