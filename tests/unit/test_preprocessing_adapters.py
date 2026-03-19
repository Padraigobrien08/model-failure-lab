from __future__ import annotations

import json
from copy import deepcopy

from model_failure_lab.config.loader import load_experiment_config
from model_failure_lab.data import (
    build_canonical_dataset,
    prepare_tfidf_adapter,
    prepare_transformer_adapter,
    write_validation_summaries,
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


def _build_canonical_samples():
    config = load_experiment_config("configs/experiments/civilcomments_logistic_baseline.yaml")
    data_config = deepcopy(config["data"])
    data_config["validation"]["subgroup_min_samples_warning"] = 1
    data_config["validation"]["preview_samples"] = 2
    dataset = build_canonical_dataset(_build_source_records(), data_config)
    return dataset.samples, data_config


def test_prepare_tfidf_and_transformer_adapters_share_canonical_inputs():
    samples, _ = _build_canonical_samples()

    tfidf_view = prepare_tfidf_adapter(samples)
    transformer_view = prepare_transformer_adapter(
        samples,
        tokenizer_name="distilbert-base-uncased",
    )

    assert len(tfidf_view.texts) == len(samples)
    assert tfidf_view.sample_ids[0] == transformer_view.records[0]["sample_id"]
    assert tfidf_view.splits == [record["split"] for record in transformer_view.records]
    assert transformer_view.preprocessing_config["tokenizer_name"] == "distilbert-base-uncased"


def test_write_validation_summaries_persists_required_bundle(temp_artifact_root):
    samples, data_config = _build_canonical_samples()
    summary_dir = temp_artifact_root / "data" / "summaries"

    validation_summary = write_validation_summaries(
        samples,
        summary_dir,
        allowed_splits=set(data_config["split_role_policy"]),
        subgroup_min_samples_warning=1,
        preview_limit=2,
    )

    expected_files = {
        "split_counts.csv",
        "label_distribution.csv",
        "subgroup_coverage.csv",
        "text_length_summary.csv",
        "data_validation.json",
        "sample_preview.jsonl",
    }
    assert expected_files == {path.name for path in summary_dir.iterdir()}
    payload = json.loads((summary_dir / "data_validation.json").read_text(encoding="utf-8"))
    assert payload["sample_count"] == validation_summary["sample_count"]
    assert payload["split_integrity"]["valid"] is True
    preview_lines = (summary_dir / "sample_preview.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(preview_lines) == 2
