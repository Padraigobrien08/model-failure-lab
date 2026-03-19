"""CivilComments data loading and materialization helpers."""

from .adapters import (
    TfidfAdapterView,
    TransformerAdapterView,
    prepare_tfidf_adapter,
    prepare_transformer_adapter,
)
from .canonical import build_canonical_dataset, build_canonical_samples, build_sample_id
from .civilcomments import DataDependencyError, load_civilcomments_dataset, resolve_split_policy
from .grouping import build_group_attributes, build_group_id
from .materialization import (
    MaterializationResult,
    build_data_manifest_payload,
    extract_source_records,
    load_canonical_civilcomments_dataset,
    materialize_civilcomments,
    write_data_manifest,
)
from .schema import CanonicalDataset, CanonicalSample
from .validation import validate_canonical_dataset, write_validation_summaries

__all__ = [
    "CanonicalDataset",
    "CanonicalSample",
    "DataDependencyError",
    "MaterializationResult",
    "TfidfAdapterView",
    "TransformerAdapterView",
    "build_canonical_dataset",
    "build_canonical_samples",
    "build_data_manifest_payload",
    "build_group_attributes",
    "build_group_id",
    "load_civilcomments_dataset",
    "extract_source_records",
    "load_canonical_civilcomments_dataset",
    "materialize_civilcomments",
    "prepare_tfidf_adapter",
    "prepare_transformer_adapter",
    "resolve_split_policy",
    "build_sample_id",
    "validate_canonical_dataset",
    "write_validation_summaries",
    "write_data_manifest",
]
