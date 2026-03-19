from __future__ import annotations

import pandas as pd

from model_failure_lab.models.export import (
    REQUIRED_PREDICTION_COLUMNS,
    build_prediction_records,
    write_prediction_exports,
)
from model_failure_lab.utils.paths import build_baseline_run_dir


def test_write_prediction_exports_uses_split_specific_filenames(temp_artifact_root):
    run_dir = build_baseline_run_dir("logistic_tfidf", "prediction_contract", create=True)
    split_records = {
        "train": build_prediction_records(
            run_id="prediction_contract",
            model_name="logistic_tfidf",
            sample_ids=["train_0"],
            splits=["train"],
            true_labels=[0],
            predicted_labels=[0],
            probability_rows=[[0.9, 0.1]],
            group_ids=["group_a"],
            is_id_flags=[True],
            is_ood_flags=[False],
        ),
        "validation": build_prediction_records(
            run_id="prediction_contract",
            model_name="logistic_tfidf",
            sample_ids=["val_0"],
            splits=["validation"],
            true_labels=[1],
            predicted_labels=[1],
            probability_rows=[[0.2, 0.8]],
            group_ids=["group_b"],
            is_id_flags=[False],
            is_ood_flags=[True],
            logits_rows=[[0.1, 0.9]],
        ),
    }

    written_paths = write_prediction_exports(run_dir, split_records)

    assert written_paths["train"].name == "predictions_train.parquet"
    assert written_paths["validation"].name == "predictions_val.parquet"
    validation_frame = pd.read_parquet(written_paths["validation"])
    assert (
        list(validation_frame.columns[: len(REQUIRED_PREDICTION_COLUMNS)])
        == REQUIRED_PREDICTION_COLUMNS
    )
    assert "logit_0" in validation_frame.columns
    assert "logit_1" in validation_frame.columns


def test_logistic_and_distilbert_records_share_required_schema():
    logistic_records = build_prediction_records(
        run_id="run_a",
        model_name="logistic_tfidf",
        sample_ids=["sample_a"],
        splits=["validation"],
        true_labels=[0],
        predicted_labels=[0],
        probability_rows=[[0.7, 0.3]],
        group_ids=["group_a"],
        is_id_flags=[False],
        is_ood_flags=[True],
    )
    distilbert_records = build_prediction_records(
        run_id="run_b",
        model_name="distilbert",
        sample_ids=["sample_b"],
        splits=["validation"],
        true_labels=[1],
        predicted_labels=[1],
        probability_rows=[[0.1, 0.9]],
        group_ids=["group_b"],
        is_id_flags=[False],
        is_ood_flags=[True],
        logits_rows=[[0.2, 0.8]],
    )

    logistic_columns = list(pd.DataFrame(logistic_records).columns)
    distilbert_columns = list(pd.DataFrame(distilbert_records).columns)

    assert logistic_columns[: len(REQUIRED_PREDICTION_COLUMNS)] == REQUIRED_PREDICTION_COLUMNS
    assert distilbert_columns[: len(REQUIRED_PREDICTION_COLUMNS)] == REQUIRED_PREDICTION_COLUMNS
