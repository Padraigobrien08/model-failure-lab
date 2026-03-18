from __future__ import annotations

from pathlib import Path

import pytest

from model_failure_lab.config.loader import apply_cli_overrides, load_experiment_config


def _write_yaml(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_load_experiment_config_composes_sections(temp_config_root):
    _write_yaml(
        temp_config_root / "data" / "civilcomments.yaml",
        """
dataset_name: civilcomments
split_details:
  train: train
  validation: val
""".strip(),
    )
    _write_yaml(
        temp_config_root / "model" / "logistic_tfidf.yaml",
        """
model_name: logistic_tfidf
feature_backend: tfidf
""".strip(),
    )
    _write_yaml(
        temp_config_root / "train" / "default.yaml",
        """
seed: 99
batch_size: 8
""".strip(),
    )
    _write_yaml(
        temp_config_root / "eval" / "default.yaml",
        """
primary_metric: accuracy
""".strip(),
    )
    _write_yaml(
        temp_config_root / "experiments" / "smoke.yaml",
        """
experiment_name: smoke
experiment_type: baseline
model_name: logistic_tfidf
data_config: ../data/civilcomments.yaml
model_config: ../model/logistic_tfidf.yaml
train_config: ../train/default.yaml
eval_config: ../eval/default.yaml
tags: [baseline]
notes: temp preset
""".strip(),
    )

    config = load_experiment_config(temp_config_root / "experiments" / "smoke.yaml")

    assert config["model_name"] == "logistic_tfidf"
    assert config["dataset_name"] == "civilcomments"
    assert config["seed"] == 99
    assert config["split_details"]["validation"] == "val"


def test_apply_cli_overrides_whitelist():
    config = {
        "run_id": None,
        "experiment_name": "smoke",
        "experiment_group": "baselines",
        "experiment_type": "baseline",
        "model_name": "distilbert",
        "dataset_name": "civilcomments",
        "split_details": {"train": "train"},
        "seed": 13,
        "tags": ["baseline"],
        "notes": "",
        "parent_run_id": None,
        "data": {"dataset_name": "civilcomments", "split_details": {"train": "train"}},
        "model": {"model_name": "distilbert"},
        "train": {"seed": 13},
        "eval": {"primary_metric": "accuracy"},
    }

    updated = apply_cli_overrides(
        config,
        {
            "seed": 7,
            "notes": "override",
            "run_id": "manual_run",
            "experiment_group": "smoke_group",
        },
    )

    assert updated["seed"] == 7
    assert updated["notes"] == "override"
    assert updated["run_id"] == "manual_run"
    assert updated["experiment_group"] == "smoke_group"


def test_apply_cli_overrides_rejects_unknown_keys():
    config = {
        "run_id": None,
        "experiment_name": "smoke",
        "experiment_group": "baselines",
        "experiment_type": "baseline",
        "model_name": "distilbert",
        "dataset_name": "civilcomments",
        "split_details": {"train": "train"},
        "seed": 13,
        "tags": [],
        "notes": "",
        "parent_run_id": None,
        "data": {"dataset_name": "civilcomments", "split_details": {"train": "train"}},
        "model": {"model_name": "distilbert"},
        "train": {"seed": 13},
        "eval": {"primary_metric": "accuracy"},
    }

    with pytest.raises(ValueError, match="Unsupported config override keys"):
        apply_cli_overrides(config, {"model_name": "should_fail"})


def test_repository_baseline_presets_resolve():
    logistic_config = load_experiment_config(
        "configs/experiments/civilcomments_logistic_baseline.yaml"
    )
    distilbert_config = load_experiment_config(
        "configs/experiments/civilcomments_distilbert_baseline.yaml"
    )

    assert logistic_config["model_name"] == "logistic_tfidf"
    assert distilbert_config["model_name"] == "distilbert"
    assert logistic_config["dataset_name"] == "civilcomments"
    assert distilbert_config["split_details"]["id_test"] == "id_test"
