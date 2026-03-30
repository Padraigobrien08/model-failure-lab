"""Summary/detail artifact emission helpers for the new reporting seam."""

from __future__ import annotations

from pathlib import Path

from model_failure_lab.schemas import JsonValue, Report
from model_failure_lab.storage import report_details_file, report_file, write_json


def build_report_payload(report: Report) -> dict[str, JsonValue]:
    """Build the persisted compact report summary payload."""

    return report.to_payload()


def build_report_details_payload(details: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Build the persisted report detail payload."""

    return dict(details)


def write_report_artifacts(
    report: Report,
    details: dict[str, JsonValue],
    *,
    root: str | Path | None = None,
) -> tuple[Path, Path]:
    """Persist one compact summary report plus its supporting detail artifact."""

    report_path = report_file(report.report_id, root=root, create=True)
    details_path = report_details_file(report.report_id, root=root, create=True)
    write_json(report_path, build_report_payload(report))
    write_json(details_path, build_report_details_payload(details))
    return report_path, details_path
