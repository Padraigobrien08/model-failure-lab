"""Shared baseline registry and PR reliability markdown output."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from model_failure_lab.index import QueryFilters, query_comparison_signals
from model_failure_lab.schemas import JsonValue
from model_failure_lab.storage import read_json, write_json
from model_failure_lab.storage.layout import project_root

BASELINE_REGISTRY_PATH = ".failure_lab/baseline_registry.json"


@dataclass(slots=True, frozen=True)
class BaselineEntry:
    name: str
    run_id: str
    model: str | None
    dataset: str | None
    owner: str | None
    notes: str | None
    updated_at: str

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "name": self.name,
            "run_id": self.run_id,
            "model": self.model,
            "dataset": self.dataset,
            "owner": self.owner,
            "notes": self.notes,
            "updated_at": self.updated_at,
        }


def list_baselines(*, root: str | Path | None = None) -> tuple[BaselineEntry, ...]:
    payload = _load_registry(root=root)
    rows = payload.get("baselines", [])
    if not isinstance(rows, list):
        return ()
    entries: list[BaselineEntry] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = _optional_string(row.get("name"))
        run_id = _optional_string(row.get("run_id"))
        if name is None or run_id is None:
            continue
        entries.append(
            BaselineEntry(
                name=name,
                run_id=run_id,
                model=_optional_string(row.get("model")),
                dataset=_optional_string(row.get("dataset")),
                owner=_optional_string(row.get("owner")),
                notes=_optional_string(row.get("notes")),
                updated_at=_optional_string(row.get("updated_at")) or "",
            )
        )
    return tuple(sorted(entries, key=lambda entry: entry.name))


def upsert_baseline(
    name: str,
    *,
    run_id: str,
    model: str | None = None,
    dataset: str | None = None,
    owner: str | None = None,
    notes: str | None = None,
    root: str | Path | None = None,
) -> BaselineEntry:
    artifact_root = project_root(root).resolve()
    existing = {entry.name: entry for entry in list_baselines(root=artifact_root)}
    updated = BaselineEntry(
        name=name,
        run_id=run_id,
        model=model,
        dataset=dataset,
        owner=owner,
        notes=notes,
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
    existing[name] = updated
    _write_registry(
        root=artifact_root,
        entries=tuple(sorted(existing.values(), key=lambda entry: entry.name)),
    )
    return updated


def build_pr_reliability_comment(
    *,
    baseline_run_id: str,
    candidate_run_id: str,
    root: str | Path | None = None,
) -> str:
    rows = query_comparison_signals(
        QueryFilters(
            baseline_run_id=baseline_run_id,
            candidate_run_id=candidate_run_id,
            limit=1,
        ),
        verdict=None,
        root=project_root(root),
    )
    if not rows:
        return (
            "## Reliability Diff\n\n"
            f"- Baseline run: `{baseline_run_id}`\n"
            f"- Candidate run: `{candidate_run_id}`\n"
            "- No saved comparison signal found for this run pair.\n"
        )
    row = rows[0]
    drivers = row.get("top_drivers")
    bullet_lines: list[str] = []
    if isinstance(drivers, list):
        for driver in drivers[:3]:
            if not isinstance(driver, dict):
                continue
            failure_type = _optional_string(driver.get("failure_type")) or "unknown"
            direction = _optional_string(driver.get("direction")) or "neutral"
            delta = driver.get("delta")
            delta_value = float(delta) if isinstance(delta, (int, float)) else 0.0
            bullet_lines.append(f"- `{failure_type}` {direction} ({delta_value:+.3f})")
    if not bullet_lines:
        bullet_lines.append("- No top drivers available.")
    return (
        "## Reliability Diff\n\n"
        f"- Baseline run: `{baseline_run_id}`\n"
        f"- Candidate run: `{candidate_run_id}`\n"
        f"- Verdict: `{row.get('signal_verdict', 'unknown')}`\n"
        f"- Severity: `{float(row.get('severity', 0.0) or 0.0):.3f}`\n"
        "\n### Top Drivers\n"
        + "\n".join(bullet_lines)
        + "\n"
    )


def _registry_path(*, root: str | Path | None) -> Path:
    return project_root(root) / BASELINE_REGISTRY_PATH


def _load_registry(*, root: str | Path | None) -> dict[str, object]:
    path = _registry_path(root=root)
    if not path.exists():
        return {"baselines": []}
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError("baseline registry must be a JSON object")
    return payload


def _write_registry(*, root: str | Path | None, entries: tuple[BaselineEntry, ...]) -> None:
    path = _registry_path(root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, {"baselines": [entry.to_payload() for entry in entries]})


def _optional_string(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None
