# Setup Guide

> Baseline audit, generated 2026-06-29. Commands marked **✓ verified** were executed during the audit
> on macOS (Darwin 24.5.0), Python 3.11.0. Commands marked **(not run)** are documented from
> `Makefile` / `README.md` / `.github/workflows/ci.yml` but were not executed.

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | `pyproject.toml` `requires-python = ">=3.11"`; audited with 3.11.0 |
| pip | recent | Used for all install paths |
| Node.js + npm | — | Only for the React UI (`frontend/`). Not required for the Python CLI. Exact version not pinned in repo. |
| Ollama | local install | Only for `--model ollama:*` |
| Anthropic/OpenAI API keys | — | Only for `anthropic:*` / OpenAI adapters |

## Installation

### Production CLI (minimal)

```bash
make install            # python3 -m pip install .   (not run; equivalent install verified present)
# or
python3 -m pip install .
```

The package installs the console scripts `failure-lab` and `model-failure-lab`
(`pyproject.toml [project.scripts]`). It can also be run as `python3 -m model_failure_lab`.

> ✓ Verified: `model-failure-lab` 0.1.0 is importable and the `demo` command works (see below).

### Development environment

```bash
make install-dev        # python3 -m pip install -e '.[dev]'   (adds pytest + ruff)
```

### Optional extras

```bash
python3 -m pip install '.[anthropic]'   # Anthropic adapter
python3 -m pip install '.[openai]'      # OpenAI adapter
python3 -m pip install '.[legacy]'      # torch/transformers/pandas/sklearn/pyarrow/wilds
python3 -m pip install '.[ui]'          # Streamlit legacy UI
```

### Frontend (React UI)

```bash
npm --prefix frontend install           # (not run)
```

## Environment variables

| Variable | Used by | Default | Purpose |
|---|---|---|---|
| `MODEL_FAILURE_LAB_ARTIFACT_ROOT` | `src/.../utils/paths.py` (legacy + test fixtures) | `<repo>/artifacts` | Legacy artifact root |
| `MODEL_FAILURE_LAB_CONFIG_ROOT` | `src/.../utils/paths.py` | `<repo>/configs` | Legacy config root |
| `FAILURE_LAB_ARTIFACT_ROOT` | React UI, `scripts/run_react_ui.py` | — | Workspace the React debugger reads |
| `TWINE_USERNAME` / `TWINE_PASSWORD` | `make publish` | — | PyPI upload (`__token__` + token) |
| API keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) | SDKs inside adapters | — | Live model calls (read by the SDKs, not custom code) |

> Note the production CLI does **not** use `MODEL_FAILURE_LAB_ARTIFACT_ROOT`. It writes relative to the
> current working directory unless `--root` is passed (`storage/layout.py`).

## Build process

```bash
make build              # pip install build && python -m build   -> dist/*.whl, *.tar.gz   (not run)
make verify-dist        # twine check dist/*                                                 (not run)
make publish            # twine upload dist/* (requires TWINE_* env)                         (not run)
```

A prebuilt `dist/model_failure_lab-0.1.0-py3-none-any.whl` and `.tar.gz` already exist in `dist/`.

## Running locally

```bash
# Deterministic demo (writes datasets/, runs/, reports/ in the CWD)
python3 -m model_failure_lab demo                         # ✓ verified

# Canonical loop
failure-lab run --dataset reasoning-failures-v1 --model demo
failure-lab report --run <run-id>
failure-lab compare <baseline-run-id> <candidate-run-id>
failure-lab harvest --comparison <comparison-id> --delta regression \
  --out datasets/harvested/regression-pack.json
failure-lab dataset promote datasets/harvested/regression-pack.json \
  --dataset-id reasoning-regressions-v1

# Inspect bundled datasets
python3 -m model_failure_lab datasets list                # ✓ verified (returns 3 core packs)

# Build/validate the derived query index
failure-lab index rebuild
failure-lab index validate
```

