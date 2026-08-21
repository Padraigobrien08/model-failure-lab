"""`failure-lab init` scaffolds a valid starter dataset the runner can execute."""

from __future__ import annotations

import json

from model_failure_lab.cli import main
from model_failure_lab.datasets import FailureDataset


def test_init_scaffolds_runnable_starter_dataset(tmp_path, capsys) -> None:
    assert main(["init", "--root", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "Dataset ID: my-prompts-v1" in output
    assert "Next steps:" in output

    dataset_path = tmp_path / "datasets" / "my-prompts-v1.json"
    dataset = FailureDataset.from_payload(json.loads(dataset_path.read_text(encoding="utf-8")))
    assert dataset.dataset_id == "my-prompts-v1"
    assert len(dataset.cases) == 3

    assert main(["run", "--dataset", "my-prompts-v1", "--model", "demo", "--root", str(tmp_path)]) == 0


def test_init_refuses_to_overwrite_without_force(tmp_path, capsys) -> None:
    assert main(["init", "--root", str(tmp_path)]) == 0
    capsys.readouterr()
    assert main(["init", "--root", str(tmp_path)]) == 1
    assert "--force" in capsys.readouterr().err
    assert main(["init", "--root", str(tmp_path), "--force"]) == 0


def test_init_from_jsonl(tmp_path, capsys) -> None:
    jsonl = tmp_path / "prompts.jsonl"
    jsonl.write_text(
        '{"prompt": "What is 2+2?", "reference_answer": "4"}\n'
        '{"prompt": "Name the largest planet.", "id": "planet", "tags": ["astro"]}\n',
        encoding="utf-8",
    )
    assert main(["init", "--from-jsonl", str(jsonl), "--id", "imported-v1", "--root", str(tmp_path)]) == 0
    dataset_path = tmp_path / "datasets" / "imported-v1.json"
    dataset = FailureDataset.from_payload(json.loads(dataset_path.read_text(encoding="utf-8")))
    assert [case.id for case in dataset.cases] == ["case-0001", "planet"]
    assert dataset.cases[1].tags == ("astro",)


def test_init_from_jsonl_rejects_missing_prompt(tmp_path, capsys) -> None:
    jsonl = tmp_path / "bad.jsonl"
    jsonl.write_text('{"id": "no-prompt"}\n', encoding="utf-8")
    assert main(["init", "--from-jsonl", str(jsonl), "--root", str(tmp_path)]) == 1
    assert '"prompt"' in capsys.readouterr().err
