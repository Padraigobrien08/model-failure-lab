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
wilds_dataset_name: civilcomments
wilds_root_dir: data/wilds
split_scheme: official
text_field: comment_text
label_field: toxicity
group_fields:
  - male
  - female
raw_splits:
  train: train
  val: val
  test: test
split_details:
  train: train
  validation: val
  id_test: train_holdout
  ood_test: test
split_role_policy:
  train:
    raw_split: train
    selector: train_remainder
    is_id: true
    is_ood: false
  validation:
    raw_split: val
    selector: full_split
    is_id: false
    is_ood: true
  id_test:
    raw_split: train
    selector: deterministic_holdout
    is_id: true
    is_ood: false
    holdout_fraction: 0.1
    holdout_seed: 13
  ood_test:
    raw_split: test
    selector: full_split
    is_id: false
    is_ood: true
validation:
  subgroup_min_samples_warning: 10
  preview_samples: 3
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
    assert config["data"]["raw_splits"]["test"] == "test"
    assert config["data"]["split_role_policy"]["id_test"]["selector"] == "deterministic_holdout"


def test_apply_cli_overrides_whitelist():
    config = {
        "run_id": None,
        "experiment_name": "smoke",
        "experiment_group": "baselines",
        "experiment_type": "baseline",
        "model_name": "distilbert",
        "dataset_name": "civilcomments",
        "split_details": {
            "train": "train",
            "validation": "val",
            "id_test": "train_holdout",
            "ood_test": "test",
        },
        "seed": 13,
        "tags": ["baseline"],
        "notes": "",
        "parent_run_id": None,
        "data": {
            "dataset_name": "civilcomments",
            "wilds_dataset_name": "civilcomments",
            "wilds_root_dir": "data/wilds",
            "split_scheme": "official",
            "text_field": "comment_text",
            "label_field": "toxicity",
            "group_fields": ["male", "female"],
            "raw_splits": {"train": "train", "val": "val", "test": "test"},
            "split_details": {
                "train": "train",
                "validation": "val",
                "id_test": "train_holdout",
                "ood_test": "test",
            },
            "split_role_policy": {
                "train": {
                    "raw_split": "train",
                    "selector": "train_remainder",
                    "is_id": True,
                    "is_ood": False,
                },
                "validation": {
                    "raw_split": "val",
                    "selector": "full_split",
                    "is_id": False,
                    "is_ood": True,
                },
                "id_test": {
                    "raw_split": "train",
                    "selector": "deterministic_holdout",
                    "is_id": True,
                    "is_ood": False,
                    "holdout_fraction": 0.1,
                    "holdout_seed": 13,
                },
                "ood_test": {
                    "raw_split": "test",
                    "selector": "full_split",
                    "is_id": False,
                    "is_ood": True,
                },
            },
            "validation": {"subgroup_min_samples_warning": 25, "preview_samples": 5},
        },
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


def test_apply_cli_overrides_merges_tags_additively():
    config = {
        "run_id": None,
        "experiment_name": "smoke",
        "experiment_group": "baselines",
        "experiment_type": "baseline",
        "model_name": "distilbert",
        "dataset_name": "civilcomments",
        "split_details": {
            "train": "train",
            "validation": "val",
            "id_test": "train_holdout",
            "ood_test": "test",
        },
        "seed": 13,
        "tags": ["baseline", "distilbert"],
        "notes": "",
        "parent_run_id": None,
        "data": {
            "dataset_name": "civilcomments",
            "wilds_dataset_name": "civilcomments",
            "wilds_root_dir": "data/wilds",
            "split_scheme": "official",
            "text_field": "comment_text",
            "label_field": "toxicity",
            "group_fields": ["male", "female"],
            "raw_splits": {"train": "train", "val": "val", "test": "test"},
            "split_details": {
                "train": "train",
                "validation": "val",
                "id_test": "train_holdout",
                "ood_test": "test",
            },
            "split_role_policy": {
                "train": {
                    "raw_split": "train",
                    "selector": "train_remainder",
                    "is_id": True,
                    "is_ood": False,
                },
                "validation": {
                    "raw_split": "val",
                    "selector": "full_split",
                    "is_id": False,
                    "is_ood": True,
                },
                "id_test": {
                    "raw_split": "train",
                    "selector": "deterministic_holdout",
                    "is_id": True,
                    "is_ood": False,
                    "holdout_fraction": 0.1,
                    "holdout_seed": 13,
                },
                "ood_test": {
                    "raw_split": "test",
                    "selector": "full_split",
                    "is_id": False,
                    "is_ood": True,
                },
            },
            "validation": {"subgroup_min_samples_warning": 25, "preview_samples": 5},
        },
        "model": {"model_name": "distilbert"},
        "train": {"seed": 13},
        "eval": {"primary_metric": "accuracy"},
    }

    updated = apply_cli_overrides(
        config,
        {
            "tags": ["v1.1_baseline", "distilbert", "official"],
        },
    )

    assert updated["tags"] == ["baseline", "distilbert", "v1.1_baseline", "official"]


def test_apply_cli_overrides_rejects_unknown_keys():
    config = {
        "run_id": None,
        "experiment_name": "smoke",
        "experiment_group": "baselines",
        "experiment_type": "baseline",
        "model_name": "distilbert",
        "dataset_name": "civilcomments",
        "split_details": {
            "train": "train",
            "validation": "val",
            "id_test": "train_holdout",
            "ood_test": "test",
        },
        "seed": 13,
        "tags": [],
        "notes": "",
        "parent_run_id": None,
        "data": {
            "dataset_name": "civilcomments",
            "wilds_dataset_name": "civilcomments",
            "wilds_root_dir": "data/wilds",
            "split_scheme": "official",
            "text_field": "comment_text",
            "label_field": "toxicity",
            "group_fields": ["male", "female"],
            "raw_splits": {"train": "train", "val": "val", "test": "test"},
            "split_details": {
                "train": "train",
                "validation": "val",
                "id_test": "train_holdout",
                "ood_test": "test",
            },
            "split_role_policy": {
                "train": {
                    "raw_split": "train",
                    "selector": "train_remainder",
                    "is_id": True,
                    "is_ood": False,
                },
                "validation": {
                    "raw_split": "val",
                    "selector": "full_split",
                    "is_id": False,
                    "is_ood": True,
                },
                "id_test": {
                    "raw_split": "train",
                    "selector": "deterministic_holdout",
                    "is_id": True,
                    "is_ood": False,
                    "holdout_fraction": 0.1,
                    "holdout_seed": 13,
                },
                "ood_test": {
                    "raw_split": "test",
                    "selector": "full_split",
                    "is_id": False,
                    "is_ood": True,
                },
            },
            "validation": {"subgroup_min_samples_warning": 25, "preview_samples": 5},
        },
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
    assert distilbert_config["split_details"]["id_test"] == "train_holdout"
    assert distilbert_config["data"]["raw_splits"]["val"] == "val"
