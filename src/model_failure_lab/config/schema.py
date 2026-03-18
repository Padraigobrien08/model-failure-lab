"""Typed configuration contracts for experiment execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class RunConfig:
    """Resolved experiment configuration used by scripts and tracking."""

    run_id: str | None
    experiment_name: str
    experiment_group: str
    experiment_type: str
    model_name: str
    dataset_name: str
    split_details: dict[str, str]
    seed: int
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    parent_run_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    model: dict[str, Any] = field(default_factory=dict)
    train: dict[str, Any] = field(default_factory=dict)
    eval: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RunConfig":
        required_fields = {
            "experiment_name",
            "experiment_type",
            "model_name",
            "dataset_name",
            "split_details",
            "seed",
            "data",
            "model",
            "train",
            "eval",
        }
        missing_fields = sorted(
            field_name for field_name in required_fields if field_name not in payload
        )
        if missing_fields:
            missing_text = ", ".join(missing_fields)
            raise ValueError(f"Missing required run config fields: {missing_text}")

        split_details = payload["split_details"]
        if not isinstance(split_details, dict) or not split_details:
            raise ValueError("split_details must be a non-empty mapping")

        seed = payload["seed"]
        if not isinstance(seed, int):
            raise ValueError("seed must be an integer")

        return cls(
            run_id=payload.get("run_id"),
            experiment_name=str(payload["experiment_name"]),
            experiment_group=str(payload.get("experiment_group", payload["experiment_name"])),
            experiment_type=str(payload["experiment_type"]),
            model_name=str(payload["model_name"]),
            dataset_name=str(payload["dataset_name"]),
            split_details={str(key): str(value) for key, value in split_details.items()},
            seed=seed,
            tags=[str(tag) for tag in payload.get("tags", [])],
            notes=str(payload.get("notes", "")),
            parent_run_id=payload.get("parent_run_id"),
            data=dict(payload["data"]),
            model=dict(payload["model"]),
            train=dict(payload["train"]),
            eval=dict(payload["eval"]),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary representation."""
        return asdict(self)
