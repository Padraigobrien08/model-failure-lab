"""Deterministic dataset evolution driven by persisted comparison signals."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from model_failure_lab.schemas import JsonValue, PromptCase
from model_failure_lab.storage import dataset_file, datasets_root, write_json
from model_failure_lab.storage.layout import project_root

from .contracts import FailureDataset
from .load import load_dataset

_SEGMENT_PATTERN = re.compile(r"[^a-z0-9]+")
_VERSION_SUFFIX_PATTERN = re.compile(r"^(?P<family>.+)-v(?P<number>[0-9]+)$")
_DEFAULT_SIGNAL_PACK_LIMIT = 10


@dataclass(slots=True, frozen=True)
class RegressionPackPolicy:
    top_n: int
    failure_type: str | None
    strategy: str = "signal_top_drivers_then_regression_delta_order"
    delta_kind: str = "regression"

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "top_n": self.top_n,
            "failure_type": self.failure_type,
            "strategy": self.strategy,
            "delta_kind": self.delta_kind,
        }


@dataclass(slots=True, frozen=True)
class RegressionPackPreviewCase:
    case_id: str
    prompt_id: str
    prompt: str
    source_case_id: str
    source_report_id: str
    source_run_id: str
    driver_failure_type: str | None
    driver_rank: int | None
    transition_type: str

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "case_id": self.case_id,
            "prompt_id": self.prompt_id,
            "prompt": self.prompt,
            "source_case_id": self.source_case_id,
            "source_report_id": self.source_report_id,
            "source_run_id": self.source_run_id,
            "driver_failure_type": self.driver_failure_type,
            "driver_rank": self.driver_rank,
            "transition_type": self.transition_type,
        }


@dataclass(slots=True, frozen=True)
class RegressionPackDraftSummary:
    dataset: FailureDataset
    output_path: Path
    comparison_id: str
    suggested_family_id: str
    policy: RegressionPackPolicy
    signal: dict[str, JsonValue]
    preview_cases: tuple[RegressionPackPreviewCase, ...]

    @property
    def selected_case_count(self) -> int:
        return len(self.dataset.cases)

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "dataset_id": self.dataset.dataset_id,
            "lifecycle": self.dataset.lifecycle,
            "comparison_id": self.comparison_id,
            "suggested_family_id": self.suggested_family_id,
            "output_path": str(self.output_path),
            "selected_case_count": self.selected_case_count,
            "policy": self.policy.to_payload(),
            "signal": dict(self.signal),
            "preview_cases": [entry.to_payload() for entry in self.preview_cases],
        }


@dataclass(slots=True, frozen=True)
class RegressionPackSelectionSummary:
    comparison_id: str
    suggested_family_id: str
    policy: RegressionPackPolicy
    signal: dict[str, JsonValue]
    preview_cases: tuple[RegressionPackPreviewCase, ...]
    selected_rows: tuple[dict[str, Any], ...] = field(default_factory=tuple, repr=False)

    @property
    def selected_case_count(self) -> int:
        return len(self.selected_rows)

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "comparison_id": self.comparison_id,
            "suggested_family_id": self.suggested_family_id,
            "selected_case_count": self.selected_case_count,
            "policy": self.policy.to_payload(),
            "signal": dict(self.signal),
            "preview_cases": [entry.to_payload() for entry in self.preview_cases],
        }


@dataclass(slots=True, frozen=True)
class DatasetVersionRecord:
    family_id: str
    dataset_id: str
    version_number: int
    version_tag: str
    created_at: str | None
    case_count: int
    path: Path
    parent_dataset_id: str | None
    source_comparison_id: str | None
    signal_verdict: str | None
    severity: float | None

    def to_payload(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {
            "family_id": self.family_id,
            "dataset_id": self.dataset_id,
            "version_number": self.version_number,
            "version_tag": self.version_tag,
            "case_count": self.case_count,
            "path": str(self.path),
            "parent_dataset_id": self.parent_dataset_id,
            "source_comparison_id": self.source_comparison_id,
            "signal_verdict": self.signal_verdict,
            "severity": self.severity,
        }
        if self.created_at is not None:
            payload["created_at"] = self.created_at
        return payload


@dataclass(slots=True, frozen=True)
class DatasetEvolutionSummary:
    dataset: FailureDataset
    output_path: Path
    family_id: str
    version_number: int
    version_tag: str
    parent_dataset_id: str | None
    previous_case_count: int
    added_case_count: int
    selected_case_count: int
    duplicate_case_count: int
    comparison_id: str
    signal: dict[str, JsonValue]
    policy: RegressionPackPolicy
    preview_cases: tuple[RegressionPackPreviewCase, ...]

    @property
    def total_case_count(self) -> int:
        return len(self.dataset.cases)

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "dataset_id": self.dataset.dataset_id,
            "family_id": self.family_id,
            "version_number": self.version_number,
            "version_tag": self.version_tag,
            "parent_dataset_id": self.parent_dataset_id,
            "output_path": str(self.output_path),
            "previous_case_count": self.previous_case_count,
            "added_case_count": self.added_case_count,
            "selected_case_count": self.selected_case_count,
            "duplicate_case_count": self.duplicate_case_count,
            "total_case_count": self.total_case_count,
            "comparison_id": self.comparison_id,
            "policy": self.policy.to_payload(),
            "signal": dict(self.signal),
            "preview_cases": [entry.to_payload() for entry in self.preview_cases],
        }


def generate_regression_pack(
    *,
    comparison_id: str,
    root: str | Path | None = None,
    family_id: str | None = None,
    failure_type: str | None = None,
    top_n: int = _DEFAULT_SIGNAL_PACK_LIMIT,
    output_path: str | Path | None = None,
    now: datetime | None = None,
) -> RegressionPackDraftSummary:
    artifact_root = project_root(root).resolve()
    selection = preview_regression_pack(
        comparison_id=comparison_id,
        root=artifact_root,
        family_id=family_id,
        failure_type=failure_type,
        top_n=top_n,
    )
    created_at = _timestamp(now)
    cases = tuple(
        _build_generated_prompt_case(
            row=row,
            root=artifact_root,
            comparison_id=selection.comparison_id,
            created_at=created_at,
            draft_case_id=_stable_entry_id(
                "signal_pack",
                selection.comparison_id,
                str(row["case_id"]),
            ),
        )
        for row in selection.selected_rows
    )
    target_path = _resolve_draft_output_path(
        root=artifact_root,
        family_id=selection.suggested_family_id,
        output_path=output_path,
    )
    dataset_id = _normalize_dataset_id(f"{selection.suggested_family_id}-draft")
    dataset = FailureDataset(
        dataset_id=dataset_id,
        name=_titleize(dataset_id),
        description=(
            "Draft regression pack generated deterministically from a saved comparison signal."
        ),
        created_at=created_at,
        lifecycle="draft",
        source={
            "type": "artifact_harvest",
            "mode": "deltas",
            "origin": "regression_signal_pack",
            "artifact_root": str(artifact_root),
            "comparison_report_id": selection.comparison_id,
            "suggested_family_id": selection.suggested_family_id,
            "filters": {
                "report_id": selection.comparison_id,
                "delta": selection.policy.delta_kind,
                "failure_type": selection.policy.failure_type,
                "limit": selection.policy.top_n,
            },
            "signal": dict(selection.signal),
            "policy": selection.policy.to_payload(),
        },
        cases=cases,
        metadata={
            "harvest": {
                "mode": "deltas",
                "origin": "regression_signal_pack",
                "selected_case_count": len(cases),
            }
        },
    )
    write_json(target_path, dataset.to_payload())
    return RegressionPackDraftSummary(
        dataset=dataset,
        output_path=target_path,
        comparison_id=selection.comparison_id,
        suggested_family_id=selection.suggested_family_id,
        policy=selection.policy,
        signal=dict(selection.signal),
        preview_cases=selection.preview_cases,
    )


def evolve_dataset_family(
    family_id: str,
    *,
    comparison_id: str,
    root: str | Path | None = None,
    failure_type: str | None = None,
    top_n: int = _DEFAULT_SIGNAL_PACK_LIMIT,
    output_path: str | Path | None = None,
    now: datetime | None = None,
) -> DatasetEvolutionSummary:
    artifact_root = project_root(root).resolve()
    normalized_family_id = _normalize_family_id(family_id)
    selection = preview_regression_pack(
        comparison_id=comparison_id,
        root=artifact_root,
        family_id=normalized_family_id,
        failure_type=failure_type,
        top_n=top_n,
    )
    created_at = _timestamp(now)

    existing_versions = list_dataset_versions(normalized_family_id, root=artifact_root)
    parent_dataset = (
        load_dataset(existing_versions[-1].path) if existing_versions else None
    )
    parent_dataset_id = parent_dataset.dataset_id if parent_dataset is not None else None
    next_version_number = existing_versions[-1].version_number + 1 if existing_versions else 1
    version_tag = f"v{next_version_number}"
    dataset_id = _normalize_dataset_id(f"{normalized_family_id}-{version_tag}")
    target_path = (
        _resolve_curated_output_path(output_path, root=artifact_root)
        if output_path is not None
        else dataset_file(dataset_id, root=artifact_root, create=True).resolve()
    )

    combined_cases: list[PromptCase] = list(parent_dataset.cases if parent_dataset is not None else ())
    canonical_keys = {_canonical_case_key(case) for case in combined_cases}
    added_case_count = 0
    duplicate_case_count = 0
    for row in selection.selected_rows:
        source_case = _build_generated_prompt_case(
            row=row,
            root=artifact_root,
            comparison_id=comparison_id,
            created_at=created_at,
            draft_case_id=_stable_entry_id("signal_pack", comparison_id, str(row["case_id"])),
        )
        canonical_key = _canonical_case_key(source_case)
        if canonical_key in canonical_keys:
            duplicate_case_count += 1
            continue
        canonical_keys.add(canonical_key)
        metadata = dict(source_case.metadata)
        harvest_metadata = dict(_mapping_or_empty(metadata.get("harvest")))
        harvest_metadata["canonical_case_id"] = _canonical_case_id(canonical_key)
        harvest_metadata["duplicate_resolution"] = "new_from_signal"
        metadata["harvest"] = harvest_metadata
        metadata["evolution"] = {
            "family_id": normalized_family_id,
            "introduced_in_dataset_id": dataset_id,
            "introduced_in_version": version_tag,
            "source_comparison_id": comparison_id,
        }
        tags = list(source_case.tags)
        if "curated" not in tags:
            tags.append("curated")
        combined_cases.append(
            PromptCase(
                id=_canonical_case_id(canonical_key),
                prompt=source_case.prompt,
                tags=tuple(tags),
                expectations=source_case.expectations,
                metadata=metadata,
            )
        )
        added_case_count += 1

    if parent_dataset is not None and added_case_count == 0:
        raise ValueError(
            f"comparison {comparison_id} introduced no new unique regression cases for {normalized_family_id}"
        )

    description = (
        parent_dataset.description
        if parent_dataset is not None and parent_dataset.description
        else "Versioned regression pack evolved from deterministic saved comparison signals."
    )
    evolved_dataset = FailureDataset(
        dataset_id=dataset_id,
        name=_titleize(dataset_id),
        description=description,
        version=version_tag,
        created_at=created_at,
        lifecycle="curated",
        source=_compact_mapping(
            {
                "type": "dataset_evolution",
                "family_id": normalized_family_id,
                "comparison_report_id": comparison_id,
                "parent_dataset_id": parent_dataset_id,
                "signal": dict(selection.signal),
                "policy": selection.policy.to_payload(),
            }
        ),
        cases=tuple(sorted(combined_cases, key=lambda case: case.id)),
        metadata={
            "versioning": {
                "family_id": normalized_family_id,
                "version_number": next_version_number,
                "version_tag": version_tag,
                "parent_dataset_id": parent_dataset_id,
                "source_comparison_id": comparison_id,
            }
        },
    )
    write_json(target_path, evolved_dataset.to_payload())
    return DatasetEvolutionSummary(
        dataset=evolved_dataset,
        output_path=target_path,
        family_id=normalized_family_id,
        version_number=next_version_number,
        version_tag=version_tag,
        parent_dataset_id=parent_dataset_id,
        previous_case_count=len(parent_dataset.cases) if parent_dataset is not None else 0,
        added_case_count=added_case_count,
        selected_case_count=selection.selected_case_count,
        duplicate_case_count=duplicate_case_count,
        comparison_id=comparison_id,
        signal=dict(selection.signal),
        policy=selection.policy,
        preview_cases=selection.preview_cases,
    )


def preview_regression_pack(
    *,
    comparison_id: str,
    root: str | Path | None = None,
    family_id: str | None = None,
    failure_type: str | None = None,
    top_n: int = _DEFAULT_SIGNAL_PACK_LIMIT,
    allow_empty: bool = False,
) -> RegressionPackSelectionSummary:
    artifact_root = project_root(root).resolve()
    signal_row, delta_rows = _comparison_signal_source(
        comparison_id=comparison_id,
        root=artifact_root,
    )
    suggested_family_id = _normalize_family_id(
        family_id
        or suggest_dataset_family_id(
            dataset_id=_string_or_none(signal_row.get("dataset")),
            signal=signal_row,
            failure_type=failure_type,
        )
    )
    policy = RegressionPackPolicy(
        top_n=max(int(top_n), 1),
        failure_type=(
            failure_type.strip()
            if isinstance(failure_type, str) and failure_type.strip()
            else None
        ),
    )
    try:
        selected_rows, preview_cases = _select_regression_rows(
            comparison_id=comparison_id,
            signal_row=signal_row,
            delta_rows=delta_rows,
            policy=policy,
        )
    except ValueError:
        if not allow_empty:
            raise
        selected_rows = []
        preview_cases = ()
    return RegressionPackSelectionSummary(
        comparison_id=comparison_id,
        suggested_family_id=suggested_family_id,
        policy=policy,
        signal=_signal_payload(signal_row),
        preview_cases=preview_cases,
        selected_rows=tuple(selected_rows),
    )


def list_dataset_versions(
    family_id: str,
    *,
    root: str | Path | None = None,
) -> tuple[DatasetVersionRecord, ...]:
    artifact_root = project_root(root).resolve()
    normalized_family_id = _normalize_family_id(family_id)
    dataset_dir = datasets_root(root=artifact_root, create=False)
    if not dataset_dir.exists():
        return ()

    records: list[DatasetVersionRecord] = []
    for candidate in sorted(dataset_dir.glob("*.json")):
        dataset = load_dataset(candidate)
        version_metadata = _mapping_or_empty(dataset.metadata.get("versioning"))
        version_family_id = _string_or_none(version_metadata.get("family_id"))
        if version_family_id != normalized_family_id:
            continue
        version_number = _int_or_none(version_metadata.get("version_number"))
        version_tag = _string_or_none(version_metadata.get("version_tag"))
        if version_number is None or version_tag is None:
            match = _VERSION_SUFFIX_PATTERN.match(dataset.dataset_id)
            if match is None or _normalize_family_id(match.group("family")) != normalized_family_id:
                continue
            version_number = int(match.group("number"))
            version_tag = f"v{version_number}"
        source = _mapping_or_empty(dataset.source)
        signal = _mapping_or_empty(source.get("signal"))
        records.append(
            DatasetVersionRecord(
                family_id=normalized_family_id,
                dataset_id=dataset.dataset_id,
                version_number=version_number,
                version_tag=version_tag,
                created_at=dataset.created_at,
                case_count=len(dataset.cases),
                path=candidate.resolve(),
                parent_dataset_id=_string_or_none(version_metadata.get("parent_dataset_id")),
                source_comparison_id=_string_or_none(
                    version_metadata.get("source_comparison_id")
                    or source.get("comparison_report_id")
                ),
                signal_verdict=_string_or_none(signal.get("verdict")),
                severity=_float_or_none(signal.get("severity")),
            )
        )
    return tuple(sorted(records, key=lambda record: record.version_number))


def suggest_dataset_family_id(
    *,
    dataset_id: str | None,
    signal: dict[str, Any],
    failure_type: str | None = None,
) -> str:
    dataset_segment = _normalize_family_id(dataset_id or "comparison")
    if isinstance(failure_type, str) and failure_type.strip():
        driver_segment = _normalize_family_id(failure_type)
    else:
        raw_drivers = signal.get("top_drivers")
        driver_values = [
            _string_or_none(driver.get("failure_type"))
            for driver in raw_drivers
            if isinstance(driver, dict) and _string_or_none(driver.get("direction")) == "regression"
        ] if isinstance(raw_drivers, list) else []
        primary_driver = next((value for value in driver_values if value is not None), None)
        driver_segment = _normalize_family_id(primary_driver or "general")
    return _normalize_family_id(f"regression-{dataset_segment}-{driver_segment}")


def _comparison_signal_source(
    *,
    comparison_id: str,
    root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    # Import lazily to avoid cycling through datasets -> index.builder -> reporting -> runner.
    from model_failure_lab.index.query import (
        QueryFilters,
        query_case_deltas,
        query_comparison_signals,
    )

    signal_rows = query_comparison_signals(
        QueryFilters(report_id=comparison_id, limit=1),
        verdict=None,
        root=root,
    )
    if not signal_rows:
        raise ValueError(f"saved comparison signal not found: {comparison_id}")
    delta_rows = query_case_deltas(
        QueryFilters(report_id=comparison_id, limit=1000),
        root=root,
    )
    return signal_rows[0], delta_rows


def _select_regression_rows(
    *,
    comparison_id: str,
    signal_row: dict[str, Any],
    delta_rows: list[dict[str, Any]],
    policy: RegressionPackPolicy,
) -> tuple[list[dict[str, Any]], tuple[RegressionPackPreviewCase, ...]]:
    if _string_or_none(signal_row.get("signal_verdict")) == "incompatible":
        raise ValueError(f"comparison {comparison_id} is incompatible and cannot generate a regression pack")

    row_by_case_id = {str(row["case_id"]): row for row in delta_rows}
    selected_case_ids: list[str] = []
    driver_by_case_id: dict[str, tuple[int | None, str | None]] = {}
    raw_drivers = signal_row.get("top_drivers")
    if isinstance(raw_drivers, list):
        for index, raw_driver in enumerate(raw_drivers):
            if not isinstance(raw_driver, dict):
                continue
            direction = _string_or_none(raw_driver.get("direction"))
            failure_type = _string_or_none(raw_driver.get("failure_type"))
            if direction != "regression":
                continue
            if policy.failure_type is not None and failure_type != policy.failure_type:
                continue
            case_ids = raw_driver.get("case_ids")
            if not isinstance(case_ids, list):
                continue
            driver_rank = _int_or_none(raw_driver.get("driver_rank"))
            normalized_rank = driver_rank if driver_rank is not None else index
            for case_id in sorted(str(case_id) for case_id in case_ids if isinstance(case_id, str)):
                row = row_by_case_id.get(case_id)
                if row is None or str(row.get("delta_kind")) != "regression":
                    continue
                if case_id not in driver_by_case_id:
                    driver_by_case_id[case_id] = (normalized_rank, failure_type)
                    selected_case_ids.append(case_id)

    if not selected_case_ids:
        for row in sorted(delta_rows, key=lambda item: str(item["case_id"])):
            if str(row.get("delta_kind")) != "regression":
                continue
            candidate_failure_type = _string_or_none(row.get("candidate_failure_type"))
            if policy.failure_type is not None and candidate_failure_type != policy.failure_type:
                continue
            case_id = str(row["case_id"])
            driver_by_case_id.setdefault(case_id, (None, candidate_failure_type))
            selected_case_ids.append(case_id)

    selected_rows: list[dict[str, Any]] = []
    preview_cases: list[RegressionPackPreviewCase] = []
    for case_id in selected_case_ids:
        if len(selected_rows) >= policy.top_n:
            break
        row = row_by_case_id[case_id]
        driver_rank, driver_failure_type = driver_by_case_id.get(case_id, (None, None))
        augmented_row = dict(row)
        augmented_row["signal_driver_rank"] = driver_rank
        augmented_row["signal_driver_failure_type"] = driver_failure_type
        selected_rows.append(augmented_row)
        preview_cases.append(
            RegressionPackPreviewCase(
                case_id=_stable_entry_id("signal_pack", comparison_id, case_id),
                prompt_id=str(row["prompt_id"]),
                prompt=str(row["prompt"]),
                source_case_id=case_id,
                source_report_id=str(row["report_id"]),
                source_run_id=str(row["candidate_run_id"]),
                driver_failure_type=driver_failure_type,
                driver_rank=driver_rank,
                transition_type=str(row["transition_type"]),
            )
        )

    if not selected_rows:
        raise ValueError(
            f"comparison {comparison_id} does not expose any regression cases for the current policy"
        )
    return selected_rows, tuple(preview_cases)


def _build_generated_prompt_case(
    *,
    row: dict[str, Any],
    root: Path,
    comparison_id: str,
    created_at: str,
    draft_case_id: str,
) -> PromptCase:
    from model_failure_lab.reporting.load import load_saved_run_artifacts

    baseline_run_id = str(row["baseline_run_id"])
    candidate_run_id = str(row["candidate_run_id"])
    case_id = str(row["case_id"])
    candidate_run = load_saved_run_artifacts(candidate_run_id, root=root)
    baseline_run = load_saved_run_artifacts(baseline_run_id, root=root)
    source_case = candidate_run.case_map().get(case_id) or baseline_run.case_map().get(case_id)
    if source_case is None:
        raise ValueError(
            f"comparison {comparison_id} references missing case {case_id} in saved runs"
        )

    tags = list(source_case.prompt.tags)
    for tag in (
        "harvested",
        "regression-pack",
        _stable_tag("driver", _string_or_none(row.get("signal_driver_failure_type"))),
    ):
        if tag and tag not in tags:
            tags.append(tag)

    metadata: dict[str, JsonValue] = {}
    harvest_metadata = dict(_mapping_or_empty(metadata.get("harvest")))
    harvest_metadata.update(
        {
            "source_kind": "comparison_signal",
            "source_report_id": str(row["report_id"]),
            "source_case_id": case_id,
            "source_prompt_id": str(row["prompt_id"]),
            "source_dataset_id": candidate_run.run.dataset,
            "baseline_run_id": baseline_run_id,
            "candidate_run_id": candidate_run_id,
            "baseline_model": baseline_run.run.model,
            "candidate_model": candidate_run.run.model,
            "delta_kind": _string_or_none(row.get("delta_kind")),
            "transition_type": _string_or_none(row.get("transition_type")),
            "transition_label": _string_or_none(row.get("transition_label")),
            "signal_driver_failure_type": _string_or_none(row.get("signal_driver_failure_type")),
            "signal_driver_rank": _int_or_none(row.get("signal_driver_rank")),
            "comparison_id": comparison_id,
            "created_at": created_at,
            "draft_case_id": draft_case_id,
            "normalized_prompt_hash": _prompt_hash(source_case.prompt.prompt, normalize=True),
            "exact_prompt_hash": _prompt_hash(source_case.prompt.prompt, normalize=False),
        }
    )
    metadata["harvest"] = harvest_metadata
    return PromptCase(
        id=draft_case_id,
        prompt=source_case.prompt.prompt,
        tags=tuple(tags),
        expectations=source_case.prompt.expectations,
        metadata=metadata,
    )


def _resolve_draft_output_path(
    *,
    root: Path,
    family_id: str,
    output_path: str | Path | None,
) -> Path:
    if output_path is not None:
        return _resolve_curated_output_path(output_path, root=root)
    harvested_dir = datasets_root(root=root, create=True) / "harvested"
    harvested_dir.mkdir(parents=True, exist_ok=True)
    candidate = harvested_dir / f"{family_id}-draft.json"
    suffix = 2
    while candidate.exists():
        candidate = harvested_dir / f"{family_id}-draft-{suffix}.json"
        suffix += 1
    return candidate.resolve()


def _resolve_curated_output_path(output_path: str | Path, *, root: Path) -> Path:
    target = Path(output_path)
    if not target.is_absolute():
        target = root / target
    if target.suffix.lower() != ".json":
        raise ValueError("dataset output path must be a .json file")
    return target.resolve()


def _signal_payload(signal_row: dict[str, Any]) -> dict[str, JsonValue]:
    return {
        "verdict": _string_or_none(signal_row.get("signal_verdict")) or "unknown",
        "regression_score": _float_or_none(signal_row.get("regression_score")) or 0.0,
        "improvement_score": _float_or_none(signal_row.get("improvement_score")) or 0.0,
        "net_score": _float_or_none(signal_row.get("net_score")) or 0.0,
        "severity": _float_or_none(signal_row.get("severity")) or 0.0,
        "top_drivers": [
            {
                "driver_rank": _int_or_none(driver.get("driver_rank")),
                "failure_type": _string_or_none(driver.get("failure_type")),
                "delta": _float_or_none(driver.get("delta")),
                "direction": _string_or_none(driver.get("direction")),
                "case_ids": list(driver.get("case_ids", []))
                if isinstance(driver.get("case_ids"), list)
                else [],
            }
            for driver in signal_row.get("top_drivers", [])
            if isinstance(driver, dict)
        ],
    }


def _stable_entry_id(kind: str, left: str, right: str) -> str:
    digest = hashlib.sha1(f"{kind}:{left}:{right}".encode("utf-8")).hexdigest()[:16]
    return f"harvest-{digest}"


def _canonical_case_key(case: PromptCase) -> str:
    expectations_payload = case.expectations.to_payload() if case.expectations is not None else None
    serialized = json.dumps(expectations_payload, sort_keys=True)
    normalized_prompt = " ".join(case.prompt.lower().split())
    return hashlib.sha1(f"{normalized_prompt}\n{serialized}".encode("utf-8")).hexdigest()


def _canonical_case_id(canonical_key: str) -> str:
    return f"case-{canonical_key[:16]}"


def _prompt_hash(prompt: str, *, normalize: bool) -> str:
    value = " ".join(prompt.lower().split()) if normalize else prompt
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def _normalize_dataset_id(value: str) -> str:
    normalized = _SEGMENT_PATTERN.sub("-", value.strip().lower()).strip("-")
    if not normalized:
        raise ValueError("dataset_id must contain at least one alphanumeric character")
    return normalized


def _normalize_family_id(value: str) -> str:
    normalized = _normalize_dataset_id(value)
    match = _VERSION_SUFFIX_PATTERN.match(normalized)
    if match is not None:
        return _normalize_dataset_id(match.group("family"))
    return normalized


def _titleize(value: str) -> str:
    return value.replace("-", " ").replace("_", " ").title()


def _stable_tag(prefix: str, value: str | None) -> str | None:
    if value is None:
        return None
    return _normalize_dataset_id(f"{prefix}-{value}")


def _timestamp(now: datetime | None) -> str:
    current_time = now or datetime.now(timezone.utc)
    return current_time.isoformat().replace("+00:00", "Z")


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _float_or_none(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _int_or_none(value: object) -> int | None:
    return value if type(value) is int else None


def _mapping_or_empty(value: object) -> dict[str, JsonValue]:
    return dict(value) if isinstance(value, dict) else {}


def _compact_mapping(value: dict[str, JsonValue | None]) -> dict[str, JsonValue]:
    return {key: entry for key, entry in value.items() if entry is not None}
