"""Policy-as-code regression gates with waiver support."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

from model_failure_lab.index import QueryFilters
from model_failure_lab.schemas import JsonValue
from model_failure_lab.storage.layout import (
    project_root,
    report_details_file,
    report_file,
)

from .lifecycle import get_active_lifecycle_action
from .policy import GovernancePolicy
from .workflow import review_dataset_actions

# Conventional in-workspace locations the gate falls back to when no explicit
# --waivers / --policy-file is supplied. Both the CLI gate and the operator
# console's read-only `gate` endpoint resolve through the same helpers, so the
# console can never show a gate state that silently ignores a team's committed
# waivers or policy. Explicit arguments always win over these defaults.
DEFAULT_WAIVER_FILENAMES: tuple[str, ...] = (
    "governance/waivers.yml",
    "governance/waivers.yaml",
    "governance/waivers.json",
)
DEFAULT_POLICY_FILENAMES: tuple[str, ...] = (
    "governance/policy.yml",
    "governance/policy.yaml",
    "governance/policy.json",
)


def _first_existing(root: str | Path | None, filenames: tuple[str, ...]) -> Path | None:
    base = project_root(root)
    for name in filenames:
        candidate = base / name
        if candidate.is_file():
            return candidate
    return None


def default_waiver_path(root: str | Path | None = None) -> Path | None:
    """Conventional committed waiver file for this workspace, if present."""

    return _first_existing(root, DEFAULT_WAIVER_FILENAMES)


def default_policy_path(root: str | Path | None = None) -> Path | None:
    """Conventional committed policy file for this workspace, if present."""

    return _first_existing(root, DEFAULT_POLICY_FILENAMES)


# --------------------------------------------------------------------------------------
# The gate contract. ONE implementation, called by every surface.
# --------------------------------------------------------------------------------------
#
# `compare --gate`, `regressions gate` and the operator console's `gate` endpoint must
# reach the same PASS/FAIL on the same artifacts, or the console can show green while CI
# shows red. They previously did not: `compare --gate` applied five checks while the
# governance gate applied only the verdict, so a candidate that deleted the cases it
# broke -- or two runs that were not comparable at all -- failed CI and passed the
# console. `evaluate_gate_conditions` is now the only place that decision is made.
#
# Checks are ordered most-fundamental first, and the first hit wins so the reported
# reason is stable and deterministic.


@dataclass(slots=True, frozen=True)
class GateConditions:
    """The comparison facts the gate contract decides on.

    Deliberately a plain value object rather than a report handle: `compare --gate` builds
    it from the report it just produced in memory, and the governance gate builds it by
    re-reading the saved artifacts. Both then run identical logic.
    """

    verdict: str
    compatible: bool
    execution_success_delta: float | None = None
    classification_coverage_delta: float | None = None
    dropped_baseline_failure_case_ids: tuple[str, ...] = ()


def evaluate_gate_conditions(conditions: GateConditions) -> str | None:
    """Return a human-readable block reason, or None when the gate should pass."""

    if not conditions.compatible:
        return "runs are not comparable"
    if conditions.verdict == "regression":
        return f"signal verdict: {conditions.verdict}"
    # Defense in depth: the signal verdict already folds in the execution-success delta,
    # but the gate is the last line before CI turns green, so it fails closed on any drop
    # in the candidate's ability to run or classify -- a candidate cannot pass simply by
    # erroring on (or failing to classify) cases the baseline handled.
    for label, value in (
        ("execution success", conditions.execution_success_delta),
        ("classification coverage", conditions.classification_coverage_delta),
    ):
        if value is not None and value < 0:
            return f"{label} regressed by {_format_signed_rate(value)}"
    # Removing failing cases from the candidate hides them from the shared-scope verdict
    # math, so a candidate could otherwise pass simply by deleting the cases it broke.
    dropped = conditions.dropped_baseline_failure_case_ids
    if dropped:
        preview = ", ".join(dropped[:3])
        return f"candidate dropped {len(dropped)} baseline failing case(s): {preview}"
    return None


def load_gate_conditions(comparison_id: str, *, root: str | Path | None = None) -> GateConditions:
    """Rebuild one comparison's gate conditions from its saved artifacts.

    The derived query index carries the verdict and `compatible` but not the delta metrics
    or the dropped-failing-case ids, so the governance gate reads the comparison's own
    report artifacts. Missing or malformed artifacts fail closed as incompatible rather
    than silently passing the gate.
    """

    report = _read_json_object(report_file(comparison_id, root=root))
    details = _read_json_object(report_details_file(comparison_id, root=root))
    if report is None:
        return GateConditions(verdict="unknown", compatible=False)

    comparison = report.get("comparison")
    comparison = comparison if isinstance(comparison, dict) else {}
    signal = comparison.get("signal")
    if not isinstance(signal, dict) and details is not None:
        candidate_signal = details.get("signal")
        signal = candidate_signal if isinstance(candidate_signal, dict) else {}
    signal = signal if isinstance(signal, dict) else {}

    metrics = report.get("metrics")
    delta = metrics.get("delta") if isinstance(metrics, dict) else None
    delta = delta if isinstance(delta, dict) else {}

    dropped = details.get("dropped_baseline_failure_case_ids") if details is not None else None
    dropped_ids = (
        tuple(sorted(value for value in dropped if isinstance(value, str)))
        if isinstance(dropped, list)
        else ()
    )

    return GateConditions(
        verdict=str(signal.get("verdict", "unknown")),
        compatible=comparison.get("compatible") is not False,
        execution_success_delta=_float_or_none(delta.get("execution_success_rate")),
        classification_coverage_delta=_float_or_none(delta.get("classification_coverage")),
        dropped_baseline_failure_case_ids=dropped_ids,
    )


def _read_json_object(path: Path) -> dict[str, JsonValue] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _float_or_none(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _format_signed_rate(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value * 100:.1f}%"


@dataclass(slots=True, frozen=True)
class GateWaiver:
    comparison_id: str
    reason: str
    owner: str | None
    expires_at: str | None
    active: bool

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "comparison_id": self.comparison_id,
            "reason": self.reason,
            "owner": self.owner,
            "expires_at": self.expires_at,
            "active": self.active,
        }


@dataclass(slots=True, frozen=True)
class GateDecision:
    comparison_id: str
    verdict: str
    action: str
    severity: float
    policy_rule: str
    blocked: bool
    waived: bool
    waiver: GateWaiver | None
    # Why the gate contract would block this comparison, independent of any waiver, or
    # None when it passes cleanly. Surfaces the non-verdict block reasons (incompatible
    # runs, coverage drops, dropped failing cases) that `compare --gate` already printed,
    # so the console and `regressions gate` can say the same thing CI says.
    block_reason: str | None = None

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "comparison_id": self.comparison_id,
            "verdict": self.verdict,
            "action": self.action,
            "severity": round(self.severity, 6),
            "policy_rule": self.policy_rule,
            "blocked": self.blocked,
            "waived": self.waived,
            "waiver": self.waiver.to_payload() if self.waiver is not None else None,
            "block_reason": self.block_reason,
        }


@dataclass(slots=True, frozen=True)
class RegressionGateResult:
    blocked: bool
    policy: GovernancePolicy
    filters: QueryFilters
    rows: tuple[GateDecision, ...]
    policy_source: str
    waiver_source: str | None

    def to_payload(self) -> dict[str, JsonValue]:
        return {
            "blocked": self.blocked,
            "policy": self.policy.to_payload(),
            "policy_source": self.policy_source,
            "waiver_source": self.waiver_source,
            "filters": {
                "failure_type": self.filters.failure_type,
                "model": self.filters.model,
                "dataset": self.filters.dataset,
                "report_id": self.filters.report_id,
                "baseline_run_id": self.filters.baseline_run_id,
                "candidate_run_id": self.filters.candidate_run_id,
                "last_n": self.filters.last_n,
                "since": self.filters.since,
                "until": self.filters.until,
                "limit": self.filters.limit,
            },
            "rows": [row.to_payload() for row in self.rows],
        }


def load_governance_policy_from_file(path: str | Path) -> GovernancePolicy:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("policy file must be a mapping")
    allowed_keys = {
        "minimum_severity",
        "top_n",
        "failure_type",
        "family_id",
        "family_case_cap",
        "max_duplicate_ratio",
        "recurrence_window",
        "recurrence_threshold",
        "strategy",
    }
    invalid = sorted(set(payload) - allowed_keys)
    if invalid:
        raise ValueError(f"unsupported policy keys: {', '.join(invalid)}")
    return GovernancePolicy(**payload)


def evaluate_regression_gate(
    *,
    root: str | Path | None = None,
    filters: QueryFilters | None = None,
    policy: GovernancePolicy | None = None,
    waiver_path: str | Path | None = None,
) -> RegressionGateResult:
    active_filters = filters or QueryFilters(limit=20)

    # Resolve policy: an explicit policy object wins; otherwise fall back to a
    # conventional committed policy file, and only then to built-in defaults.
    if policy is not None:
        active_policy = policy
        policy_source = "argument"
    else:
        discovered_policy = default_policy_path(root)
        if discovered_policy is not None:
            active_policy = load_governance_policy_from_file(discovered_policy)
            policy_source = _relative_source(discovered_policy, root)
        else:
            active_policy = GovernancePolicy()
            policy_source = "default"

    # Resolve waivers the same way: an explicit --waivers path wins; otherwise
    # fall back to a conventional committed waiver file if one exists.
    resolved_waiver_path = waiver_path
    waiver_source: str | None = None
    if resolved_waiver_path is None:
        resolved_waiver_path = default_waiver_path(root)
    if resolved_waiver_path is not None:
        waiver_source = _relative_source(resolved_waiver_path, root)
    waivers = _load_waivers(root=root, waiver_path=resolved_waiver_path)
    recommendations = review_dataset_actions(
        filters=active_filters,
        root=project_root(root),
        policy=active_policy,
        include_ignored=True,
    )
    rows: list[GateDecision] = []
    for recommendation in recommendations:
        severity = float(recommendation.signal.get("severity", 0.0) or 0.0)
        signal_verdict = str(recommendation.signal.get("verdict", "unknown"))
        # CI blocking is a gate-contract decision, not a dataset-governance decision. The
        # severity floor governs only whether to create/evolve a dataset family
        # (recommendation.action), never whether CI turns green. The contract itself lives
        # in `evaluate_gate_conditions`, which `compare --gate` also calls, so all three
        # surfaces block on exactly the same conditions.
        conditions = load_gate_conditions(recommendation.comparison_id, root=root)
        if conditions.verdict == "unknown":
            # The index knows the verdict even when the report artifact is unreadable;
            # prefer it so a stale-artifact read cannot downgrade a real regression.
            conditions = GateConditions(
                verdict=signal_verdict,
                compatible=conditions.compatible,
                execution_success_delta=conditions.execution_success_delta,
                classification_coverage_delta=conditions.classification_coverage_delta,
                dropped_baseline_failure_case_ids=(
                    conditions.dropped_baseline_failure_case_ids
                ),
            )
        block_reason = evaluate_gate_conditions(conditions)
        should_block = block_reason is not None
        waiver = waivers.get(recommendation.comparison_id)
        if waiver is None:
            # A retired dataset family is being wound down, so its regressions should
            # stop blocking CI. Surface it through the existing waiver channel with a
            # clear reason rather than silently un-blocking.
            family_id = recommendation.matched_family.family_id
            active_lifecycle = get_active_lifecycle_action(family_id, root=root)
            if active_lifecycle is not None and active_lifecycle.action == "retire":
                waiver = GateWaiver(
                    comparison_id=recommendation.comparison_id,
                    reason=f"family retired via lifecycle action ({family_id})",
                    owner=None,
                    expires_at=None,
                    active=True,
                )
        waived = waiver is not None and waiver.active
        rows.append(
            GateDecision(
                comparison_id=recommendation.comparison_id,
                verdict=signal_verdict,
                action=recommendation.action,
                severity=severity,
                policy_rule=recommendation.policy_rule,
                blocked=bool(should_block and not waived),
                waived=waived,
                waiver=waiver,
                block_reason=block_reason,
            )
        )
    return RegressionGateResult(
        blocked=any(row.blocked for row in rows),
        policy=active_policy,
        filters=active_filters,
        rows=tuple(rows),
        policy_source=policy_source,
        waiver_source=waiver_source,
    )


def _relative_source(path: str | Path, root: str | Path | None) -> str:
    resolved = Path(path)
    try:
        return resolved.resolve().relative_to(project_root(root).resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _load_waivers(
    *,
    root: str | Path | None,
    waiver_path: str | Path | None,
) -> dict[str, GateWaiver]:
    if waiver_path is None:
        return {}
    # Accept YAML or JSON (YAML is a JSON superset) so the waiver file matches the
    # policy file's format and the console's `--waivers waivers.yml` remedy works.
    payload = yaml.safe_load(Path(waiver_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("waiver file must be a YAML or JSON mapping")
    raw_rows = payload.get("waivers")
    if not isinstance(raw_rows, list):
        raise ValueError("waiver file must contain a `waivers` list")
    now = datetime.now(tz=timezone.utc)
    waivers: dict[str, GateWaiver] = {}
    for index, raw in enumerate(raw_rows):
        if not isinstance(raw, dict):
            raise ValueError(f"waivers[{index}] must be an object")
        comparison_id = _required_string(raw, "comparison_id", f"waivers[{index}]")
        reason = _required_string(raw, "reason", f"waivers[{index}]")
        owner = _optional_string(raw.get("owner"))
        expires_at = _optional_string(raw.get("expires_at"))
        active = True
        if expires_at is not None:
            active = _is_future_timestamp(expires_at, now=now)
        waivers[comparison_id] = GateWaiver(
            comparison_id=comparison_id,
            reason=reason,
            owner=owner,
            expires_at=expires_at,
            active=active,
        )
    return waivers


def _required_string(payload: dict[str, object], key: str, label: str) -> str:
    value = payload.get(key)
    if isinstance(value, str) and value.strip():
        return value
    raise ValueError(f"{label}.{key} must be a non-empty string")


def _optional_string(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def _is_future_timestamp(value: str, *, now: datetime) -> bool:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed >= now
