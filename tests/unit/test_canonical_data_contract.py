from __future__ import annotations

from copy import deepcopy

import pytest

from model_failure_lab.config.loader import load_experiment_config
from model_failure_lab.data import (
    build_canonical_dataset,
    build_canonical_samples,
    build_group_id,
    validate_canonical_dataset,
)


def _build_source_records() -> list[dict[str, object]]:
    return [
        {
            "raw_index": 0,
            "raw_split": "train",
            "comment_text": "sample train zero",
            "toxicity": 0,
            "male": 1,
            "female": 0,
            "LGBTQ": 0,
            "christian": 0,
            "muslim": 0,
            "other_religions": 0,
            "black": 0,
            "white": 1,
            "identity_any": 1,
            "severe_toxicity": 0,
            "obscene": 0,
            "threat": 0,
            "insult": 0,
            "identity_attack": 0,
            "sexual_explicit": 0,
        },
        {
            "raw_index": 1,
            "raw_split": "train",
            "comment_text": "sample train one",
            "toxicity": 1,
            "male": 0,
            "female": 1,
            "LGBTQ": 0,
            "christian": 0,
            "muslim": 1,
            "other_religions": 0,
            "black": 1,
            "white": 0,
            "identity_any": 1,
            "severe_toxicity": 0,
            "obscene": 1,
            "threat": 0,
            "insult": 1,
            "identity_attack": 0,
            "sexual_explicit": 0,
        },
        {
            "raw_index": 2,
            "raw_split": "val",
            "comment_text": "sample val two",
            "toxicity": 0,
            "male": 0,
            "female": 1,
            "LGBTQ": 0,
            "christian": 1,
            "muslim": 0,
            "other_religions": 0,
            "black": 0,
            "white": 1,
            "identity_any": 1,
            "severe_toxicity": 0,
            "obscene": 0,
            "threat": 0,
            "insult": 0,
            "identity_attack": 0,
            "sexual_explicit": 0,
        },
        {
            "raw_index": 3,
            "raw_split": "test",
            "comment_text": "sample test three",
            "toxicity": 1,
            "male": 0,
            "female": 0,
            "LGBTQ": 1,
            "christian": 0,
            "muslim": 0,
            "other_religions": 0,
            "black": 1,
            "white": 0,
            "identity_any": 1,
            "severe_toxicity": 1,
            "obscene": 1,
            "threat": 0,
            "insult": 1,
            "identity_attack": 1,
            "sexual_explicit": 0,
        },
    ]


def test_build_canonical_samples_is_stable_and_explicit():
    config = load_experiment_config("configs/experiments/civilcomments_logistic_baseline.yaml")
    data_config = deepcopy(config["data"])
    data_config["validation"]["subgroup_min_samples_warning"] = 1
    data_config["split_role_policy"]["id_test"]["holdout_fraction"] = 1.0

    first_pass = build_canonical_samples(_build_source_records(), data_config)
    second_pass = build_canonical_samples(_build_source_records(), data_config)

    assert [sample.sample_id for sample in first_pass] == [
        sample.sample_id for sample in second_pass
    ]
    assert {sample.split for sample in first_pass} == {"id_test", "validation", "ood_test"}
    assert all(sample.split == "id_test" for sample in first_pass if sample.raw_split == "train")
    assert all(sample.raw_split in {"train", "val", "test"} for sample in first_pass)
    assert all(isinstance(sample.is_id, bool) for sample in first_pass)
    assert all(isinstance(sample.is_ood, bool) for sample in first_pass)


def test_build_canonical_dataset_preserves_group_metadata():
    config = load_experiment_config("configs/experiments/civilcomments_logistic_baseline.yaml")
    data_config = deepcopy(config["data"])
    data_config["validation"]["subgroup_min_samples_warning"] = 1
    data_config["split_role_policy"]["id_test"]["holdout_fraction"] = 0.5

    dataset = build_canonical_dataset(_build_source_records(), data_config)
    sample = dataset.samples[0]

    assert sample.group_attributes["male"] == 1
    assert sample.group_attributes["white"] == 1
    assert sample.group_id == build_group_id(sample.group_attributes)
    assert sample.dataset_name == "civilcomments"


def test_validate_canonical_dataset_rejects_missing_required_fields():
    bad_sample = {
        "sample_id": "civilcomments_bad",
        "label": 1,
        "split": "train",
        "is_id": True,
        "is_ood": False,
        "group_id": "group_x",
        "group_attributes": {"male": 1},
        "dataset_name": "civilcomments",
        "raw_split": "train",
    }

    with pytest.raises(ValueError, match="missing required fields: text"):
        validate_canonical_dataset([bad_sample], allowed_splits={"train"})


def test_validate_canonical_dataset_rejects_inconsistent_split_flags():
    bad_sample = {
        "sample_id": "civilcomments_bad",
        "text": "broken flags",
        "label": 1,
        "split": "train",
        "is_id": True,
        "is_ood": True,
        "group_id": "group_x",
        "group_attributes": {"male": 1},
        "dataset_name": "civilcomments",
        "raw_split": "train",
    }

    with pytest.raises(ValueError, match="both ID and OOD"):
        validate_canonical_dataset([bad_sample], allowed_splits={"train"})
