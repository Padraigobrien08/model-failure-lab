from __future__ import annotations

from model_failure_lab.config import apply_cli_overrides, load_experiment_config
from model_failure_lab.perturbations import (
    build_perturbed_sample_id,
    generate_perturbation_suite,
    select_source_samples,
)


def _source_sample(
    sample_id: str,
    *,
    split: str = "validation",
    text: str = "Please, YOU are really great people!",
    label: int = 1,
) -> dict[str, object]:
    return {
        "sample_id": sample_id,
        "text": text,
        "label": label,
        "split": split,
        "is_id": split in {"train", "id_test"},
        "is_ood": split in {"validation", "ood_test"},
        "group_id": "group_a" if label == 0 else "group_b",
        "group_attributes": {"identity_any": 1},
        "dataset_name": "civilcomments",
        "raw_split": "val" if split == "validation" else "train",
        "raw_index": sample_id,
    }


def test_load_perturbation_preset_and_cli_overrides():
    config = load_experiment_config("configs/experiments/civilcomments_perturbation_stress.yaml")
    updated = apply_cli_overrides(
        config,
        {
            "source_split": "validation",
            "max_source_samples": 12,
            "families": "slang_rewrite,typo_noise",
            "severities": "medium,high",
            "selection_seed": 99,
            "perturbation_seed": 101,
            "output_tag": "stress_debug",
        },
    )

    assert updated["experiment_type"] == "perturbation_eval"
    assert updated["perturbation"]["source_split"] == "validation"
    assert updated["perturbation"]["max_source_samples"] == 12
    assert updated["perturbation"]["families"] == ["slang_rewrite", "typo_noise"]
    assert updated["perturbation"]["default_family_order"] == [
        "slang_rewrite",
        "typo_noise",
    ]
    assert updated["perturbation"]["severities"] == ["medium", "high"]
    assert updated["perturbation"]["selection_seed"] == 99
    assert updated["perturbation"]["perturbation_seed"] == 101
    assert updated["perturbation"]["output_tag"] == "stress_debug"


def test_select_source_samples_uses_validation_split_and_cap():
    samples = [
        _source_sample("train_0", split="train"),
        _source_sample("val_0"),
        _source_sample("val_1"),
        _source_sample("val_2"),
    ]

    selected_once = select_source_samples(
        samples,
        split="validation",
        max_samples=2,
        selection_seed=13,
    )
    selected_twice = select_source_samples(
        samples,
        split="validation",
        max_samples=2,
        selection_seed=13,
    )

    assert [sample["sample_id"] for sample in selected_once] == [
        sample["sample_id"] for sample in selected_twice
    ]
    assert len(selected_once) == 2
    assert all(sample["split"] == "validation" for sample in selected_once)


def test_generate_perturbation_suite_is_deterministic_and_expands_nine_variants():
    source_samples = [_source_sample("val_0")]

    suite_one = generate_perturbation_suite(
        source_samples,
        source_run_id="saved_run",
        model_name="distilbert",
        families=["typo_noise", "format_degradation", "slang_rewrite"],
        severities=["low", "medium", "high"],
        selection_seed=13,
        perturbation_seed=7,
    )
    suite_two = generate_perturbation_suite(
        source_samples,
        source_run_id="saved_run",
        model_name="distilbert",
        families=["typo_noise", "format_degradation", "slang_rewrite"],
        severities=["low", "medium", "high"],
        selection_seed=13,
        perturbation_seed=7,
    )

    assert suite_one.source_sample_count == 1
    assert suite_one.perturbed_sample_count == 9
    assert suite_one.to_records() == suite_two.to_records()
    assert len({sample["perturbed_sample_id"] for sample in suite_one.to_records()}) == 9
    assert {sample["perturbation_family"] for sample in suite_one.to_records()} == {
        "typo_noise",
        "format_degradation",
        "slang_rewrite",
    }
    assert {sample["severity"] for sample in suite_one.to_records()} == {
        "low",
        "medium",
        "high",
    }
    assert all(isinstance(sample["applied_operations"], list) for sample in suite_one.to_records())


def test_build_perturbed_sample_id_is_stable():
    sample_id = build_perturbed_sample_id(
        "val_0",
        "typo_noise",
        "medium",
        7,
        "perturbed text",
    )

    assert sample_id == build_perturbed_sample_id(
        "val_0",
        "typo_noise",
        "medium",
        7,
        "perturbed text",
    )
    assert sample_id != build_perturbed_sample_id(
        "val_0",
        "typo_noise",
        "high",
        7,
        "perturbed text",
    )
