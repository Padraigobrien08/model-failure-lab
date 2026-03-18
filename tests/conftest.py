from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


@pytest.fixture()
def temp_artifact_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MODEL_FAILURE_LAB_ARTIFACT_ROOT", str(artifact_dir))
    return artifact_dir


@pytest.fixture()
def temp_config_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    config_dir = tmp_path / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MODEL_FAILURE_LAB_CONFIG_ROOT", str(config_dir))
    return config_dir
