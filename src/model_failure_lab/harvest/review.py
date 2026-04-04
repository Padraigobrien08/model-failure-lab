"""Review and promote harvested draft dataset packs."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from model_failure_lab.datasets import FailureDataset, load_dataset
from model_failure_lab.schemas import JsonValue, PromptCase
from model_failure_lab.storage import write_json
from model_failure_lab.storage.layout import dataset_file, project_root

_SEGMENT_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(slots=True, frozen=True)
class HarvestDuplicateGroup:
    canonical_case_id: str
    kept_case_id: str
    case_ids: tuple[str, ...]
    source_case_ids: tuple[str, ...]
    size: int
    match_kind: str


@dataclass(slots=True, frozen=True)
class HarvestReviewSummary:
    dataset: FailureDataset
    draft_path: Path
    total_cases: int
    unique_case_count: int
    duplicate_case_count: int
    duplicate_groups: tuple[HarvestDuplicateGroup, ...]


@dataclass(slots=True, frozen=True)
class HarvestPromotionSummary:
    dataset: FailureDataset
    output_path: Path
    total_cases: int
    unique_case_count: int
    duplicate_case_count: int


def review_harvest_dataset(draft_path: str | Path) -> HarvestReviewSummary:
    source_path = Path(draft_path).resolve()
    dataset = load_dataset(source_path)
    _assert_harvest_dataset(dataset)
    groups = _build_duplicate_groups(dataset.cases)
    unique_case_count = len(groups)
    total_cases = len(dataset.cases)
    duplicate_case_count = total_cases - unique_case_count
    return HarvestReviewSummary(
        dataset=dataset,
        draft_path=source_path,
        total_cases=total_cases,
        unique_case_count=unique_case_count,
        duplicate_case_count=duplicate_case_count,
        duplicate_groups=groups,
    )


def promote_harvest_dataset(
    draft_path: str | Path,
    *,
    dataset_id: str,
    root: str | Path | None = None,
    output_path: str | Path | None = None,
    now: datetime | None = None,
) -> HarvestPromotionSummary:
    review = review_harvest_dataset(draft_path)
    normalized_dataset_id = _normalize_dataset_id(dataset_id)
    artifact_root = project_root(root).resolve()
    target_path = (
        _resolve_output_path(output_path, root=artifact_root)
        if output_path is not None
        else dataset_file(normalized_dataset_id, root=artifact_root, create=True).resolve()
    )

    case_map = {case.id: case for case in review.dataset.cases}
    curated_cases: list[PromptCase] = []
    for group in review.duplicate_groups:
        source_case = case_map[group.kept_case_id]
        metadata = dict(source_case.metadata)
        harvest_metadata = dict(metadata.get("harvest", {}))
        harvest_metadata["draft_case_id"] = source_case.id
        harvest_metadata["canonical_case_id"] = group.canonical_case_id
        harvest_metadata["duplicate_group_size"] = group.size
        harvest_metadata["duplicate_resolution"] = group.match_kind
        metadata["harvest"] = harvest_metadata

        curated_tags = list(source_case.tags)
        if "curated" not in curated_tags:
            curated_tags.append("curated")
        curated_cases.append(
            PromptCase(
                id=group.canonical_case_id,
                prompt=source_case.prompt,
                tags=tuple(curated_tags),
                expectations=source_case.expectations,
                metadata=metadata,
            )
        )

    promoted_at = _timestamp(now)
    harvest_metadata = dict(review.dataset.metadata.get("harvest", {}))
    harvest_metadata["draft_dataset_id"] = review.dataset.dataset_id
    harvest_metadata["draft_case_count"] = review.total_cases
    harvest_metadata["unique_case_count"] = review.unique_case_count
    harvest_metadata["duplicate_case_count"] = review.duplicate_case_count
    harvest_metadata["promoted_at"] = promoted_at

    source_payload = dict(review.dataset.source)
    source_payload["draft_dataset_id"] = review.dataset.dataset_id
    source_payload["draft_path"] = str(review.draft_path)

    promoted_dataset = FailureDataset(
        dataset_id=normalized_dataset_id,
        name=_titleize_dataset_id(normalized_dataset_id),
        description=review.dataset.description,
        version=review.dataset.version,
        created_at=promoted_at,
        lifecycle="curated",
        source=source_payload,
        cases=tuple(curated_cases),
        metadata={**review.dataset.metadata, "harvest": harvest_metadata},
    )
    write_json(target_path, promoted_dataset.to_payload())
    return HarvestPromotionSummary(
        dataset=promoted_dataset,
        output_path=target_path,
        total_cases=review.total_cases,
        unique_case_count=review.unique_case_count,
        duplicate_case_count=review.duplicate_case_count,
    )


def _build_duplicate_groups(cases: tuple[PromptCase, ...]) -> tuple[HarvestDuplicateGroup, ...]:
    grouped: dict[str, list[PromptCase]] = {}
    match_kind_by_key: dict[str, str] = {}
    for case in cases:
        canonical_key = _canonical_key(case)
        grouped.setdefault(canonical_key, []).append(case)
        exact_match = len({_exact_prompt_hash(candidate) for candidate in grouped[canonical_key]}) == 1
        match_kind_by_key[canonical_key] = "exact_prompt_match" if exact_match else "normalized_prompt_match"

    groups: list[HarvestDuplicateGroup] = []
    for canonical_key, grouped_cases in sorted(grouped.items()):
        ordered_cases = sorted(grouped_cases, key=lambda candidate: candidate.id)
        kept_case = ordered_cases[0]
        groups.append(
            HarvestDuplicateGroup(
                canonical_case_id=_canonical_case_id(canonical_key),
                kept_case_id=kept_case.id,
                case_ids=tuple(case.id for case in ordered_cases),
                source_case_ids=tuple(
                    _source_case_id(case) for case in ordered_cases
                ),
                size=len(ordered_cases),
                match_kind=match_kind_by_key[canonical_key],
            )
        )
    return tuple(groups)


def _canonical_key(case: PromptCase) -> str:
    expectations_payload = (
        case.expectations.to_payload() if case.expectations is not None else None
    )
    serialized = json.dumps(expectations_payload, sort_keys=True)
    normalized_prompt = " ".join(case.prompt.lower().split())
    return hashlib.sha1(f"{normalized_prompt}\n{serialized}".encode("utf-8")).hexdigest()


def _canonical_case_id(canonical_key: str) -> str:
    return f"case-{canonical_key[:16]}"


def _exact_prompt_hash(case: PromptCase) -> str:
    harvest_metadata = case.metadata.get("harvest", {})
    if isinstance(harvest_metadata, dict):
        exact_hash = harvest_metadata.get("exact_prompt_hash")
        if isinstance(exact_hash, str) and exact_hash:
            return exact_hash
    return hashlib.sha1(case.prompt.encode("utf-8")).hexdigest()


def _source_case_id(case: PromptCase) -> str:
    harvest_metadata = case.metadata.get("harvest", {})
    if isinstance(harvest_metadata, dict):
        source_case_id = harvest_metadata.get("source_case_id")
        if isinstance(source_case_id, str) and source_case_id:
            return source_case_id
    return case.id


def _assert_harvest_dataset(dataset: FailureDataset) -> None:
    source_type = dataset.source.get("type")
    if source_type != "artifact_harvest":
        raise ValueError("dataset is not an artifact harvest pack")


def _resolve_output_path(output_path: str | Path, *, root: Path) -> Path:
    target = Path(output_path)
    if not target.is_absolute():
        target = root / target
    if target.suffix.lower() != ".json":
        raise ValueError("promotion output path must be a .json file")
    return target.resolve()


def _normalize_dataset_id(value: str) -> str:
    normalized = _SEGMENT_PATTERN.sub("-", value.strip().lower()).strip("-")
    if not normalized:
        raise ValueError("dataset_id must contain at least one alphanumeric character")
    return normalized


def _titleize_dataset_id(value: str) -> str:
    return value.replace("-", " ").replace("_", " ").title()


def _timestamp(now: datetime | None) -> str:
    current_time = now or datetime.now(timezone.utc)
    return current_time.isoformat().replace("+00:00", "Z")
