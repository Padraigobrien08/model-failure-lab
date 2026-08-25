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
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from .contracts import FailureDataset

INTEGRITY_METADATA_KEY = "integrity"
CONTENT_DIGEST_KEY = "content_digest"
DIGEST_ALGORITHM = "sha256"
_DIGEST_LENGTH = 16
CURATED_LIFECYCLE = "curated"


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


# --------------------------------------------------------------------------------------
# Workspace audit: a curated pack that cannot be checked is a finding, not a pass.
# --------------------------------------------------------------------------------------
#
# Grandfathering unstamped packs keeps upgrades working, but it also made the guarantee
# trivially removable: deleting `metadata.integrity` from a tampered pack restored every
# pre-digest behavior exactly -- `run` loaded two of four cases and exited 0, and
# `index validate` reported `ok`. Nothing distinguished "written before digests existed"
# from "digest deleted".
#
# `lifecycle: "curated"` does distinguish it enough to matter: only `dataset promote` and
# `dataset evolve` set it, and both have stamped a digest since the feature landed. So a
# curated pack with no digest is either a pre-digest pack or a stripped one, and in both
# cases the honest answer to "is this immutable?" is "I cannot tell" -- which is a finding
# for the command whose whole job is answering that question, not a silent pass.
#
# Loading stays permissive (an old workspace must keep working); `index validate` reports.


@dataclass(slots=True, frozen=True)
class DatasetIntegrityFinding:
    """One dataset whose immutability could not be confirmed."""

    path: Path
    dataset_id: str
    #: `mismatch` = cases changed under a recorded digest. `unstamped` = curated, no digest.
    kind: str
    detail: str

    def message(self) -> str:
        return f"dataset integrity: {self.detail}"


def dataset_integrity_status(dataset: FailureDataset) -> str:
    """`verified`, `mismatch`, `unstamped`, or `unmanaged` (not a curated pack)."""

    recorded = recorded_content_digest(dataset)
    if recorded is None:
        return "unstamped" if dataset.lifecycle == CURATED_LIFECYCLE else "unmanaged"
    return "verified" if compute_content_digest(dataset) == recorded else "mismatch"


def audit_dataset_directory(directory: Path) -> tuple[DatasetIntegrityFinding, ...]:
    """Report every curated pack in `directory` whose digest is missing or wrong.

    Unreadable and malformed files are skipped: the index builder already reports those as
    contract violations, and reporting them twice would bury the integrity answer.
    """

    from .load import parse_dataset_payload

    findings: list[DatasetIntegrityFinding] = []
    if not directory.is_dir():
        return ()
    for path in sorted(directory.glob("*.json")):
        try:
            dataset = parse_dataset_payload(
                json.loads(path.read_text(encoding="utf-8")),
                fallback_dataset_id=path.stem,
            )
        except Exception:  # noqa: BLE001 - malformed packs are the index builder's report
            continue
        status = dataset_integrity_status(dataset)
        if status == "mismatch":
            findings.append(
                DatasetIntegrityFinding(
                    path=path,
                    dataset_id=dataset.dataset_id,
                    kind="mismatch",
                    detail=(
                        f"'{dataset.dataset_id}' ({path}) was modified after promotion: "
                        f"recorded {recorded_content_digest(dataset)}, "
                        f"actual {compute_content_digest(dataset)}. Restore the promoted "
                        "version from source control, or promote the change as a new "
                        "version with `failure-lab dataset evolve`."
                    ),
                )
            )
        elif status == "unstamped":
            findings.append(
                DatasetIntegrityFinding(
                    path=path,
                    dataset_id=dataset.dataset_id,
                    kind="unstamped",
                    detail=(
                        f"curated dataset '{dataset.dataset_id}' ({path}) carries no content "
                        "digest, so its immutability cannot be checked -- it either predates "
                        "digest stamping or had `metadata.integrity` removed. Confirm the "
                        "cases are the ones you promoted, then re-stamp with "
                        f"`failure-lab dataset promote {path} "
                        f"--dataset-id {dataset.dataset_id} --force`."
                    ),
                )
            )
    return tuple(findings)
