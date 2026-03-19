"""Deterministic perturbation generation helpers."""

from .bundle import build_suite_manifest_payload, write_perturbation_bundle
from .generation import (
    DEFAULT_SLANG_MAPPING,
    apply_format_degradation,
    apply_slang_rewrite,
    apply_typo_noise,
    generate_perturbation_suite,
)
from .loaders import load_clean_source_predictions, load_saved_perturbation_predictions
from .metrics import (
    build_family_severity_matrix,
    build_family_summary,
    build_severity_summary,
    build_source_delta_summary,
    build_suite_summary,
)
from .schema import (
    SCHEMA_VERSION,
    PerturbationSuite,
    PerturbedSample,
    build_perturbed_sample_id,
)
from .scoring import SavedRunScorer, load_saved_run_scorer, score_perturbation_suite
from .selection import select_source_samples

__all__ = [
    "DEFAULT_SLANG_MAPPING",
    "SCHEMA_VERSION",
    "PerturbationSuite",
    "PerturbedSample",
    "SavedRunScorer",
    "apply_format_degradation",
    "apply_slang_rewrite",
    "apply_typo_noise",
    "build_family_severity_matrix",
    "build_family_summary",
    "build_perturbed_sample_id",
    "build_severity_summary",
    "build_source_delta_summary",
    "build_suite_manifest_payload",
    "build_suite_summary",
    "generate_perturbation_suite",
    "load_clean_source_predictions",
    "load_saved_perturbation_predictions",
    "load_saved_run_scorer",
    "score_perturbation_suite",
    "select_source_samples",
    "write_perturbation_bundle",
]
