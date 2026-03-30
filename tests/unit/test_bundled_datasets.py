from __future__ import annotations

from model_failure_lab.datasets import (
    available_bundled_dataset_ids,
    available_bundled_datasets,
    load_bundled_dataset,
)


def test_reasoning_pack_is_registered_and_loads_by_canonical_id() -> None:
    assert "reasoning-failures-v1" in available_bundled_dataset_ids()

    dataset = load_bundled_dataset("reasoning-failures-v1", include_extended=True)

    assert dataset.dataset_id == "reasoning-failures-v1"
    assert len(dataset.cases) == 12


def test_reasoning_pack_orders_core_cases_before_extended_tail() -> None:
    dataset = load_bundled_dataset("reasoning-failures-v1", include_extended=True)

    core_cases = dataset.cases[:8]
    extended_cases = dataset.cases[8:]

    assert all("core" in case.tags for case in core_cases)
    assert all("extended" in case.tags for case in extended_cases)
    assert sum(
        1
        for case in dataset.cases
        if case.expectations and case.expectations.expected_failure == "no_failure"
    ) == 2


def test_hallucination_pack_is_registered_and_loads_by_canonical_id() -> None:
    assert "hallucination-failures-v1" in available_bundled_dataset_ids()

    dataset = load_bundled_dataset("hallucination-failures-v1", include_extended=True)

    assert dataset.dataset_id == "hallucination-failures-v1"
    assert len(dataset.cases) == 12


def test_rag_pack_is_registered_and_loads_by_canonical_id() -> None:
    assert "rag-failures-v1" in available_bundled_dataset_ids()

    dataset = load_bundled_dataset("rag-failures-v1", include_extended=True)

    assert dataset.dataset_id == "rag-failures-v1"
    assert len(dataset.cases) == 12


def test_bundled_packs_share_structural_tags_and_control_posture() -> None:
    reasoning = load_bundled_dataset("reasoning-failures-v1", include_extended=True)
    hallucination = load_bundled_dataset("hallucination-failures-v1", include_extended=True)
    rag = load_bundled_dataset("rag-failures-v1", include_extended=True)

    for dataset in (reasoning, hallucination, rag):
        core_cases = dataset.cases[:8]
        extended_cases = dataset.cases[8:]
        control_cases = [
            case
            for case in dataset.cases
            if case.expectations and case.expectations.expected_failure == "no_failure"
        ]

        assert all("core" in case.tags for case in core_cases)
        assert all("extended" in case.tags for case in extended_cases)
        assert len(control_cases) == 2
        assert all("control" in case.tags for case in control_cases)


def test_rag_pack_authors_grounding_expectations_and_registry_summaries() -> None:
    dataset = load_bundled_dataset("rag-failures-v1", include_extended=True)
    summaries = {summary.dataset_id: summary for summary in available_bundled_datasets()}

    grounding_cases = [
        case
        for case in dataset.cases
        if case.expectations is not None
        and case.expectations.context is not None
        and (
            case.expectations.context.evidence_items
            or case.expectations.context.required_sources
        )
    ]

    assert grounding_cases
    assert summaries["rag-failures-v1"].target_failure_type == "retrieval"
    assert summaries["rag-failures-v1"].core_case_count == 8
    assert summaries["rag-failures-v1"].full_case_count == 12
