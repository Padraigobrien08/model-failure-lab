"""TF-IDF plus Logistic Regression baseline training."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from model_failure_lab.data import CanonicalDataset, prepare_tfidf_adapter

from .common import (
    compute_binary_classification_metrics,
    load_baseline_canonical_dataset,
    set_random_seed,
)
from .export import build_prediction_records, write_prediction_exports

DatasetLoader = Callable[..., CanonicalDataset]


@dataclass(slots=True)
class LogisticBaselineArtifacts:
    """Artifacts produced by a completed logistic baseline run."""

    metrics_payload: dict[str, Any]
    prediction_paths: dict[str, Path]
    vectorizer_path: Path
    model_path: Path
    checkpoint_dir: Path


def _checkpoint_paths(run_dir: Path) -> tuple[Path, Path, Path]:
    checkpoint_dir = run_dir / "checkpoint"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    return (
        checkpoint_dir,
        checkpoint_dir / "vectorizer.joblib",
        checkpoint_dir / "logistic_model.joblib",
    )


def train_logistic_baseline(
    config: dict[str, Any],
    run_dir: Path,
    *,
    dataset_loader: DatasetLoader | None = None,
) -> LogisticBaselineArtifacts:
    """Train the canonical TF-IDF plus Logistic Regression baseline."""
    set_random_seed(int(config["seed"]))
    resolved_loader = dataset_loader or load_baseline_canonical_dataset
    dataset = resolved_loader(config, download=True)
    train_view = prepare_tfidf_adapter(dataset.samples, split="train")
    validation_view = prepare_tfidf_adapter(dataset.samples, split="validation")

    model_config = dict(config.get("model", {}))
    vectorizer_config = dict(model_config.get("vectorizer", {}))
    classifier_config = dict(model_config.get("classifier", {}))

    vectorizer = TfidfVectorizer(
        ngram_range=tuple(vectorizer_config.get("ngram_range", [1, 2])),
        lowercase=bool(vectorizer_config.get("lowercase", True)),
        min_df=int(vectorizer_config.get("min_df", 3)),
        max_df=float(vectorizer_config.get("max_df", 0.95)),
        max_features=int(vectorizer_config.get("max_features", 50000)),
        strip_accents=vectorizer_config.get("strip_accents", "unicode"),
        sublinear_tf=bool(vectorizer_config.get("sublinear_tf", True)),
    )
    classifier = LogisticRegression(
        penalty=str(classifier_config.get("penalty", "l2")),
        C=float(classifier_config.get("c", 1.0)),
        solver=str(classifier_config.get("solver", "liblinear")),
        class_weight=classifier_config.get("class_weight", "balanced"),
        max_iter=int(classifier_config.get("max_iter", 1000)),
        random_state=int(config["seed"]),
    )

    train_matrix = vectorizer.fit_transform(train_view.texts)
    validation_matrix = vectorizer.transform(validation_view.texts)
    classifier.fit(train_matrix, train_view.labels)

    train_probability_rows = classifier.predict_proba(train_matrix).tolist()
    train_predicted_labels = classifier.predict(train_matrix).tolist()
    probability_rows = classifier.predict_proba(validation_matrix).tolist()
    predicted_labels = classifier.predict(validation_matrix).tolist()
    probability_positive = [float(row[1]) for row in probability_rows]
    validation_metrics = compute_binary_classification_metrics(
        true_labels=[int(label) for label in validation_view.labels],
        predicted_labels=[int(label) for label in predicted_labels],
        probability_positive=probability_positive,
    )

    primary_metric_name = str(config.get("eval", {}).get("primary_metric", "macro_f1"))
    metrics_payload = {
        "primary_metric": {
            "name": primary_metric_name,
            "value": validation_metrics.get(primary_metric_name),
        },
        "worst_group_metric": {
            "name": str(config.get("eval", {}).get("worst_group_metric", "accuracy")),
            "value": None,
        },
        "robustness_gap": {
            "name": str(config.get("eval", {}).get("robustness_gap_metric", "accuracy_delta")),
            "value": None,
        },
        "calibration_metric": {
            "name": str(config.get("eval", {}).get("calibration_metric", "ece")),
            "value": None,
        },
        "validation_metrics": validation_metrics,
    }

    prediction_paths = write_prediction_exports(
        run_dir,
        {
            "train": build_prediction_records(
                run_id=str(config["run_id"]),
                model_name=str(config["model_name"]),
                sample_ids=train_view.sample_ids,
                splits=train_view.splits,
                true_labels=[int(label) for label in train_view.labels],
                predicted_labels=[int(label) for label in train_predicted_labels],
                probability_rows=[
                    [float(row[0]), float(row[1])] for row in train_probability_rows
                ],
                group_ids=train_view.group_ids,
                is_id_flags=train_view.is_id_flags,
                is_ood_flags=train_view.is_ood_flags,
            ),
            "validation": build_prediction_records(
                run_id=str(config["run_id"]),
                model_name=str(config["model_name"]),
                sample_ids=validation_view.sample_ids,
                splits=validation_view.splits,
                true_labels=[int(label) for label in validation_view.labels],
                predicted_labels=[int(label) for label in predicted_labels],
                probability_rows=[[float(row[0]), float(row[1])] for row in probability_rows],
                group_ids=validation_view.group_ids,
                is_id_flags=validation_view.is_id_flags,
                is_ood_flags=validation_view.is_ood_flags,
            ),
        },
    )

    checkpoint_dir, vectorizer_path, model_path = _checkpoint_paths(run_dir)
    joblib.dump(vectorizer, vectorizer_path)
    joblib.dump(classifier, model_path)

    return LogisticBaselineArtifacts(
        metrics_payload=metrics_payload,
        prediction_paths=prediction_paths,
        vectorizer_path=vectorizer_path,
        model_path=model_path,
        checkpoint_dir=checkpoint_dir,
    )