> ✓ Verified `demo` output: dataset `demo-failure-cases-v1`, 4 cases classified, 75% failure rate,
> artifacts written under `datasets/`, `runs/<id>/`, `reports/<id>/`.

> **Tip:** run these from a scratch directory (not the repo root) to avoid creating `runs/`,
> `reports/`, `.failure_lab/` inside the checkout. These paths are gitignored but accumulate locally.
> `make clean` removes them.

### React UI (not run)

```bash
export FAILURE_LAB_ARTIFACT_ROOT=/path/to/workspace
npm --prefix frontend run dev        # or: python3 scripts/run_react_ui.py
```

## Running tests

```bash
make lint               # python3 -m ruff check src tests      # ✓ verified: "All checks passed!"
make test               # production suite (legacy auto-skipped without [legacy]) # ✓ verified
make test-fast          # smoke + governance subset            # ✓ verified: 9 passed
make test-legacy        # legacy ML tests (needs '.[legacy]' installed)
```

### Verified test results (`oss-hardening` branch)

| Command | Result |
|---|---|
| `ruff check src tests` | **✓ All checks passed** (ruff 0.13.3) |
| `pytest -q` (production) | **✓ 249 passed, 1 skipped** |
| `make test-fast` | **✓ 9 passed** |

On the `oss-hardening` branch, `tests/conftest.py` probes whether the optional `[legacy]` ML stack
(`numpy`/`pandas`/`torch`/`scikit-learn`) is *cleanly importable*. When it is absent **or**
present-but-broken (e.g. the `numpy.dtype size changed` ABI mismatch from numpy 2.x against a pandas
built for numpy 1.x), the legacy-only test modules are ignored at collection and `@pytest.mark.legacy`
tests are skipped — so `pytest -q` is green on a production-only install. In CI, where
`.[dev,legacy]` is installed with compatible versions, the legacy tests run as well.

> Baseline note: before this branch, `pytest -q` produced **252 passed, 1 failed, 23 collection
> errors**, all caused by the numpy/pandas ABI mismatch. See `docs/technical-debt.md` (D1).

Run a single test:

```bash
python3 -m pytest tests/unit/test_cli.py::<test_name> -q
python3 -m pytest tests/unit/test_cli_governance.py -q
```

## Common issues

| Symptom | Cause | Fix |
|---|---|---|
| `ValueError: numpy.dtype size changed` when running legacy tests | numpy 2.x installed against pandas built for numpy 1.x | The production `pytest -q` auto-skips legacy tests in this case (see "Running tests"). To run them, reinstall `.[legacy]` into a clean venv so pip resolves a compatible numpy/pandas pair, or pin `numpy<2`. |
| Importing `model_failure_lab.reporting` pulls in pandas/matplotlib | Production and legacy reporting share one package | Import the specific module (`reporting.core`, `reporting.compare`) rather than the package, or install `[legacy]`. |
| `failure-lab: command not found` | Console script not on PATH | Use `python3 -m model_failure_lab <cmd>` |
| `UnknownModelAdapterError` | Model string not recognized / SDK extra missing | Install `[anthropic]`/`[openai]`, or use `demo` |
| Stray `runs/`, `reports/`, `.failure_lab/` in checkout | CLI writes to CWD | Run from a scratch dir, or `make clean` |
| `npm` not found when launching React UI | Node not installed | Install Node.js/npm (`scripts/run_react_ui.py` errors clearly if npm is absent) |

## CI reference

`.github/workflows/ci.yml` (on push + PR): Python 3.11 → `pip install .` → `pip install -e
'.[dev,legacy]'` → `pytest -q` → `ruff check` → CLI smoke (`demo`, `datasets list`, `run`, `report`,
`index validate`). The fresh `[dev,legacy]` install is expected to resolve a compatible numpy/pandas
pair (not reproduced in this audit — see Assumptions in `docs/overview.md`).
