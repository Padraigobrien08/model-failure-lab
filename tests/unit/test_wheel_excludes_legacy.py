"""`pip install model-failure-lab` must ship only the supported workflow.

`pyproject.toml` has said so since the packaging was written. It was not true: the exclude
list named seven legacy packages and missed `utils`, `tracking`, `artifact_index` and
`config`, and `reporting` was a single package holding both surfaces -- so setuptools could
exclude it whole or not at all. Nineteen modules importing torch / pandas / numpy /
scikit-learn / matplotlib shipped in the wheel, where they raise `ImportError` on use.

The import-time guard in `test_production_cli_isolation.py` never caught it, and could not:
it asserts that *importing the production surface* pulls in no heavy dependency, which was
always true. Shipping a module and importing it are different questions.

This walks the package set setuptools will actually build and reads the source of every
module in it, so a new legacy-coupled module -- or a legacy package added without an
exclude entry -- fails here rather than in a user's virtualenv.
"""

from __future__ import annotations

import fnmatch
import re
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

#: Third-party roots that belong to the optional `[legacy]` extra, never to the wheel.
HEAVY_IMPORT = re.compile(
    r"^\s*(?:from|import)\s+"
    r"(torch|torchvision|pandas|numpy|sklearn|matplotlib|transformers|wilds|pyarrow|streamlit)\b",
    re.MULTILINE,
)

#: The legacy artifact layout (`MODEL_FAILURE_LAB_ARTIFACT_ROOT`), which production code
#: must never touch -- it uses `storage/layout.py`.
LEGACY_LAYOUT_IMPORT = re.compile(r"model_failure_lab\.(utils|tracking)\b")


def _wheel_packages() -> list[str]:
    """The package list `[tool.setuptools.packages.find]` resolves to.

    Resolved by walking `src/` and applying the include/exclude globs the way setuptools
    does, rather than importing `setuptools.discovery`: setuptools is a build-time tool and
    is not in the `dev` extra, nor in a stock Python 3.12 virtualenv, so importing it made
    this module fail to collect on 3.12 while passing on 3.11. The wheel *itself* is checked
    by the `consumer-install` CI job; this is the fast local guard.
    """

    config = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    find = config["tool"]["setuptools"]["packages"]["find"]
    include = tuple(find.get("include", ("*",)))
    exclude = tuple(find.get("exclude", ()))

    names = []
    for init in SRC_ROOT.rglob("__init__.py"):
        name = ".".join(init.parent.relative_to(SRC_ROOT).parts)
        if not name:
            continue
        if not any(fnmatch.fnmatchcase(name, pattern) for pattern in include):
            continue
        if any(fnmatch.fnmatchcase(name, pattern) for pattern in exclude):
            continue
        names.append(name)
    return sorted(names)


def _shipped_modules() -> list[Path]:
    packages = _wheel_packages()
    package_dirs = {SRC_ROOT.joinpath(*name.split(".")) for name in packages}
    return sorted(
        path
        for directory in package_dirs
        for path in directory.glob("*.py")
        # Only the package's own modules; subpackages appear as their own entry, and one
        # that was excluded must not be swept back in through its parent's glob.
        if path.parent in package_dirs
    )


def test_the_wheel_ships_the_production_surface_and_nothing_else() -> None:
    assert _wheel_packages() == [
        "model_failure_lab",
        "model_failure_lab.adapters",
        "model_failure_lab.analysis",
        "model_failure_lab.classifiers",
        "model_failure_lab.datasets",
        "model_failure_lab.governance",
        "model_failure_lab.harvest",
        "model_failure_lab.index",
        "model_failure_lab.reporting",
        "model_failure_lab.runner",
        "model_failure_lab.schemas",
        "model_failure_lab.storage",
        "model_failure_lab.testing",
    ], (
        "the wheel's package set changed. Adding a production package is fine -- add it "
        "here. Seeing a legacy package appear means it needs an entry in "
        "`[tool.setuptools.packages.find] exclude`."
    )


def test_no_shipped_module_imports_the_legacy_ml_stack() -> None:
    offenders = [
        str(path.relative_to(SRC_ROOT))
        for path in _shipped_modules()
        if HEAVY_IMPORT.search(path.read_text(encoding="utf-8"))
    ]
    assert not offenders, (
        f"these modules ship in the wheel but import the optional [legacy] extra: "
        f"{offenders}. They raise ImportError for anyone who `pip install`ed the package. "
        "Move them under a package the exclude list covers."
    )


def test_no_shipped_module_reads_the_legacy_artifact_layout() -> None:
    # Two different layouts exist (CLAUDE.md, docs/legacy.md): production resolves paths
    # through `storage/layout.py`, the legacy stack through `utils/paths.py`. A shipped
    # module reaching for the latter would read from a root the production CLI never writes.
    offenders = [
        str(path.relative_to(SRC_ROOT))
        for path in _shipped_modules()
        if LEGACY_LAYOUT_IMPORT.search(path.read_text(encoding="utf-8"))
    ]
    assert not offenders, (
        f"these modules ship in the wheel but import the legacy artifact layout: {offenders}"
    )


def test_the_legacy_reporting_surface_is_still_reachable_from_a_checkout() -> None:
    # Excluding it from the wheel must not delete it: docs/legacy.md offers it for
    # reference, and `make test-legacy` runs against it.
    legacy = SRC_ROOT / "model_failure_lab" / "reporting" / "legacy"
    assert (legacy / "__init__.py").is_file()
    assert {path.stem for path in legacy.glob("*.py")} == {
        "__init__",
        "bundle",
        "calibration",
        "closeout",
        "discovery",
        "figures",
        "mitigation",
        "perturbation",
        "robustness",
        "selection",
        "stability",
        "summary",
        "tables",
    }
