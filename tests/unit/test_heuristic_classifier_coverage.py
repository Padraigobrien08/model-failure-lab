"""heuristic_v1 declares an honest, tested subset of the failure taxonomy.

The full taxonomy defines eight failure types, but the baseline classifier can only emit
four (plus no_failure). This test pins that declared subset so the gap stays explicit
rather than silently over-claiming coverage across filters and governance.
"""

from __future__ import annotations

from model_failure_lab.adapters import ModelResult
from model_failure_lab.classifiers.contracts import ClassifierExpectations, ClassifierInput
from model_failure_lab.classifiers.heuristic import (
    HEURISTIC_V1_EMITTED_FAILURE_TYPES,
    heuristic_classifier,
)
from model_failure_lab.schemas.taxonomy import FAILURE_TYPES


def test_declared_subset_is_strict_and_documents_the_gap() -> None:
    full = set(FAILURE_TYPES)
    declared = set(HEURISTIC_V1_EMITTED_FAILURE_TYPES)
    assert declared < full  # strict subset
    # The types the baseline classifier cannot produce, called out explicitly.
    assert full - declared == {"retrieval", "safety", "format", "tool_use"}


def _classify(text: str, *, reference: str | None = None) -> str:
    expectations = (
        ClassifierExpectations(reference_answer=reference) if reference is not None else None
    )
    result = heuristic_classifier(
        ClassifierInput(output=ModelResult(text=text), expectations=expectations)
    )
    return result.failure_type


def test_emitted_types_stay_within_the_declared_subset() -> None:
    samples = [
        _classify("the answer is 42"),  # no_failure
        _classify("wrong", reference="the correct answer"),  # reasoning
        _classify("according to a study everything is fine"),  # hallucination
    ]
    for failure_type in samples:
        assert failure_type in HEURISTIC_V1_EMITTED_FAILURE_TYPES


# ---------------------------------------------------------------------------------------
# The gap is declared in code. It also has to be visible to whoever runs the tool.
# ---------------------------------------------------------------------------------------
#
# `rag-failures-v1` ships as a core bundled dataset with
# `metadata.target_failure_type: retrieval` -- a type no registered classifier can emit. A
# run over it reports `hallucination` and `instruction_following` and nothing on screen
# explained why the type the dataset exists to find never appeared.


def test_every_bundled_dataset_target_is_either_emittable_or_flagged_on_run(
    tmp_path, capsys
) -> None:
    from model_failure_lab.cli import main
    from model_failure_lab.datasets import available_bundled_datasets

    for dataset in available_bundled_datasets():
        target = dataset.target_failure_type
        if not isinstance(target, str) or target in HEURISTIC_V1_EMITTED_FAILURE_TYPES:
            continue
        root = tmp_path / dataset.dataset_id
        root.mkdir()
        assert main(["run", "--dataset", dataset.dataset_id, "--model", "demo",
                     "--root", str(root)]) == 0
        output = capsys.readouterr().out
        assert f"targets '{target}'" in output, (
            f"{dataset.dataset_id} declares an unreachable target failure type "
            f"'{target}' and the run says nothing about it"
        )
        assert "cannot emit" in output


def test_a_reachable_target_prints_no_note(tmp_path, capsys) -> None:
    root = tmp_path / "reachable"
    root.mkdir()
    assert main_run(root) == 0
    assert "cannot emit" not in capsys.readouterr().out


def main_run(root) -> int:
    from model_failure_lab.cli import main

    # reasoning-failures-v1 targets `reasoning`, which heuristic_v1 does emit.
    return main(["run", "--dataset", "reasoning-failures-v1", "--model", "demo",
                 "--root", str(root)])
