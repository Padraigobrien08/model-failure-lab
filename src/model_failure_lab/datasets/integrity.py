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
from typing import Any

from model_failure_lab.storage import write_json

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


def audit_dataset_directory(
    directory: Path,
    *,
    ledger: dict[str, PromotionRecord] | None = None,
) -> tuple[DatasetIntegrityFinding, ...]:
    """Report every promoted pack in `directory` whose digest is missing or wrong.

    Two witnesses, because one inside the file can be deleted along with the marker that
    made its absence suspicious:

    * the pack's own `metadata.integrity`, gated on `lifecycle: "curated"`, and
    * `governance/promotions.json`, which records outside the pack that this dataset id was
      promoted and what its digest was.

    A pack stripped of both its integrity block and its lifecycle is self-consistent, and
    the ledger is what turns it back into a contradiction.

    Unreadable and malformed files are skipped: the index builder already reports those as
    contract violations, and reporting them twice would bury the integrity answer.
    """

    from .load import parse_dataset_payload

    ledger = {} if ledger is None else ledger
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
        recorded = ledger.get(dataset.dataset_id)
        if status == "unmanaged" and recorded is not None:
            # The ledger says this id was promoted; the pack no longer admits to being
            # curated and carries no digest. Exactly the shape of a stripped pack.
            actual = compute_content_digest(dataset)
            detail = (
                f"'{dataset.dataset_id}' ({path}) was promoted on {recorded.promoted_at} "
                f"with {recorded.case_count} case(s) and digest {recorded.content_digest}, "
                f"but the file now carries no integrity block and is not marked curated "
                f"(actual digest {actual}, {len(dataset.cases)} case(s)). Restore it from "
                "source control, or re-promote it with `--force` if the change is intended."
            )
            findings.append(
                DatasetIntegrityFinding(
                    path=path,
                    dataset_id=dataset.dataset_id,
                    kind="unrecorded",
                    detail=detail,
                )
            )
            continue
        if status == "verified" and recorded is not None:
            actual = compute_content_digest(dataset)
            if actual != recorded.content_digest:
                # Self-consistent, but not the pack that was promoted: someone re-stamped
                # the digest after editing. The ledger is the only thing that still knows.
                findings.append(
                    DatasetIntegrityFinding(
                        path=path,
                        dataset_id=dataset.dataset_id,
                        kind="re_stamped",
                        detail=(
                            f"'{dataset.dataset_id}' ({path}) carries a valid digest "
                            f"{actual}, but was promoted with {recorded.content_digest} on "
                            f"{recorded.promoted_at}. Its cases changed and the digest was "
                            "recomputed. Restore from source control, or re-promote with "
                            "`--force` to accept the change."
                        ),
                    )
                )
            continue
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


# --------------------------------------------------------------------------------------
# The promotion ledger: a witness that does not live inside the artifact it protects.
# --------------------------------------------------------------------------------------
#
# Stamping `metadata.integrity` catches an edit, and gating on `lifecycle: "curated"`
# catches deleting the stamp. Neither survives deleting *both*, and no scheme keyed on the
# pack's own fields ever will -- the witness is inside the thing it is meant to witness.
#
# `governance/promotions.json` records, outside the pack, that a dataset id was promoted and
# what its digest was at the time. A pack whose id is in the ledger must still match; one
# that has had its integrity block and lifecycle removed is now a *contradiction* between
# two files rather than a self-consistent lie.
#
# It lives in `governance/` for the same reason waivers and baselines do: it is a record of
# something a human did, it belongs in git, and `make clean` must not touch it.

PROMOTION_LEDGER_PATH = "governance/promotions.json"


@dataclass(slots=True, frozen=True)
class PromotionRecord:
    """One promotion, as recorded outside the promoted file."""

    dataset_id: str
    content_digest: str
    case_count: int
    promoted_at: str
    path: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "content_digest": self.content_digest,
            "case_count": self.case_count,
            "promoted_at": self.promoted_at,
            "path": self.path,
        }


def load_promotion_ledger(root: Path) -> dict[str, PromotionRecord]:
    """Every recorded promotion, keyed by dataset id. Missing or malformed reads as empty."""

    path = root / PROMOTION_LEDGER_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    rows = payload.get("promotions") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return {}
    records: dict[str, PromotionRecord] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        dataset_id = row.get("dataset_id")
        digest = row.get(CONTENT_DIGEST_KEY)
        if not isinstance(dataset_id, str) or not isinstance(digest, str):
            continue
        records[dataset_id] = PromotionRecord(
            dataset_id=dataset_id,
            content_digest=digest,
            case_count=int(row.get("case_count") or 0),
            promoted_at=str(row.get("promoted_at") or ""),
            path=str(row.get("path") or ""),
        )
    return records


def write_curated_dataset(
    dataset: FailureDataset,
    *,
    path: Path,
    root: Path,
    promoted_at: str,
) -> FailureDataset:
    """The one way a curated dataset reaches disk: stamped, written, and recorded.

    Two commands produce a `lifecycle: curated` pack -- `dataset promote` and
    `dataset evolve` -- and both guarantees have to hold for both of them. They did not:
    0.13.0 added the ledger and wired it into `promote` only, so an evolved version kept
    the bypass the ledger exists to close. Stripping `metadata.integrity` and `lifecycle`
    from an evolved pack left `index validate` at exit 0 with three of four cases gone,
    while the same edit to a promoted pack was caught. `dataset evolve` is the mode the
    console's harvest dialog offers first, so the guarantee failed on the common path.

    Keeping the stamp, the write, and the ledger entry in one function is the point: a
    third writer cannot pick up two of the three, because there is nothing to pick from.
    `tests/unit/test_curated_packs_are_recorded.py` drives every curated-producing command
    and asserts the ledger grew, so a new one that routes around this door fails there.
    """

    stamped = FailureDataset(
        dataset_id=dataset.dataset_id,
        name=dataset.name,
        description=dataset.description,
        version=dataset.version,
        created_at=dataset.created_at,
        lifecycle=dataset.lifecycle,
        source=dataset.source,
        cases=dataset.cases,
        metadata={**dataset.metadata, INTEGRITY_METADATA_KEY: integrity_payload(dataset)},
    )
    write_json(path, stamped.to_payload())
    record_promotion(stamped, root=root, dataset_path=path, promoted_at=promoted_at)
    return stamped


def record_promotion(
    dataset: FailureDataset,
    *,
    root: Path,
    dataset_path: Path,
    promoted_at: str,
) -> Path:
    """Write this promotion into the ledger, replacing any earlier entry for the same id."""

    records = load_promotion_ledger(root)
    try:
        relative = dataset_path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        relative = dataset_path.as_posix()
    records[dataset.dataset_id] = PromotionRecord(
        dataset_id=dataset.dataset_id,
        content_digest=compute_content_digest(dataset),
        case_count=len(dataset.cases),
        promoted_at=promoted_at,
        path=relative,
    )
    path = root / PROMOTION_LEDGER_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        # Sorted by id: the file is committed, so two promotions must not reorder the diff.
        "promotions": [records[key].to_payload() for key in sorted(records)]
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
