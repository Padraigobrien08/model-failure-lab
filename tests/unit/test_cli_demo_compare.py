from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import model_failure_lab.runner.execute as runner_execute_module
from model_failure_lab.adapters import ModelMetadata, ModelRequest, ModelResult, register_model
from model_failure_lab.classifiers import ClassifierInput, ClassifierResult, register_classifier
from model_failure_lab.cli import main
from model_failure_lab.datasets import FailureDataset, demo_dataset_path
from model_failure_lab.runner import execute_dataset_run, write_run_artifacts
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


class CompareCliAdapter:
    def generate(self, request: ModelRequest) -> ModelResult:
        return ModelResult(
            text=f"model:{request.model}::{request.prompt}",
            metadata=ModelMetadata(model=request.model, latency_ms=5.0),
        )


class CompareCliClassifier:
    def __call__(self, classifier_input: ClassifierInput) -> ClassifierResult:
        output = classifier_input.output.text.lower()
        if "shared improvement" in output and "baseline-model" in output:
            return ClassifierResult(failure_type="reasoning", confidence=0.8)
        if "shared stable failure" in output:
            return ClassifierResult(failure_type="hallucination", confidence=0.7)
        return ClassifierResult(failure_type="no_failure", confidence=0.2)


def _write_saved_run(
    root: Path,
    *,
    dataset: FailureDataset,
    model: str,
    seed: int,
    suffix_minutes: int,
    adapter_id: str,
    classifier_id: str,
) -> Path:
    execution = execute_dataset_run(
        dataset=dataset,
        adapter_id=adapter_id,
        classifier_id=classifier_id,
        model=model,
        run_seed=seed,
        now=datetime(2026, 3, 30, 14, suffix_minutes, 0, tzinfo=timezone.utc),
    )
    run_path, _ = write_run_artifacts(execution, root=root)
    return run_path


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
    assert "Case changes:" not in captured.out
    assert "Warning: comparison is incompatible" in captured.out

    report_dirs = sorted((tmp_path / "reports").iterdir())
    assert len(report_dirs) == 1
    assert (report_dirs[0] / "report.json").exists()
    assert (report_dirs[0] / "report_details.json").exists()


def test_compare_command_handles_rapid_same_dataset_runs_without_sleep(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    dataset_path = tmp_path / "datasets" / "reasoning-basics-v1.json"
    _write_dataset(
        dataset_path,
        FailureDataset(
            dataset_id="reasoning-basics-v1",
            cases=(
                PromptCase(id="case-001", prompt="Return the hidden validation code."),
                PromptCase(id="case-002", prompt="Explain why 2 + 2 = 4."),
            ),
        ),
    )

    class FixedDatetime:
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 3, 30, 13, 0, 0, 123456, tzinfo=timezone.utc)

    monkeypatch.setattr(runner_execute_module, "datetime", FixedDatetime)

    assert (
        main(
            [
                "run",
                "--dataset",
                str(dataset_path),
                "--model",
                "demo:baseline",
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
                str(dataset_path),
                "--model",
                "demo:candidate",
                "--root",
                str(tmp_path),
            ]
        )
        == 0
    )
    _ = capsys.readouterr()

    run_dirs = sorted((tmp_path / "runs").iterdir())
    assert len(run_dirs) == 2
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
    assert "Compatible: True" in captured.out
    assert "Status: unchanged" in captured.out
    assert "Case changes:" not in captured.out


def test_compare_command_surfaces_directional_transition_summary(tmp_path, capsys) -> None:
    adapter_id = "unit-cli-compare-adapter"
    classifier_id = "unit-cli-compare-classifier"
    register_model(adapter_id, CompareCliAdapter)
    register_classifier(classifier_id, CompareCliClassifier())

    baseline_path = _write_saved_run(
        tmp_path,
        dataset=FailureDataset(
            dataset_id="reasoning-basics-v1",
            cases=(
                PromptCase(id="case-001", prompt="shared improvement"),
                PromptCase(id="case-002", prompt="shared stable failure"),
            ),
        ),
        model="baseline-model",
        seed=61,
        suffix_minutes=0,
        adapter_id=adapter_id,
        classifier_id=classifier_id,
    )
    candidate_path = _write_saved_run(
        tmp_path,
        dataset=FailureDataset(
            dataset_id="reasoning-basics-v1",
            cases=(
                PromptCase(id="case-001", prompt="shared improvement"),
                PromptCase(id="case-002", prompt="shared stable failure"),
            ),
        ),
        model="candidate-model",
        seed=62,
        suffix_minutes=1,
        adapter_id=adapter_id,
        classifier_id=classifier_id,
    )

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
    assert "Status: improved" in captured.out
    assert "Compatible: True" in captured.out
    assert "Case changes: improvements=1" in captured.out
