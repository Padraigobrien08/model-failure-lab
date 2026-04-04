"""Turn saved query-selected artifact cases into reusable draft dataset packs."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from model_failure_lab.datasets import FailureDataset
from model_failure_lab.index import QueryFilters, query_case_deltas, query_cases
from model_failure_lab.reporting.load import load_saved_run_artifacts
from model_failure_lab.runner import CaseExecution
from model_failure_lab.schemas import JsonValue, PromptCase
from model_failure_lab.storage import write_json
from model_failure_lab.storage.layout import project_root

_SEGMENT_PATTERN = re.compile(r"[^a-z0-9]+")

HarvestMode = Literal["cases", "deltas"]


@dataclass(slots=True, frozen=True)
class HarvestDraftSummary:
    dataset: FailureDataset
    output_path: Path
    mode: HarvestMode
    selected_case_count: int


def infer_harvest_mode(
    filters: QueryFilters,
    *,
    comparison_id: str | None = None,
) -> HarvestMode:
    if (
        comparison_id is not None
        or filters.report_id is not None
        or filters.baseline_run_id is not None
        or filters.candidate_run_id is not None
        or filters.delta is not None
    ):
        return "deltas"
    return "cases"


def harvest_artifact_cases(
    *,
    filters: QueryFilters,
    output_path: str | Path,
    root: str | Path | None = None,
    dataset_id: str | None = None,
    comparison_id: str | None = None,
    mode: HarvestMode | None = None,
    now: datetime | None = None,
) -> HarvestDraftSummary:
    artifact_root = project_root(root).resolve()
    normalized_filters = _with_comparison_filter(filters, comparison_id=comparison_id)
    resolved_mode = mode or infer_harvest_mode(
        normalized_filters,
        comparison_id=comparison_id,
    )
    created_at = _timestamp(now)
    rows = (
        query_case_deltas(normalized_filters, root=artifact_root)
        if resolved_mode == "deltas"
        else query_cases(normalized_filters, root=artifact_root)
    )
    if not rows:
        raise ValueError("no saved artifact cases matched the current harvest filters")

    hydrated_cases = (
        _harvest_delta_cases(rows, artifact_root=artifact_root, created_at=created_at)
        if resolved_mode == "deltas"
        else _harvest_query_cases(rows, artifact_root=artifact_root, created_at=created_at)
    )
    target_path = _resolve_output_path(output_path, root=artifact_root)
    resolved_dataset_id = _normalize_dataset_id(dataset_id or target_path.stem)
    dataset = FailureDataset(
        dataset_id=resolved_dataset_id,
        name=_titleize_dataset_id(resolved_dataset_id),
        description=(
            "Draft harvested dataset pack derived from saved artifact evidence under the local "
            "failure-lab workspace."
        ),
        created_at=created_at,
        lifecycle="draft",
        source={
            "type": "artifact_harvest",
            "mode": resolved_mode,
            "artifact_root": str(artifact_root),
            "filters": _query_filters_payload(normalized_filters),
        },
        cases=tuple(hydrated_cases),
        metadata={
            "harvest": {
                "selected_case_count": len(hydrated_cases),
                "mode": resolved_mode,
            }
        },
    )
    write_json(target_path, dataset.to_payload())
    return HarvestDraftSummary(
        dataset=dataset,
        output_path=target_path,
        mode=resolved_mode,
        selected_case_count=len(hydrated_cases),
    )


def _harvest_query_cases(
    rows: list[dict[str, object]],
    *,
    artifact_root: Path,
    created_at: str,
) -> list[PromptCase]:
    saved_run_cache: dict[str, object] = {}
    harvested_cases: list[PromptCase] = []
    for row in rows:
        run_id = _require_string(row.get("run_id"), "run_id")
        case_id = _require_string(row.get("case_id"), "case_id")
        prompt_id = _require_string(row.get("prompt_id"), "prompt_id")
        saved_run = saved_run_cache.get(run_id)
        if saved_run is None:
            saved_run = load_saved_run_artifacts(run_id, root=artifact_root)
            saved_run_cache[run_id] = saved_run
        case_result = saved_run.case_map().get(case_id)
        if case_result is None:
            raise ValueError(f"saved run {run_id} does not contain case {case_id}")
        harvested_cases.append(
            _build_prompt_case(
                source_case=case_result,
                draft_case_id=_stable_entry_id("run_case", run_id, case_id),
                created_at=created_at,
                extra_tags=(
                    "harvested",
                    _stable_tag("failure", _optional_string(row.get("failure_type"))),
                ),
                metadata={
                    "harvest": {
                        "source_kind": "run_case",
                        "source_run_id": run_id,
                        "source_dataset_id": saved_run.run.dataset,
                        "source_case_id": case_id,
                        "source_prompt_id": prompt_id,
                        "source_model": saved_run.run.model,
                        "failure_type": _optional_string(row.get("failure_type")),
                        "expectation_verdict": _optional_string(row.get("expectation_verdict")),
                        "harvested_at": created_at,
                    }
                },
            )
        )
    return harvested_cases


def _harvest_delta_cases(
    rows: list[dict[str, object]],
    *,
    artifact_root: Path,
    created_at: str,
) -> list[PromptCase]:
    saved_run_cache: dict[str, object] = {}
    harvested_cases: list[PromptCase] = []
    for row in rows:
        report_id = _require_string(row.get("report_id"), "report_id")
        case_id = _require_string(row.get("case_id"), "case_id")
        prompt_id = _require_string(row.get("prompt_id"), "prompt_id")
        baseline_run_id = _require_string(row.get("baseline_run_id"), "baseline_run_id")
        candidate_run_id = _require_string(row.get("candidate_run_id"), "candidate_run_id")
        baseline_saved = saved_run_cache.get(baseline_run_id)
        if baseline_saved is None:
            baseline_saved = load_saved_run_artifacts(baseline_run_id, root=artifact_root)
            saved_run_cache[baseline_run_id] = baseline_saved
        candidate_saved = saved_run_cache.get(candidate_run_id)
        if candidate_saved is None:
            candidate_saved = load_saved_run_artifacts(candidate_run_id, root=artifact_root)
            saved_run_cache[candidate_run_id] = candidate_saved

        baseline_case = baseline_saved.case_map().get(case_id)
        candidate_case = candidate_saved.case_map().get(case_id)
        source_case = baseline_case or candidate_case
        if source_case is None:
            raise ValueError(
                f"comparison source cases are unavailable for {report_id}:{case_id}"
            )

        prompt_mismatch = (
            baseline_case is not None
            and candidate_case is not None
            and baseline_case.prompt.to_payload() != candidate_case.prompt.to_payload()
        )
        harvested_cases.append(
            _build_prompt_case(
                source_case=source_case,
                draft_case_id=_stable_entry_id("comparison_case", report_id, case_id),
                created_at=created_at,
                extra_tags=(
                    "harvested",
                    _stable_tag("delta", _optional_string(row.get("delta_kind"))),
                    _stable_tag("transition", _optional_string(row.get("transition_type"))),
                ),
                metadata={
                    "harvest": {
                        "source_kind": "comparison_delta",
                        "source_report_id": report_id,
                        "source_dataset_id": baseline_saved.run.dataset,
                        "source_case_id": case_id,
                        "source_prompt_id": prompt_id,
                        "baseline_run_id": baseline_run_id,
                        "candidate_run_id": candidate_run_id,
                        "baseline_model": baseline_saved.run.model,
                        "candidate_model": candidate_saved.run.model,
                        "delta_kind": _optional_string(row.get("delta_kind")),
                        "transition_type": _optional_string(row.get("transition_type")),
                        "transition_label": _optional_string(row.get("transition_label")),
                        "baseline_failure_type": _optional_string(row.get("baseline_failure_type")),
                        "candidate_failure_type": _optional_string(row.get("candidate_failure_type")),
                        "baseline_expectation_verdict": _optional_string(
                            row.get("baseline_expectation_verdict")
                        ),
                        "candidate_expectation_verdict": _optional_string(
                            row.get("candidate_expectation_verdict")
                        ),
                        "prompt_mismatch": prompt_mismatch,
                        "harvested_at": created_at,
                    }
                },
            )
        )
    return harvested_cases


def _build_prompt_case(
    *,
    source_case: CaseExecution,
    draft_case_id: str,
    created_at: str,
    extra_tags: tuple[str | None, ...],
    metadata: dict[str, JsonValue],
) -> PromptCase:
    prompt = source_case.prompt
    combined_tags = list(prompt.tags)
    for tag in extra_tags:
        if tag and tag not in combined_tags:
            combined_tags.append(tag)
    harvest_metadata = dict(metadata.get("harvest", {}))
    harvest_metadata["normalized_prompt_hash"] = _prompt_hash(prompt.prompt, normalize=True)
    harvest_metadata["exact_prompt_hash"] = _prompt_hash(prompt.prompt, normalize=False)
    harvest_metadata["draft_case_id"] = draft_case_id
    harvest_metadata["created_at"] = created_at
    metadata["harvest"] = harvest_metadata
    return PromptCase(
        id=draft_case_id,
        prompt=prompt.prompt,
        tags=tuple(combined_tags),
        expectations=prompt.expectations,
        metadata=metadata,
    )


def _resolve_output_path(output_path: str | Path, *, root: Path) -> Path:
    target = Path(output_path)
    if not target.is_absolute():
        target = root / target
    if target.suffix.lower() != ".json":
        raise ValueError("harvest output path must be a .json file")
    return target.resolve()


def _with_comparison_filter(
    filters: QueryFilters,
    *,
    comparison_id: str | None,
) -> QueryFilters:
    if comparison_id is None:
        return filters
    return QueryFilters(
        failure_type=filters.failure_type,
        model=filters.model,
        dataset=filters.dataset,
        run_id=filters.run_id,
        prompt_id=filters.prompt_id,
        report_id=comparison_id,
        baseline_run_id=filters.baseline_run_id,
        candidate_run_id=filters.candidate_run_id,
        delta=filters.delta,
        last_n=filters.last_n,
        since=filters.since,
        until=filters.until,
        limit=filters.limit,
    )


def _query_filters_payload(filters: QueryFilters) -> dict[str, JsonValue]:
    return {
        "failure_type": filters.failure_type,
        "model": filters.model,
        "dataset": filters.dataset,
        "run_id": filters.run_id,
        "prompt_id": filters.prompt_id,
        "report_id": filters.report_id,
        "baseline_run_id": filters.baseline_run_id,
        "candidate_run_id": filters.candidate_run_id,
        "delta": filters.delta,
        "last_n": filters.last_n,
        "since": filters.since,
        "until": filters.until,
        "limit": filters.limit,
    }


def _stable_entry_id(kind: str, left: str, right: str) -> str:
    digest = hashlib.sha1(f"{kind}:{left}:{right}".encode("utf-8")).hexdigest()[:16]
    return f"harvest-{digest}"


def _prompt_hash(prompt: str, *, normalize: bool) -> str:
    value = " ".join(prompt.lower().split()) if normalize else prompt
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


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


def _require_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _stable_tag(prefix: str, value: str | None) -> str | None:
    if value is None:
        return None
    normalized = _SEGMENT_PATTERN.sub("-", value.strip().lower()).strip("-")
    if not normalized:
        return None
    return f"{prefix}-{normalized}"
