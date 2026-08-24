"""Policy-as-code regression gates with waiver support."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

from model_failure_lab.index import QueryFilters
from model_failure_lab.schemas import JsonValue
from model_failure_lab.storage.layout import project_root

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
        # CI blocking is a verdict decision, not a dataset-governance decision. Any
        # un-waived regression blocks the gate, exactly like `compare --gate` -- the
        # severity floor governs only whether to create/evolve a dataset family
        # (recommendation.action), never whether CI turns green. Tying blocking to the
        # create/evolve action previously let a below-minimum-severity regression pass
        # the governance/console gate while failing `compare --gate` on the same runs.
        should_block = signal_verdict == "regression"
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
