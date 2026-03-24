"""Shared constants for the artifact-index contract."""

from __future__ import annotations

ARTIFACT_INDEX_SCHEMA_VERSION = "artifact_index_v1"
DEFAULT_ARTIFACT_INDEX_VERSION = "v1"

OFFICIAL_RUN_GROUPS = {
    "baselines_v1_2_logistic",
    "baselines_v1_2_distilbert",
    "temperature_scaling_v1_2",
    "reweighting_v1_2",
}

DEFAULT_VISIBLE_REPORT_SCOPES = {
    "phase18_temperature_scaling_seeded",
    "phase19_reweighting_seeded",
    "phase20_stability",
    "phase26_robustness_final",
}

OFFICIAL_REPORT_SCOPE_PREFIXES = (
    "phase18_temperature_scaling_seed_",
    "phase18_temperature_scaling_seeded",
    "phase19_reweighting_seed_",
    "phase19_reweighting_seeded",
    "phase19_three_way_seed_",
    "phase20_stability",
    "phase26_robustness_final",
)

PRIMARY_COHORT_DEFINITIONS = {
    "baselines_v1_2_logistic": {
        "cohort_id": "logistic_baseline",
        "cohort_type": "baseline",
        "model_name": "logistic_tfidf",
        "mitigation_method": None,
        "display_name": "Logistic TF-IDF Baseline",
    },
    "baselines_v1_2_distilbert": {
        "cohort_id": "distilbert_baseline",
        "cohort_type": "baseline",
        "model_name": "distilbert",
        "mitigation_method": None,
        "display_name": "DistilBERT Baseline",
    },
    "temperature_scaling_v1_2": {
        "cohort_id": "temperature_scaling",
        "cohort_type": "mitigation",
        "model_name": "distilbert",
        "mitigation_method": "temperature_scaling",
        "display_name": "Temperature Scaling",
    },
    "reweighting_v1_2": {
        "cohort_id": "reweighting",
        "cohort_type": "mitigation",
        "model_name": "distilbert",
        "mitigation_method": "reweighting",
        "display_name": "Reweighting",
    },
}

PRIMARY_COHORT_ORDER = [
    "logistic_baseline",
    "distilbert_baseline",
    "temperature_scaling",
    "reweighting",
]

METRIC_KEYS = [
    "id_macro_f1",
    "ood_macro_f1",
    "robustness_gap_f1",
    "worst_group_f1",
    "ece",
    "brier_score",
]
