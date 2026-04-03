from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import model_failure_lab.adapters.ollama_adapter as ollama_adapter_module
import model_failure_lab.datasets as datasets_module
from model_failure_lab.cli import main
from model_failure_lab.datasets import FailureDataset
from model_failure_lab.schemas import PromptCase, PromptExpectations
from model_failure_lab.storage import read_json

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
    assert "datasets" in result.stdout
    assert "run-baseline" not in result.stdout


def test_run_help_describes_current_working_directory_default() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "model_failure_lab", "run", "--help"],
        cwd=PROJECT_ROOT,
        env=_module_env(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Defaults to the current working directory." in result.stdout
    assert "--system-prompt" in result.stdout
    assert "--model-option" in result.stdout
    assert "--ollama-host" in result.stdout


def test_cli_module_import_does_not_load_matplotlib() -> None:
    _purge_modules("model_failure_lab.cli", "model_failure_lab.reporting", "matplotlib")

    importlib.import_module("model_failure_lab.cli")

    assert "matplotlib" not in sys.modules
    assert not any(
        name == "model_failure_lab.reporting"
        or name.startswith("model_failure_lab.reporting.")
        for name in sys.modules
    )


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


def test_run_command_uses_current_working_directory_when_root_is_omitted(
    tmp_path, monkeypatch, capsys
) -> None:
    dataset_path = tmp_path / "datasets" / "reasoning-basics-v1.json"
    _write_dataset(
        dataset_path,
        FailureDataset(
            dataset_id="reasoning-basics-v1",
            name="Reasoning Basics",
            cases=(PromptCase(id="case-001", prompt="Explain why 2 + 2 = 4."),),
        ),
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(["run", "--dataset", "reasoning-basics-v1", "--model", "demo"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Failure Lab Run" in captured.out
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


def test_report_command_surfaces_expectation_verdicts_when_present(tmp_path, capsys) -> None:
    dataset_root = tmp_path / "datasets"
    dataset_path = dataset_root / "hallucination-failures-v1.json"
    _write_dataset(
        dataset_path,
        FailureDataset(
            dataset_id="hallucination-failures-v1",
            name="Hallucination Failures",
            cases=(
                PromptCase(
                    id="case-001",
                    prompt="Explain why 2 + 2 = 4.",
                    tags=("core", "factuality"),
                    expectations=PromptExpectations(
                        expected_failure="no_failure",
                        reference_answer="The answer must explicitly say exactly forty-two.",
                    ),
                ),
            ),
        ),
    )

    run_exit = main(
        [
            "run",
            "--dataset",
            "hallucination-failures-v1",
            "--model",
            "demo",
            "--root",
            str(tmp_path),
        ]
    )
    capsys.readouterr()
    run_dir = sorted((tmp_path / "runs").iterdir())[0]

    report_exit = main(
        [
            "report",
            "--run",
            str(run_dir),
            "--root",
            str(tmp_path),
        ]
    )
    report_output = capsys.readouterr().out

    assert run_exit == 0
    assert report_exit == 0
    assert "Failure types:" in report_output
    assert "Verdicts: unexpected_failure=1" in report_output


def test_run_command_supports_bundled_dataset_ids_with_core_default(tmp_path, capsys) -> None:
    exit_code = main(
        [
            "run",
            "--dataset",
            "reasoning-failures-v1",
            "--model",
            "demo",
            "--root",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()
    run_dirs = sorted((tmp_path / "runs").iterdir())
    run_dir = run_dirs[0]
    run_payload = read_json(run_dir / "run.json")
    results_payload = read_json(run_dir / "results.json")

    assert exit_code == 0
    assert "Failure Lab Run" in captured.out
    assert "Dataset: reasoning-failures-v1" in captured.out
    assert "Dataset scope: core" in captured.out
    assert run_payload["config"]["dataset_scope"] == "core"
    assert run_payload["config"]["dataset_source"] == "bundled"
    assert results_payload["total_cases"] == 8


def test_run_command_supports_full_bundled_dataset_execution(tmp_path, capsys) -> None:
    exit_code = main(
        [
            "run",
            "--dataset",
            "reasoning-failures-v1",
            "--model",
            "demo",
            "--full",
            "--root",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()
    run_dirs = sorted((tmp_path / "runs").iterdir())
    run_dir = run_dirs[0]
    run_payload = read_json(run_dir / "run.json")
    results_payload = read_json(run_dir / "results.json")

    assert exit_code == 0
    assert "Dataset scope: full" in captured.out
    assert run_payload["config"]["dataset_scope"] == "full"
    assert results_payload["total_cases"] == 12


def test_run_command_supports_hallucination_bundled_dataset_ids(tmp_path, capsys) -> None:
    exit_code = main(
        [
            "run",
            "--dataset",
            "hallucination-failures-v1",
            "--model",
            "demo",
            "--root",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()
    run_dirs = sorted((tmp_path / "runs").iterdir())
    run_dir = run_dirs[0]
    results_payload = read_json(run_dir / "results.json")

    assert exit_code == 0
    assert "Dataset: hallucination-failures-v1" in captured.out
    assert "Dataset scope: core" in captured.out
    assert results_payload["total_cases"] == 8


def test_run_command_supports_rag_bundled_dataset_ids(tmp_path, capsys) -> None:
    exit_code = main(
        [
            "run",
            "--dataset",
            "rag-failures-v1",
            "--model",
            "demo",
            "--root",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()
    run_dirs = sorted((tmp_path / "runs").iterdir())
    run_dir = run_dirs[0]
    results_payload = read_json(run_dir / "results.json")

    assert exit_code == 0
    assert "Dataset: rag-failures-v1" in captured.out
    assert "Dataset scope: core" in captured.out
    assert results_payload["total_cases"] == 8


def test_run_command_threads_explicit_ollama_config_into_run_artifacts(
    tmp_path, monkeypatch, capsys
) -> None:
    dataset_path = tmp_path / "datasets" / "reasoning-basics-v1.json"
    _write_dataset(
        dataset_path,
        FailureDataset(
            dataset_id="reasoning-basics-v1",
            name="Reasoning Basics",
            cases=(PromptCase(id="case-001", prompt="Explain why 2 + 2 = 4."),),
        ),
    )
    ollama_calls: list[dict[str, object]] = []

    def fake_post_json(base_url: str, payload: dict[str, object], timeout_seconds: float | None):
        ollama_calls.append(
            {
                "base_url": base_url,
                "payload": dict(payload),
                "timeout_seconds": timeout_seconds,
            }
        )
        return {
            "model": str(payload["model"]),
            "response": f"model:{payload['model']}::{payload['prompt']}",
            "done": True,
            "prompt_eval_count": 8,
            "eval_count": 5,
        }

    monkeypatch.setattr(ollama_adapter_module, "_post_json", fake_post_json)

    exit_code = main(
        [
            "run",
            "--dataset",
            str(dataset_path),
            "--model",
            "ollama:llama3.2",
            "--ollama-host",
            "http://127.0.0.1:11434",
            "--system-prompt",
            "Be concise.",
            "--model-option",
            "temperature=0",
            "--model-option",
            'stop=["DONE"]',
            "--root",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()
    run_dir = sorted((tmp_path / "runs").iterdir())[0]
    run_payload = read_json(run_dir / "run.json")

    assert exit_code == 0
    assert "Adapter: ollama" in captured.out
    assert run_payload["config"] == {
        "system_prompt": "Be concise.",
        "model_options": {
            "temperature": 0,
            "stop": ["DONE"],
            "base_url": "http://127.0.0.1:11434",
        },
    }
    assert ollama_calls[0]["base_url"] == "http://127.0.0.1:11434"
    assert ollama_calls[0]["payload"]["system"] == "Be concise."
    assert ollama_calls[0]["payload"]["options"]["temperature"] == 0
    assert ollama_calls[0]["payload"]["options"]["stop"] == ["DONE"]


def test_run_command_rejects_malformed_model_option(tmp_path, capsys) -> None:
    dataset_path = tmp_path / "datasets" / "reasoning-basics-v1.json"
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
            "ollama:llama3.2",
            "--model-option",
            "temperature=oops",
            "--root",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "model option must use `key=json-value`" in captured.err


def test_datasets_list_command_shows_compact_bundled_catalog(capsys) -> None:
    exit_code = main(["datasets", "list"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Failure Lab Datasets" in captured.out
    assert "reasoning-failures-v1" in captured.out
    assert "hallucination-failures-v1" in captured.out
    assert "rag-failures-v1" in captured.out
    assert "core" in captured.out
    assert "full" in captured.out


def test_demo_command_surfaces_packaged_install_error_when_asset_is_missing(
    monkeypatch, tmp_path, capsys
) -> None:
    missing_path = tmp_path / "missing-demo-dataset.json"
    monkeypatch.setattr(datasets_module, "demo_dataset_path", lambda: missing_path)

    exit_code = main(["demo"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "installed `model-failure-lab` package" in captured.err
    assert str(missing_path) not in captured.err
