"""CivilComments-specific WILDS integration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable


class DataDependencyError(RuntimeError):
    """Raised when an optional data dependency required for execution is missing."""


@dataclass(frozen=True, slots=True)
class SplitRole:
    """Resolved project-local split role layered on top of raw WILDS split names."""

    name: str
    raw_split: str
    selector: str
    is_id: bool
    is_ood: bool
    holdout_fraction: float | None = None
    holdout_seed: int | None = None


def _resolve_get_dataset(
    get_dataset_fn: Callable[..., Any] | None = None,
) -> Callable[..., Any]:
    if get_dataset_fn is not None:
        return get_dataset_fn
    try:
        module = import_module("wilds")
    except ModuleNotFoundError as exc:
        raise DataDependencyError(
            "CivilComments materialization requires the 'wilds' package. "
            "Install the legacy benchmark extra with "
            "`python -m pip install -e '.[legacy]'`, run "
            "`python scripts/check_environment.py`, and then rerun "
            "`python scripts/download_data.py`."
        ) from exc

    get_dataset = getattr(module, "get_dataset", None)
    if not callable(get_dataset):
        raise DataDependencyError(
            "The installed 'wilds' package does not expose get_dataset(). "
            "Run `python scripts/check_environment.py` to verify the legacy benchmark setup."
        )
    return get_dataset


def resolve_split_policy(data_config: dict[str, Any]) -> dict[str, SplitRole]:
    """Return the project-local split policy for canonical data processing."""
    policy_payload = data_config["split_role_policy"]
    resolved_policy: dict[str, SplitRole] = {}
    for role_name, role_config in policy_payload.items():
        resolved_policy[role_name] = SplitRole(
            name=role_name,
            raw_split=str(role_config["raw_split"]),
            selector=str(role_config["selector"]),
            is_id=bool(role_config["is_id"]),
            is_ood=bool(role_config["is_ood"]),
            holdout_fraction=(
                float(role_config["holdout_fraction"])
                if "holdout_fraction" in role_config
                else None
            ),
            holdout_seed=int(role_config["holdout_seed"])
            if "holdout_seed" in role_config
            else None,
        )
    return resolved_policy


def load_civilcomments_dataset(
    data_config: dict[str, Any],
    *,
    download: bool = True,
    get_dataset_fn: Callable[..., Any] | None = None,
) -> Any:
    """Load CivilComments via the official WILDS dataset entrypoint."""
    get_dataset = _resolve_get_dataset(get_dataset_fn)
    return get_dataset(
        dataset=str(data_config.get("wilds_dataset_name", data_config["dataset_name"])),
        root_dir=str(data_config.get("wilds_root_dir", "data/wilds")),
        download=download,
    )
