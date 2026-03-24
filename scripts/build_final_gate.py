# ruff: noqa: E402

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

try:
    from scripts._bootstrap import bootstrap_repo_paths
except ModuleNotFoundError:
    from _bootstrap import bootstrap_repo_paths

bootstrap_repo_paths()

from model_failure_lab.reporting import (
    DEFAULT_REOPEN_CONDITIONS,
    build_final_gate_payload,
    load_saved_json,
    write_final_gate,
)
from model_failure_lab.runners.contracts import DispatchResult
from model_failure_lab.utils.paths import build_final_gate_path, repository_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the final dataset-expansion gate artifact from saved reports."
    )
    parser.add_argument("--stability-summary", required=True)
    parser.add_argument("--robustness-summary", required=True)
    parser.add_argument("--robustness-report", required=True)
    parser.add_argument("--promotion-audit", required=True)
    parser.add_argument("--output")
    parser.add_argument("--gate-name", default="phase27_gate")
    parser.add_argument("--findings-doc", default="docs/v1_4_closeout.md")
    parser.add_argument("--ui-entrypoint", default="scripts/run_results_ui.py")
    parser.add_argument(
        "--reopen-condition",
        action="append",
        dest="reopen_conditions",
        default=None,
        help=(
            "Add one explicit reopen condition. May be provided multiple times. "
            "Defaults to the locked Phase 27 conditions."
        ),
    )
    return parser


def _repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repository_root()))
    except ValueError:
        return path.as_posix()


def run_command(argv: Sequence[str] | None = None) -> DispatchResult:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else build_final_gate_path(str(args.gate_name), create=True).resolve()
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    stability_summary_path = Path(args.stability_summary).expanduser().resolve()
    robustness_summary_path = Path(args.robustness_summary).expanduser().resolve()
    robustness_report_path = Path(args.robustness_report).expanduser().resolve()
    promotion_audit_path = Path(args.promotion_audit).expanduser().resolve()

    payload = build_final_gate_payload(
        gate_name=str(args.gate_name),
        stability_summary=load_saved_json(stability_summary_path),
        robustness_summary=load_saved_json(robustness_summary_path),
        robustness_report_data=load_saved_json(robustness_report_path),
        promotion_audit_path=promotion_audit_path,
        stability_summary_path=stability_summary_path,
        robustness_summary_path=robustness_summary_path,
        robustness_report_data_path=robustness_report_path,
        reopen_conditions=args.reopen_conditions or list(DEFAULT_REOPEN_CONDITIONS),
        findings_doc_path=str(args.findings_doc),
        ui_entrypoint_path=str(args.ui_entrypoint),
    )
    payload["supporting_artifact_refs"]["final_gate_json"] = _repo_relative(output_path)
    write_final_gate(output_path, payload)
    return DispatchResult(
        status="completed",
        message=f"Final gate written to {output_path}",
        run_dir=output_path.parent,
        metadata_path=output_path,
        metrics_path=output_path,
    )


def main(argv: Sequence[str] | None = None) -> int:
    result = run_command(argv)
    print(result.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
