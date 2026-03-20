from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def bootstrap_repo_paths() -> Path:
    """Ensure repo-root script execution can import project packages."""
    repo_root = Path(__file__).resolve().parents[1]
    src_root = repo_root / "src"

    if importlib.util.find_spec("model_failure_lab") is None:
        for path in (repo_root, src_root):
            path_str = str(path)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)
    else:
        repo_root_str = str(repo_root)
        if repo_root_str not in sys.path:
            sys.path.insert(0, repo_root_str)

    return repo_root
