# ruff: noqa: E402

from __future__ import annotations

import argparse
import json
from typing import Any, Sequence

try:
    from scripts._bootstrap import bootstrap_repo_paths
except ModuleNotFoundError:
    from _bootstrap import bootstrap_repo_paths

bootstrap_repo_paths()

from model_failure_lab.config import load_experiment_config
from model_failure_lab.utils.runtime import (
    check_python_dependency,
    ensure_matplotlib_runtime_dir,
)

_DEPENDENCIES = ("matplotlib", "wilds", "torch", "transformers")
_DISTILBERT_PRESET = "civilcomments_distilbert_baseline"
_INSTALL_COMMAND = "python -m pip install -e '.[dev,legacy]'"


def _distilbert_prefetch_command(pretrained_name: str) -> str:
    return (
        "python -c \"from transformers import AutoModelForSequenceClassification, "
        f"AutoTokenizer; AutoTokenizer.from_pretrained('{pretrained_name}'); "
        f"AutoModelForSequenceClassification.from_pretrained('{pretrained_name}')\""
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify benchmark runtime prerequisites.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def _check_transformer_assets(pretrained_name: str) -> dict[str, object]:
    dependency_status = check_python_dependency("transformers")
    if not dependency_status["available"]:
        return {
            "pretrained_name": pretrained_name,
            "local_cache_available": False,
            "message": "Transformers is not installed.",
        }

    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    try:
        AutoTokenizer.from_pretrained(pretrained_name, local_files_only=True)
        AutoModelForSequenceClassification.from_pretrained(
            pretrained_name,
            local_files_only=True,
        )
    except Exception:
        return {
            "pretrained_name": pretrained_name,
            "local_cache_available": False,
            "message": (
                "Local cache not detected. The first DistilBERT run will require "
                "network access or a pre-populated local cache."
            ),
        }

    return {
        "pretrained_name": pretrained_name,
        "local_cache_available": True,
        "message": "Local cache available for DistilBERT assets.",
    }


def run_command(
    argv: Sequence[str] | None = None,
    *,
    dependency_checker=check_python_dependency,
    matplotlib_dir_resolver=ensure_matplotlib_runtime_dir,
    config_loader=load_experiment_config,
    transformer_asset_checker=_check_transformer_assets,
) -> dict[str, Any]:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    distilbert_config = config_loader(_DISTILBERT_PRESET)
    pretrained_name = str(distilbert_config.get("model", {}).get("pretrained_name", ""))
    dependency_status = {
        package: dependency_checker(package)
        for package in _DEPENDENCIES
    }
    matplotlib_dir = matplotlib_dir_resolver()
    transformer_assets = transformer_asset_checker(pretrained_name)
    all_dependencies_available = all(
        bool(status["available"]) for status in dependency_status.values()
    )
    payload = {
        "dependencies": dependency_status,
        "matplotlib": {
            "runtime_dir": str(matplotlib_dir),
            "writable": True,
        },
        "distilbert": transformer_assets,
        "overall_ok": all_dependencies_available,
    }

    if args.as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        missing_packages = [
            package_name
            for package_name, status in dependency_status.items()
            if not bool(status["available"])
        ]
        print("Model Failure Lab environment check")
        print(f"Matplotlib runtime dir: {payload['matplotlib']['runtime_dir']}")
        for package_name, status in dependency_status.items():
            state = "ok" if status["available"] else "missing"
            version = status["version"] or "unknown"
            print(f"{package_name}: {state} ({version})")
        if missing_packages:
            print(
                "Install missing benchmark dependencies with:\n"
                f"  {_INSTALL_COMMAND}"
            )
        print(
            f"DistilBERT model: {transformer_assets['pretrained_name']} "
            f"(local cache: {'yes' if transformer_assets['local_cache_available'] else 'no'})"
        )
        print(transformer_assets["message"])
        if not transformer_assets["local_cache_available"]:
            print(
                "To pre-populate the Hugging Face cache before the first run, use:\n"
                f"  {_distilbert_prefetch_command(pretrained_name)}"
            )

    return payload


def main(argv: Sequence[str] | None = None) -> int:
    payload = run_command(argv)
    return 0 if payload["overall_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
