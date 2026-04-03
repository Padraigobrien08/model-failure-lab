from __future__ import annotations

from pathlib import Path

import pytest

from model_failure_lab.data.civilcomments import DataDependencyError, _resolve_get_dataset
from model_failure_lab.models.distilbert import build_sequence_classifier, build_tokenizer
from model_failure_lab.utils.runtime import (
    check_python_dependency,
    ensure_matplotlib_runtime_dir,
)
from scripts.check_environment import run_command as run_check_environment_command


def test_ensure_matplotlib_runtime_dir_sets_env(monkeypatch, tmp_path):
    monkeypatch.delenv("MPLCONFIGDIR", raising=False)

    runtime_dir = ensure_matplotlib_runtime_dir(tmp_path / "mplconfig")

    assert runtime_dir.exists()
    assert runtime_dir == Path(tmp_path / "mplconfig")
    assert runtime_dir.as_posix() == str(runtime_dir)


def test_check_python_dependency_reports_missing_package():
    status = check_python_dependency("model_failure_lab_missing_package")

    assert status["available"] is False
    assert status["package"] == "model_failure_lab_missing_package"
    assert status["error"] is not None


def test_check_environment_reports_dependency_and_model_status(tmp_path):
    payload = run_check_environment_command(
        ["--json"],
        dependency_checker=lambda package: {
            "package": package,
            "available": package != "wilds",
            "version": "1.0" if package != "wilds" else None,
            "error": None if package != "wilds" else "missing",
        },
        matplotlib_dir_resolver=lambda: tmp_path / "mplconfig",
        config_loader=lambda _preset: {
            "model": {"pretrained_name": "distilbert-base-uncased"},
        },
        transformer_asset_checker=lambda pretrained_name: {
            "pretrained_name": pretrained_name,
            "local_cache_available": False,
            "message": (
                "Local cache not detected. The first DistilBERT run will require "
                "network access or a pre-populated local cache."
            ),
        },
    )

    assert payload["overall_ok"] is False
    assert payload["dependencies"]["wilds"]["available"] is False
    assert payload["matplotlib"]["runtime_dir"].endswith("mplconfig")
    assert payload["distilbert"]["pretrained_name"] == "distilbert-base-uncased"
    assert "network access" in payload["distilbert"]["message"]


def test_check_environment_human_output_includes_install_and_prefetch_guidance(
    capsys,
    tmp_path,
):
    payload = run_check_environment_command(
        [],
        dependency_checker=lambda package: {
            "package": package,
            "available": package != "wilds",
            "version": "1.0" if package != "wilds" else None,
            "error": None if package != "wilds" else "missing",
        },
        matplotlib_dir_resolver=lambda: tmp_path / "mplconfig",
        config_loader=lambda _preset: {
            "model": {"pretrained_name": "distilbert-base-uncased"},
        },
        transformer_asset_checker=lambda pretrained_name: {
            "pretrained_name": pretrained_name,
            "local_cache_available": False,
            "message": (
                "Local cache not detected. The first DistilBERT run will require "
                "network access or a pre-populated local cache."
            ),
        },
    )

    captured = capsys.readouterr()
    assert payload["overall_ok"] is False
    assert "python -m pip install -e '.[dev,legacy]'" in captured.out
    assert "AutoTokenizer.from_pretrained('distilbert-base-uncased')" in captured.out
    assert "network access" in captured.out


def test_missing_wilds_message_points_to_check_environment(monkeypatch):
    def fake_import_module(_name: str):
        raise ModuleNotFoundError("wilds")

    monkeypatch.setattr("model_failure_lab.data.civilcomments.import_module", fake_import_module)

    with pytest.raises(DataDependencyError, match="python scripts/check_environment.py"):
        _resolve_get_dataset()
    with pytest.raises(DataDependencyError, match="\\[legacy\\]"):
        _resolve_get_dataset()


def test_distilbert_tokenizer_failure_mentions_cache_and_check_environment(monkeypatch):
    def raise_missing_tokenizer(_pretrained_name: str):
        raise OSError("missing tokenizer assets")

    monkeypatch.setattr(
        "model_failure_lab.models.distilbert.AutoTokenizer.from_pretrained",
        raise_missing_tokenizer,
    )

    with pytest.raises(RuntimeError) as excinfo:
        build_tokenizer("distilbert-base-uncased")

    message = str(excinfo.value)
    assert "distilbert-base-uncased" in message
    assert "local cache" in message or "network access" in message
    assert "python scripts/check_environment.py" in message


def test_distilbert_model_failure_mentions_cache_and_check_environment(monkeypatch):
    def raise_missing_model(_pretrained_name: str, *, num_labels: int):
        del num_labels
        raise OSError("missing model assets")

    monkeypatch.setattr(
        "model_failure_lab.models.distilbert.AutoModelForSequenceClassification.from_pretrained",
        raise_missing_model,
    )

    with pytest.raises(RuntimeError) as excinfo:
        build_sequence_classifier("distilbert-base-uncased", 2)

    message = str(excinfo.value)
    assert "distilbert-base-uncased" in message
    assert "local cache" in message or "network access" in message
    assert "python scripts/check_environment.py" in message
