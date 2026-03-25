from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.sync_react_ui_manifest import run_command


def _write_manifest(path: Path, *, schema_version: str = "artifact_index_v1") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": schema_version,
                "entities": {
                    "runs": [],
                    "evaluations": [],
                    "reports": [
                        {
                            "id": "phase26_report",
                            "artifact_refs": {
                                "report_data_json": {
                                    "path": "artifacts/reports/comparisons/phase26/report_data.json",
                                    "exists": True,
                                }
                            },
                            "payload_refs": {
                                "report_data_json": {
                                    "path": "artifacts/reports/comparisons/phase26/report_data.json",
                                    "exists": True,
                                }
                            },
                            "metadata_path": "artifacts/reports/comparisons/phase26/metadata.json",
                        }
                    ],
                },
                "views": {
                    "seeded_cohorts": [],
                    "mitigation_comparisons": [],
                    "stability_packages": [],
                    "research_closeout": [],
                },
            }
        ),
        encoding="utf-8",
    )


def _write_report_payloads(root: Path) -> None:
    report_dir = root / "artifacts" / "reports" / "comparisons" / "phase26"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "report_data.json").write_text('{"official_method_summaries":[]}', encoding="utf-8")
    (report_dir / "metadata.json").write_text('{"status":"completed"}', encoding="utf-8")


def test_sync_react_ui_manifest_copies_source_contract(tmp_path: Path):
    source = tmp_path / "artifacts" / "contracts" / "artifact_index" / "v1" / "index.json"
    target_root = tmp_path / "frontend" / "public"
    _write_manifest(source)
    _write_report_payloads(tmp_path)

    result = run_command(["--source", str(source), "--target-root", str(target_root)])
    target = target_root / "artifacts" / "contracts" / "artifact_index" / "v1" / "index.json"
    payload_copy = target_root / "artifacts" / "reports" / "comparisons" / "phase26" / "report_data.json"

    assert result.status == "completed"
    assert target.exists()
    assert payload_copy.exists()
    assert source.read_text(encoding="utf-8") == target.read_text(encoding="utf-8")


def test_sync_react_ui_manifest_check_mode_requires_parity(tmp_path: Path):
    source = tmp_path / "artifacts" / "contracts" / "artifact_index" / "v1" / "index.json"
    target_root = tmp_path / "frontend" / "public"
    _write_manifest(source)
    _write_report_payloads(tmp_path)
    run_command(["--source", str(source), "--target-root", str(target_root)])

    result = run_command(
        ["--source", str(source), "--target-root", str(target_root), "--check"]
    )

    assert result.status == "completed"
    assert "in sync" in result.message


def test_sync_react_ui_manifest_rejects_wrong_schema(tmp_path: Path):
    source = tmp_path / "artifacts" / "contracts" / "artifact_index" / "v1" / "index.json"
    _write_manifest(source, schema_version="artifact_index_v2")

    with pytest.raises(ValueError):
        run_command(["--source", str(source), "--target-root", str(tmp_path / "frontend" / "public")])


def test_sync_react_ui_manifest_check_mode_detects_payload_drift(tmp_path: Path):
    source = tmp_path / "artifacts" / "contracts" / "artifact_index" / "v1" / "index.json"
    target_root = tmp_path / "frontend" / "public"
    _write_manifest(source)
    _write_report_payloads(tmp_path)
    run_command(["--source", str(source), "--target-root", str(target_root)])

    payload_copy = target_root / "artifacts" / "reports" / "comparisons" / "phase26" / "report_data.json"
    payload_copy.write_text('{"official_method_summaries":["stale"]}', encoding="utf-8")

    with pytest.raises(ValueError):
        run_command(["--source", str(source), "--target-root", str(target_root), "--check"])
