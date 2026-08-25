""""Immutable" has to be a guarantee the tool checks, not a word in a label.

The README sells a harvested regression as "a permanent, versioned test you can re-run
forever" and the console labelled a promoted pack immutable. Nothing enforced it: a promoted
dataset carried no digest, deleting three of its four cases was undetectable, `index validate`
reported `ok` on the tampered pack, and re-promoting the same id silently overwrote the
version and exited 0.

A digest cannot stop an edit on someone's own disk. It can make the edit *visible*, which is
what turns the claim into something checkable:

* `dataset promote` and `dataset evolve` stamp `metadata.integrity.content_digest`,
* `load_dataset` verifies it, so a tampered pack fails at every consumer, and
* `dataset promote` refuses to write over an existing curated version without `--force`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from model_failure_lab.cli import main
from model_failure_lab.datasets import load_dataset
from model_failure_lab.datasets.integrity import (
    DatasetIntegrityError,
    compute_content_digest,
    recorded_content_digest,
)
from model_failure_lab.harvest import DatasetPromotionConflictError, promote_harvest_dataset

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_RUNS = PROJECT_ROOT / "examples" / "regression_demo" / "runs"
COMPARISON_ID = "compare_8ba8496a_to_dda18a0e_66320e7c"
DATASET_ID = "support-regressions-v1"


@pytest.fixture()
def promoted_workspace(tmp_path: Path) -> tuple[Path, Path]:
    """A workspace with one promoted curated dataset. Returns (root, dataset_path)."""

    root = tmp_path / "workspace"
    runs = root / "runs"
    runs.mkdir(parents=True)
    for name in ("baseline", "candidate"):
        destination = runs / name
        destination.mkdir()
        for filename in ("run.json", "results.json"):
            (destination / filename).write_text(
                (DEMO_RUNS / name / filename).read_text(encoding="utf-8"), encoding="utf-8"
            )

    assert main(["compare", "baseline", "candidate", "--root", str(root)]) == 0
    draft = "datasets/harvested/reg.json"
    assert (
        main(
            [
                "harvest",
                "--comparison",
                COMPARISON_ID,
                "--delta",
                "regression",
                "--out",
                draft,
                "--root",
                str(root),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "dataset",
                "promote",
                str(root / draft),
                "--dataset-id",
                DATASET_ID,
                "--root",
                str(root),
            ]
        )
        == 0
    )
    return root, root / "datasets" / f"{DATASET_ID}.json"


def _tamper(dataset_path: Path) -> None:
    """Delete all but one case and rewrite its prompt -- the original attack."""

    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    payload["cases"] = payload["cases"][:1]
    payload["cases"][0]["prompt"] = "TAMPERED"
    dataset_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def test_promotion_records_a_content_digest(promoted_workspace: tuple[Path, Path]) -> None:
    _, dataset_path = promoted_workspace
    dataset = load_dataset(dataset_path)

    recorded = recorded_content_digest(dataset)
    assert recorded is not None, "a promoted version must record its content digest"
    assert recorded == compute_content_digest(dataset)
    integrity = dataset.metadata["integrity"]
    assert integrity["algorithm"] == "sha256"
    assert integrity["case_count"] == len(dataset.cases)


def test_loading_a_tampered_dataset_fails_loudly(
    promoted_workspace: tuple[Path, Path],
) -> None:
    _, dataset_path = promoted_workspace
    _tamper(dataset_path)

    with pytest.raises(DatasetIntegrityError) as excinfo:
        load_dataset(dataset_path)
    message = str(excinfo.value)
    # The message has to tell the operator what to do, not just that a hash mismatched.
    assert DATASET_ID in message
    assert "modified after promotion" in message
    assert "dataset evolve" in message


def test_running_a_tampered_dataset_exits_non_zero(
    promoted_workspace: tuple[Path, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, dataset_path = promoted_workspace
    _tamper(dataset_path)

    # The consumer-visible contract: CI running a tampered regression pack must fail, not
    # quietly test one edited case and report 100% coverage.
    exit_code = main(["run", "--dataset", DATASET_ID, "--model", "demo", "--root", str(root)])
    assert exit_code == 1
    assert "modified after promotion" in capsys.readouterr().err


def test_index_validate_rejects_a_tampered_dataset(
    promoted_workspace: tuple[Path, Path],
) -> None:
    root, dataset_path = promoted_workspace
    assert main(["index", "rebuild", "--root", str(root)]) == 0
    assert main(["index", "validate", "--root", str(root)]) == 0

    _tamper(dataset_path)
    # Exit 2 is `index validate`'s documented "contracts do not hold" code
    # (docs/api.md, docs/ci-governance.md). A tampered pack used to escape the rebuild as
    # an unhandled exception and exit 1 -- indistinguishable, to a CI script, from the
    # command itself crashing.
    assert main(["index", "validate", "--root", str(root)]) == 2


def test_promote_refuses_to_overwrite_an_existing_version(
    promoted_workspace: tuple[Path, Path],
) -> None:
    root, dataset_path = promoted_workspace
    before = dataset_path.read_text(encoding="utf-8")

    with pytest.raises(DatasetPromotionConflictError) as excinfo:
        promote_harvest_dataset(
            root / "datasets" / "harvested" / "reg.json",
            dataset_id=DATASET_ID,
            root=root,
        )
    message = str(excinfo.value)
    assert "immutable" in message
    assert "dataset evolve" in message
    assert "--force" in message
    # And the refusal left the promoted version byte-identical.
    assert dataset_path.read_text(encoding="utf-8") == before


def test_promote_force_replaces_deliberately(
    promoted_workspace: tuple[Path, Path],
) -> None:
    root, dataset_path = promoted_workspace
    _tamper(dataset_path)

    # --force is the documented escape hatch, and it restores a pack whose digest verifies.
    summary = promote_harvest_dataset(
        root / "datasets" / "harvested" / "reg.json",
        dataset_id=DATASET_ID,
        root=root,
        force=True,
    )
    assert summary.output_path == dataset_path
    restored = load_dataset(dataset_path)
    assert recorded_content_digest(restored) == compute_content_digest(restored)
    assert len(restored.cases) > 1


def test_evolved_versions_also_record_a_digest(tmp_path: Path) -> None:
    from model_failure_lab.datasets import evolve_dataset_family
    from model_failure_lab.testing import materialize_insight_fixture

    workspace = materialize_insight_fixture(tmp_path / "fx")
    summary = evolve_dataset_family(
        "insight-fixture-regressions",
        comparison_id="compare_66f669a9_to_df4f8650_1094b97e",
        root=workspace.root,
    )

    # Both writers of a curated version must behave the same way, or "immutable" holds only
    # on whichever path a given operator happened to use.
    evolved = load_dataset(summary.output_path)
    assert recorded_content_digest(evolved) == compute_content_digest(evolved)


def test_a_pack_without_a_digest_still_loads(tmp_path: Path) -> None:
    # Datasets written before digests existed carry none. Rejecting them would break every
    # existing workspace on upgrade, so absence is accepted and only a mismatch is an error.
    legacy = tmp_path / "legacy.json"
    legacy.write_text(
        json.dumps(
            {
                "dataset_id": "legacy-v1",
                "name": "Legacy",
                "cases": [{"id": "case-1", "prompt": "hello"}],
            }
        ),
        encoding="utf-8",
    )

    dataset = load_dataset(legacy)
    assert recorded_content_digest(dataset) is None
    assert len(dataset.cases) == 1


def test_digest_ignores_provenance_but_tracks_case_content(tmp_path: Path) -> None:
    from model_failure_lab.datasets import parse_dataset_payload

    base = {
        "dataset_id": "digest-v1",
        "name": "Digest",
        "cases": [{"id": "case-1", "prompt": "hello", "tags": ["core"]}],
    }
    original = compute_content_digest(parse_dataset_payload(base))

    # Re-stamping provenance or a promotion timestamp must not invalidate a pack whose cases
    # are unchanged, or every metadata write would look like tampering.
    with_provenance = {**base, "created_at": "2030-01-01T00:00:00Z", "source": {"type": "x"}}
    assert compute_content_digest(parse_dataset_payload(with_provenance)) == original

    # Changing what a case actually asserts must change the digest.
    edited = {**base, "cases": [{"id": "case-1", "prompt": "goodbye", "tags": ["core"]}]}
    assert compute_content_digest(parse_dataset_payload(edited)) != original
    dropped = {**base, "cases": []}
    assert compute_content_digest(parse_dataset_payload(dropped)) != original


# ---------------------------------------------------------------------------------------
# Removing the digest was the bypass: it restored every pre-digest behavior exactly.
# ---------------------------------------------------------------------------------------
#
# Grandfathering unstamped packs is right for loading -- an old workspace must keep working
# -- but it also meant deleting `metadata.integrity` made a tampered pack load silently with
# two of its four cases while `index validate` still exited 0. `lifecycle: "curated"` is the
# discriminator: only `dataset promote` and `dataset evolve` set it, and both stamp a digest,
# so a curated pack with no digest is a pack whose immutability cannot be checked.


def _strip_integrity(dataset_path: Path) -> None:
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    payload["metadata"].pop("integrity", None)
    dataset_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_index_validate_rejects_a_curated_pack_whose_digest_was_removed(
    promoted_workspace: tuple[Path, Path],
) -> None:
    root, dataset_path = promoted_workspace
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    payload["cases"] = payload["cases"][:2]
    dataset_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _strip_integrity(dataset_path)

    # Before: exit 0 and "ok". The tamper was invisible once the digest went with it.
    assert main(["index", "validate", "--root", str(root)]) == 2


def test_the_unstamped_finding_names_the_pack_and_a_command_that_re_stamps_it(
    promoted_workspace: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    root, dataset_path = promoted_workspace
    _strip_integrity(dataset_path)

    assert main(["index", "validate", "--root", str(root)]) == 2
    output = capsys.readouterr().out
    assert DATASET_ID in output
    assert str(dataset_path) in output
    # DESIGN.md's rule for errors, applied to the CLI: say what failed, which file, and what
    # to run. A remedy the reader cannot paste is not a remedy.
    assert "--force" in output
    assert "failure-lab dataset promote" in output


def test_re_stamping_clears_the_finding(promoted_workspace: tuple[Path, Path]) -> None:
    root, dataset_path = promoted_workspace
    _strip_integrity(dataset_path)
    assert main(["index", "validate", "--root", str(root)]) == 2

    assert (
        main(
            [
                "dataset",
                "promote",
                str(dataset_path),
                "--dataset-id",
                DATASET_ID,
                "--root",
                str(root),
                "--force",
            ]
        )
        == 0
    )
    assert main(["index", "validate", "--root", str(root)]) == 0


def test_an_unstamped_pack_that_was_never_promoted_is_not_a_finding(tmp_path: Path) -> None:
    # A hand-authored prompt pack has no lifecycle and makes no immutability claim, so it
    # must not be dragged into the curated-pack audit.
    root = tmp_path / "workspace"
    (root / "datasets").mkdir(parents=True)
    (root / "datasets" / "mine.json").write_text(
        json.dumps(
            {
                "dataset_id": "mine-v1",
                "name": "Mine",
                "cases": [{"id": "case-1", "prompt": "hello"}],
            }
        ),
        encoding="utf-8",
    )

    assert main(["index", "validate", "--root", str(root)]) == 0


def test_audit_classifies_each_pack_state(tmp_path: Path) -> None:
    from model_failure_lab.datasets import parse_dataset_payload
    from model_failure_lab.datasets.integrity import (
        audit_dataset_directory,
        dataset_integrity_status,
        integrity_payload,
    )

    base = {
        "dataset_id": "state-v1",
        "name": "State",
        "lifecycle": "curated",
        "cases": [{"id": "case-1", "prompt": "hello"}],
    }
    stamped = {**base, "metadata": {"integrity": integrity_payload(parse_dataset_payload(base))}}

    assert dataset_integrity_status(parse_dataset_payload(stamped)) == "verified"
    assert dataset_integrity_status(parse_dataset_payload(base)) == "unstamped"
    assert dataset_integrity_status(parse_dataset_payload({**base, "lifecycle": None})) == (
        "unmanaged"
    )
    tampered = {**stamped, "cases": [{"id": "case-1", "prompt": "goodbye"}]}
    assert dataset_integrity_status(parse_dataset_payload(tampered)) == "mismatch"

    directory = tmp_path / "datasets"
    directory.mkdir()
    (directory / "ok.json").write_text(json.dumps(stamped), encoding="utf-8")
    (directory / "bare.json").write_text(json.dumps(base), encoding="utf-8")
    (directory / "broken.json").write_text("{not json", encoding="utf-8")

    findings = audit_dataset_directory(directory)
    # The malformed file is the index builder's finding to report, not this one's.
    assert [finding.kind for finding in findings] == ["unstamped"]
    assert findings[0].path.name == "bare.json"
