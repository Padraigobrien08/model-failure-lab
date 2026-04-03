#!/usr/bin/env python3
"""Install-surface smoke that proves the packaged failure-lab CLI works end-to-end."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import venv
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLED_DATASET_ID = "reasoning-failures-v1"
DEMO_DATASET_ID = "demo-failure-cases-v1"


@dataclass(slots=True, frozen=True)
class CommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class SmokeFailure(RuntimeError):
    def __init__(
        self,
        stage: str,
        message: str,
        *,
        command: tuple[str, ...] | None = None,
        returncode: int | None = None,
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        super().__init__(message)
        self.stage = stage
        self.message = message
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    def render(self, temp_root: Path) -> str:
        lines = [f"{self.stage.upper()} FAILURE: {self.message}", f"Temp root: {temp_root}"]
        if self.command is not None:
            lines.append(f"Command: {shlex.join(self.command)}")
        if self.returncode is not None:
            lines.append(f"Exit code: {self.returncode}")
        if self.stdout.strip():
            lines.extend(["stdout:", self.stdout.rstrip()])
        if self.stderr.strip():
            lines.extend(["stderr:", self.stderr.rstrip()])
        return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    temp_root = Path(tempfile.mkdtemp(prefix="failure-lab-package-smoke-"))
    keep_temp = False
    try:
        run_smoke(temp_root, verify_debugger=args.verify_debugger)
    except SmokeFailure as exc:
        keep_temp = True
        print(exc.render(temp_root), file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive top-level fallback
        keep_temp = True
        print(f"UNEXPECTED FAILURE: {exc}\nTemp root: {temp_root}", file=sys.stderr)
        return 1
    finally:
        if not keep_temp:
            shutil.rmtree(temp_root)
    return 0


def run_smoke(temp_root: Path, *, verify_debugger: bool) -> None:
    env_root = temp_root / "venv"
    workspace_root = temp_root / "workspace"
    workspace_root.mkdir(parents=True, exist_ok=True)

    print(f"[setup] temp root: {temp_root}")
    print(f"[setup] workspace: {workspace_root}")

    venv.EnvBuilder(with_pip=True, system_site_packages=True).create(env_root)
    env_python = _env_python(env_root)
    cli_path = _install_package(env_python, env_root)
    _verify_installed_dependency_metadata(env_python)

    demo_result = _run_cli(cli_path, ["demo"], workspace_root)
    _require_output(demo_result, "Failure Lab Demo", command_name="demo")

    baseline_run_id = _single_entry((workspace_root / "runs").iterdir(), kind="run")
    demo_report_id = _single_entry((workspace_root / "reports").iterdir(), kind="report")

    run_dirs_before = _entry_names(workspace_root / "runs")
    report_dirs_before = _entry_names(workspace_root / "reports")

    run_result = _run_cli(
        cli_path,
        ["run", "--dataset", INSTALLED_DATASET_ID, "--model", "demo"],
        workspace_root,
    )
    _require_output(run_result, "Failure Lab Run", command_name="run")

    candidate_run_id = _new_entry_name(
        before=run_dirs_before,
        after=_entry_names(workspace_root / "runs"),
        kind="run",
    )

    report_result = _run_cli(
        cli_path,
        ["report", "--run", candidate_run_id],
        workspace_root,
    )
    _require_output(report_result, "Failure Lab Report", command_name="report")

    rebuilt_report_id = _new_entry_name(
        before=report_dirs_before,
        after=_entry_names(workspace_root / "reports"),
        kind="report",
    )
    report_dirs_before = _entry_names(workspace_root / "reports")

    compare_result = _run_cli(
        cli_path,
        ["compare", baseline_run_id, candidate_run_id],
        workspace_root,
    )
    _require_output(compare_result, "Failure Lab Compare", command_name="compare")

    comparison_report_id = _new_entry_name(
        before=report_dirs_before,
        after=_entry_names(workspace_root / "reports"),
        kind="report",
    )

    _verify_artifacts(
        workspace_root=workspace_root,
        baseline_run_id=baseline_run_id,
        candidate_run_id=candidate_run_id,
        demo_report_id=demo_report_id,
        rebuilt_report_id=rebuilt_report_id,
        comparison_report_id=comparison_report_id,
    )

    if verify_debugger:
        _verify_debugger_handoff(workspace_root)

    if verify_debugger:
        print("Package install smoke passed with debugger verification.")
    else:
        print("Package install smoke passed.")


def _install_package(env_python: Path, env_root: Path) -> Path:
    install_command = (
        str(env_python),
        "-m",
        "pip",
        "install",
        "--no-build-isolation",
        "--no-deps",
        str(REPO_ROOT),
    )
    result = _run_command(
        install_command,
        cwd=REPO_ROOT,
        stage="install",
        label="pip install",
        allow_failure=True,
    )
    if result is None:
        raise SmokeFailure("install", "pip install did not return a result.")
    if result.stderr.count("invalid command 'bdist_wheel'") > 0:
        wheel_asset = _find_local_wheel_asset()
        if wheel_asset is None:
            raise SmokeFailure(
                "install",
                "pip install could not build the package because `bdist_wheel` is unavailable "
                "and no local wheel bootstrap artifact was found.",
                command=install_command,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=1,
            )
        print("[install] bdist_wheel unavailable; bootstrapping local wheel support")
        _run_command(
            (
                str(env_python),
                "-m",
                "pip",
                "install",
                "--no-deps",
                str(wheel_asset),
            ),
            cwd=REPO_ROOT,
            stage="install",
            label="bootstrap local wheel",
        )
        result = _run_command(
            install_command,
            cwd=REPO_ROOT,
            stage="install",
            label="pip install",
            allow_failure=True,
        )
        if result is None:
            raise SmokeFailure("install", "pip install retry did not return a result.")
    if result is None:
        raise SmokeFailure("install", "pip install did not return a result.")
    if result.returncode != 0:
        raise SmokeFailure(
            "install",
            "pip install failed.",
            command=install_command,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    cli_path = _env_cli(env_root)
    if not cli_path.exists():
        raise SmokeFailure(
            "install",
            "pip install completed but the installed `failure-lab` console script was not created.",
            command=install_command,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    _verify_installed_module_path(env_python, env_root)
    return cli_path


def _run_cli(cli_path: Path, args: list[str], workspace_root: Path) -> CommandResult:
    return _run_command(
        (str(cli_path), *args),
        cwd=workspace_root,
        stage="cli",
        label=f"failure-lab {' '.join(args)}",
    )


def _run_command(
    command: tuple[str, ...],
    *,
    cwd: Path,
    stage: str,
    label: str,
    allow_failure: bool = False,
) -> CommandResult | None:
    print(f"[{stage}] {label}")
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=_command_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    should_echo_output = not allow_failure or completed.returncode == 0
    if should_echo_output and completed.stdout.strip():
        print(completed.stdout.rstrip())
    if should_echo_output and completed.stderr.strip():
        print(completed.stderr.rstrip(), file=sys.stderr)
    if completed.returncode != 0 and not allow_failure:
        raise SmokeFailure(
            stage,
            f"{label} failed.",
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    return CommandResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _find_local_wheel_asset() -> Path | None:
    stdlib_root = Path(sysconfig.get_path("stdlib")).resolve()
    candidates = sorted(
        stdlib_root.parents[2].glob("*/lib/python*/test/wheeldata/wheel-*.whl"),
        reverse=True,
    )
    if candidates:
        return candidates[0]
    return None


def _verify_installed_module_path(env_python: Path, env_root: Path) -> None:
    result = _run_command(
        (
            str(env_python),
            "-c",
            (
                "import pathlib, model_failure_lab; "
                "print(pathlib.Path(model_failure_lab.__file__).resolve())"
            ),
        ),
        cwd=REPO_ROOT,
        stage="install",
        label="verify installed module path",
    )
    module_path = Path(result.stdout.strip().splitlines()[-1]).resolve()
    if env_root.resolve() not in module_path.parents:
        raise SmokeFailure(
            "install",
            f"`model_failure_lab` resolved outside the temp environment: {module_path}",
            command=result.command,
            stdout=result.stdout,
            stderr=result.stderr,
        )


def _verify_installed_dependency_metadata(env_python: Path) -> None:
    result = _run_command(
        (
            str(env_python),
            "-c",
            (
                "import importlib.metadata as metadata, json; "
                "dist = metadata.distribution('model-failure-lab'); "
                "print(json.dumps(dist.metadata.get_all('Requires-Dist') or []))"
            ),
        ),
        cwd=REPO_ROOT,
        stage="install",
        label="verify installed dependency metadata",
    )
    try:
        requires_dist = json.loads(result.stdout.strip().splitlines()[-1])
    except json.JSONDecodeError as exc:
        raise SmokeFailure(
            "install",
            "installed package metadata did not return valid Requires-Dist JSON.",
            command=result.command,
            stdout=result.stdout,
            stderr=result.stderr,
        ) from exc
    if not isinstance(requires_dist, list) or not all(
        isinstance(item, str) for item in requires_dist
    ):
        raise SmokeFailure(
            "install",
            "installed package metadata did not expose Requires-Dist entries as strings.",
            command=result.command,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    base_requirements = [item for item in requires_dist if "extra ==" not in item]
    optional_requirements = [item for item in requires_dist if "extra ==" in item]

    if base_requirements != ["PyYAML"]:
        raise SmokeFailure(
            "install",
            f"unexpected base Requires-Dist entries: {base_requirements}.",
            command=result.command,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    _require_extra_marker(optional_requirements, "openai", "openai")
    _require_extra_marker(optional_requirements, "ui", "streamlit")
    for package_name in (
        "matplotlib",
        "pandas",
        "pyarrow",
        "scikit-learn",
        "torch",
        "transformers",
        "wilds",
    ):
        _require_extra_marker(optional_requirements, "legacy", package_name)


def _require_extra_marker(requires_dist: list[str], extra_name: str, package_name: str) -> None:
    expected_marker = f"extra == '{extra_name}'"
    for item in requires_dist:
        if package_name in item and expected_marker in item:
            return
    raise SmokeFailure(
        "install",
        f"missing optional dependency marker for {package_name!r} under extra {extra_name!r}.",
    )


def _command_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env["PIP_NO_CACHE_DIR"] = "1"
    return env


def _env_python(env_root: Path) -> Path:
    if os.name == "nt":
        return env_root / "Scripts" / "python.exe"
    return env_root / "bin" / "python"


def _env_cli(env_root: Path) -> Path:
    candidates = (
        env_root / "bin" / "failure-lab",
        env_root / "Scripts" / "failure-lab.exe",
        env_root / "Scripts" / "failure-lab",
        env_root / "Scripts" / "failure-lab.cmd",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _entry_names(root: Path) -> set[str]:
    if not root.exists():
        return set()
    return {entry.name for entry in root.iterdir()}


def _single_entry(entries, *, kind: str) -> str:
    names = sorted(entry.name for entry in entries)
    if len(names) != 1:
        raise SmokeFailure(
            "verify",
            f"expected exactly one {kind} artifact after the first command, found {names or 'none'}.",
        )
    return names[0]


def _new_entry_name(*, before: set[str], after: set[str], kind: str) -> str:
    names = sorted(after - before)
    if len(names) != 1:
        raise SmokeFailure(
            "verify",
            f"expected exactly one new {kind} artifact, found {names or 'none'}.",
        )
    return names[0]


def _require_output(result: CommandResult, expected_heading: str, *, command_name: str) -> None:
    if expected_heading not in result.stdout:
        raise SmokeFailure(
            "cli",
            f"`failure-lab {command_name}` succeeded but did not print the expected summary heading "
            f"`{expected_heading}`.",
            command=result.command,
            stdout=result.stdout,
            stderr=result.stderr,
        )


def _verify_artifacts(
    *,
    workspace_root: Path,
    baseline_run_id: str,
    candidate_run_id: str,
    demo_report_id: str,
    rebuilt_report_id: str,
    comparison_report_id: str,
) -> None:
    demo_dataset = workspace_root / "datasets" / f"{DEMO_DATASET_ID}.json"
    _require_file(demo_dataset, "demo dataset snapshot")

    _require_run_artifacts(workspace_root / "runs" / baseline_run_id)
    _require_run_artifacts(workspace_root / "runs" / candidate_run_id)
    _require_report_artifacts(workspace_root / "reports" / demo_report_id)
    _require_report_artifacts(workspace_root / "reports" / rebuilt_report_id)
    comparison_report_dir = workspace_root / "reports" / comparison_report_id
    _require_report_artifacts(comparison_report_dir)

    report_payload = _read_json(comparison_report_dir / "report.json")
    comparison = report_payload.get("comparison")
    if not isinstance(comparison, dict):
        raise SmokeFailure(
            "verify",
            "comparison report did not include a `comparison` payload.",
        )
    if comparison.get("baseline_run_id") != baseline_run_id:
        raise SmokeFailure(
            "verify",
            "comparison report baseline run ID did not match the demo run.",
        )
    if comparison.get("candidate_run_id") != candidate_run_id:
        raise SmokeFailure(
            "verify",
            "comparison report candidate run ID did not match the bundled run.",
        )


def _verify_debugger_handoff(workspace_root: Path) -> None:
    smoke_script = REPO_ROOT / "frontend" / "scripts" / "smoke-real-artifacts.mjs"
    _run_command(
        (
            "node",
            str(smoke_script),
            "--mode",
            "existing",
            "--artifact-root",
            str(workspace_root),
        ),
        cwd=REPO_ROOT,
        stage="verify",
        label="verify debugger handoff",
    )


def _require_run_artifacts(run_dir: Path) -> None:
    _require_file(run_dir / "run.json", "run artifact")
    _require_file(run_dir / "results.json", "results artifact")


def _require_report_artifacts(report_dir: Path) -> None:
    _require_file(report_dir / "report.json", "report artifact")
    _require_file(report_dir / "report_details.json", "report details artifact")


def _require_file(path: Path, description: str) -> None:
    if not path.is_file():
        raise SmokeFailure(
            "verify",
            f"expected {description} at {path}.",
        )


def _read_json(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SmokeFailure("verify", f"expected JSON artifact at {path}.") from exc
    if not isinstance(payload, dict):
        raise SmokeFailure("verify", f"expected object payload in {path}.")
    return payload


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prove that the installed failure-lab package works end-to-end.",
    )
    parser.add_argument(
        "--verify-debugger",
        action="store_true",
        help="Verify that the generated artifact workspace also loads through the debugger contract.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
