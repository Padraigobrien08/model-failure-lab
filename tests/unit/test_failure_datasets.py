from __future__ import annotations

import json

import pytest

import model_failure_lab.datasets as datasets_module
from model_failure_lab.datasets import (
    FailureDataset,
    available_bundled_dataset_ids,
    load_bundled_dataset,
    load_dataset,
    parse_dataset_payload,
)
from model_failure_lab.schemas import PayloadValidationError, PromptCase, PromptExpectations


def test_parse_dataset_payload_accepts_envelope_shape() -> None:
    dataset = parse_dataset_payload(
        {
            "dataset_id": "reasoning-basics-v1",
            "name": "Reasoning Basics",
            "description": "Small baseline set",
            "version": "1",
            "created_at": "2026-04-03T00:00:00Z",
            "lifecycle": "draft",
            "source": {
                "type": "artifact_harvest",
                "filters": {"failure_type": "reasoning"},
            },
            "cases": [
                {
                    "id": "case-001",
                    "prompt": "Explain why 2 + 2 = 4.",
                    "expectations": {"expected_failure": "reasoning"},
                }
            ],
        }
    )

    assert dataset == FailureDataset(
        dataset_id="reasoning-basics-v1",
        name="Reasoning Basics",
        description="Small baseline set",
        version="1",
        created_at="2026-04-03T00:00:00Z",
        lifecycle="draft",
        source={
            "type": "artifact_harvest",
            "filters": {"failure_type": "reasoning"},
        },
        cases=(
            PromptCase(
                id="case-001",
                prompt="Explain why 2 + 2 = 4.",
                expectations=PromptExpectations(expected_failure="reasoning"),
            ),
        ),
    )


def test_failure_dataset_to_payload_preserves_harvest_fields() -> None:
    dataset = FailureDataset(
        dataset_id="harvested-pack-v1",
        created_at="2026-04-03T00:00:00Z",
        lifecycle="curated",
        source={"type": "artifact_harvest", "filters": {"delta": "regression"}},
        cases=(PromptCase(id="case-001", prompt="Prompt"),),
    )

    assert dataset.to_payload() == {
        "dataset_id": "harvested-pack-v1",
        "created_at": "2026-04-03T00:00:00Z",
        "lifecycle": "curated",
        "source": {"type": "artifact_harvest", "filters": {"delta": "regression"}},
        "cases": [
            {
                "id": "case-001",
                "prompt": "Prompt",
                "tags": [],
                "metadata": {},
            }
        ],
    }


def test_parse_dataset_payload_accepts_bare_case_list_with_fallback_metadata() -> None:
    dataset = parse_dataset_payload(
        [
            {
                "id": "case-001",
                "prompt": "Explain why 2 + 2 = 4.",
            }
        ],
        fallback_dataset_id="Reasoning Basics",
    )

    assert dataset.dataset_id == "reasoning-basics"
    assert dataset.name == "Reasoning Basics"
    assert dataset.cases == (PromptCase(id="case-001", prompt="Explain why 2 + 2 = 4."),)


def test_load_dataset_reads_json_file_into_normalized_contract(tmp_path) -> None:
    dataset_path = tmp_path / "reasoning_set.json"
    dataset_path.write_text(
        json.dumps(
            {
                "dataset_id": "reasoning-set",
                "cases": [
                    {
                        "id": "case-001",
                        "prompt": "Compute the answer.",
                        "expected_failure": "reasoning",
                        "metadata": {"reference_answer": "42"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    dataset = load_dataset(dataset_path)

    assert dataset.dataset_id == "reasoning-set"
    assert dataset.cases[0].expectations == PromptExpectations(
        expected_failure="reasoning",
        reference_answer="42",
    )
    assert dataset.cases[0].metadata == {}


def test_parse_dataset_payload_rejects_invalid_root_shape() -> None:
    with pytest.raises(PayloadValidationError, match="list or an object with cases"):
        parse_dataset_payload("not a dataset")


def test_parse_dataset_payload_rejects_envelope_without_cases() -> None:
    with pytest.raises(PayloadValidationError, match="dataset envelope must contain cases"):
        parse_dataset_payload({"dataset_id": "broken"})


def test_available_bundled_dataset_ids_exposes_reasoning_pack() -> None:
    bundled_ids = available_bundled_dataset_ids()

    assert "reasoning-failures-v1" in bundled_ids
    assert "hallucination-failures-v1" in bundled_ids
    assert "rag-failures-v1" in bundled_ids


def test_load_bundled_dataset_defaults_to_core_cases_only() -> None:
    dataset = load_bundled_dataset("reasoning-failures-v1")

    assert dataset.dataset_id == "reasoning-failures-v1"
    assert len(dataset.cases) == 8
    assert all("core" in case.tags for case in dataset.cases)
    assert sum(
        1
        for case in dataset.cases
        if case.expectations and case.expectations.expected_failure == "no_failure"
    ) == 2


def test_load_demo_dataset_surfaces_packaged_install_error_when_asset_is_missing(
    monkeypatch, tmp_path
) -> None:
    missing_path = tmp_path / "missing-demo-dataset.json"
    monkeypatch.setattr(datasets_module, "demo_dataset_path", lambda: missing_path)

    with pytest.raises(FileNotFoundError) as exc_info:
        datasets_module.load_demo_dataset()

    message = str(exc_info.value)
    assert "bundled demo dataset asset `demo_dataset.json`" in message.lower()
    assert "installed `model-failure-lab` package" in message
    assert str(missing_path) not in message
