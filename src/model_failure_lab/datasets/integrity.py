"""Content digests that make a promoted dataset's immutability checkable.

The product's promise is that a harvested regression becomes "a permanent, versioned test
you can re-run forever", and the console labels a promoted pack "immutable". Nothing enforced
either: a promoted dataset had no digest, editing it was undetectable, `index validate`
reported `ok` on a pack with three of four cases deleted, and re-promoting the same id
silently overwrote the version with no warning.

A digest cannot stop someone editing a file on their own disk. What it can do is make the
edit *visible* -- so "immutable" becomes a claim the tool checks rather than a word in a
label. This module computes it; `harvest/review.py` and `datasets/evolution.py` stamp it,
and `datasets/load.py` verifies it on load.

The digest covers the material the dataset asserts -- its id, version, and the ordered cases
-- and deliberately excludes `created_at`, `metadata`, and `source`, so re-stamping
provenance or a promotion timestamp does not invalidate a pack whose cases are unchanged.
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from .contracts import FailureDataset

INTEGRITY_METADATA_KEY = "integrity"
CONTENT_DIGEST_KEY = "content_digest"
DIGEST_ALGORITHM = "sha256"
_DIGEST_LENGTH = 16


class DatasetIntegrityError(Exception):
    """A dataset's recorded content digest does not match its cases."""


def compute_content_digest(dataset: FailureDataset) -> str:
    """Stable digest over a dataset's identity and ordered case content."""

    payload = {
        "dataset_id": dataset.dataset_id,
        "version": dataset.version,
        "cases": [_case_fingerprint(case) for case in dataset.cases],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:_DIGEST_LENGTH]


def _case_fingerprint(case: Any) -> dict[str, Any]:
    """One case's material content: id, prompt, tags, and expectations.

    `metadata` is excluded for the same reason as the dataset's: harvest bookkeeping is
    provenance, not the test being asserted.
    """

    expectations = getattr(case, "expectations", None)
    return {
        "id": case.id,
        "prompt": case.prompt,
        "tags": sorted(case.tags),
        "expectations": expectations.to_payload() if expectations is not None else None,
    }


def integrity_payload(dataset: FailureDataset) -> dict[str, Any]:
    """The `metadata.integrity` block stamped into a curated dataset."""

    return {
        "algorithm": DIGEST_ALGORITHM,
        CONTENT_DIGEST_KEY: compute_content_digest(dataset),
        "case_count": len(dataset.cases),
    }


def recorded_content_digest(dataset: FailureDataset) -> str | None:
    """The digest a dataset claims, or None when it predates digest stamping."""

    integrity = dataset.metadata.get(INTEGRITY_METADATA_KEY)
    if not isinstance(integrity, dict):
        return None
    digest = integrity.get(CONTENT_DIGEST_KEY)
    return digest if isinstance(digest, str) and digest else None


def verify_content_digest(dataset: FailureDataset, *, source: str | None = None) -> None:
    """Raise when a dataset's cases no longer match its recorded digest.

    Packs written before digests existed carry none and are accepted unchanged -- refusing
    them would break every workspace on upgrade. A pack that *claims* a digest must match it.
    """

    recorded = recorded_content_digest(dataset)
    if recorded is None:
        return
    actual = compute_content_digest(dataset)
    if actual == recorded:
        return
    location = f" ({source})" if source else ""
    raise DatasetIntegrityError(
        f"dataset '{dataset.dataset_id}'{location} was modified after promotion: "
        f"recorded content digest {recorded}, actual {actual}. "
        "Restore the promoted version from source control, or promote the change as a new "
        "version with `failure-lab dataset evolve`."
    )
