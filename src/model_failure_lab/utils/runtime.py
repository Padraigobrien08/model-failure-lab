"""Runtime environment helpers for script execution and diagnostics."""

from __future__ import annotations

import importlib
import os
import tempfile
from importlib import metadata as importlib_metadata
from pathlib import Path


def _is_writable_directory(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe_path = path / ".write_probe"
        probe_path.write_text("ok", encoding="utf-8")
        probe_path.unlink()
    except OSError:
        return False
    return True


def ensure_matplotlib_runtime_dir(preferred_path: str | Path | None = None) -> Path:
    """Set MPLCONFIGDIR to a writable deterministic path and return it."""
    candidates: list[Path] = []
    if preferred_path is not None:
        candidates.append(Path(preferred_path))
    env_path = os.environ.get("MPLCONFIGDIR")
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(Path(tempfile.gettempdir()) / "model_failure_lab_mplconfig")

    for candidate in candidates:
        if _is_writable_directory(candidate):
            os.environ["MPLCONFIGDIR"] = str(candidate)
            return candidate

    raise RuntimeError("Unable to configure a writable MPLCONFIGDIR for report generation.")


def check_python_dependency(package_name: str) -> dict[str, object]:
    """Return a small diagnostic record for an importable Python dependency."""
    try:
        module = importlib.import_module(package_name)
    except Exception as exc:
        return {
            "package": package_name,
            "available": False,
            "version": None,
            "error": str(exc),
        }

    try:
        version = importlib_metadata.version(package_name)
    except importlib_metadata.PackageNotFoundError:
        version = getattr(module, "__version__", None)

    return {
        "package": package_name,
        "available": True,
        "version": version,
        "error": None,
    }
