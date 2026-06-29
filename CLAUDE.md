# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Model Failure Lab is a local-first toolkit for evaluating LLM/RAG systems. The supported product
loop is `run -> report -> compare -> harvest -> promote -> rerun`: execute a prompt dataset against a
model adapter, classify failures, diff baseline vs candidate, harvest regressions into reusable
datasets, and promote them into immutable versions. The core value is deterministic artifact history,
so determinism and stable artifact contracts matter more than raw feature count.

## Commands

```bash
make install-dev      # editable install with dev extras (pytest, ruff)
make check            # lint + full test suite (run before considering work done)
make lint             # ruff check src tests
make test             # pytest -q (full suite)
make test-fast        # smoke + governance tests only (fast feedback)
make demo             # deterministic demo flow
make smoke            # clean-clone smoke: install + demo + datasets-list + run + report
```

Run a single test:

```bash
python3 -m pytest tests/unit/test_cli_governance.py -q
python3 -m pytest tests/unit/test_cli.py::<test_name> -q
```

The CLI is invokable three ways (all equivalent): `failure-lab <cmd>`, `model-failure-lab <cmd>`,
or `python3 -m model_failure_lab <cmd>`. Top-level commands: `run report compare demo datasets
dataset index query history clusters cluster regressions harvest`.

Frontend (React debugger, in `frontend/`):

```bash
npm --prefix frontend run dev      # needs FAILURE_LAB_ARTIFACT_ROOT pointing at a workspace
npm --prefix frontend run build    # tsc typecheck + vite build
npm --prefix frontend test         # vitest
```

## Architecture

### Two distinct surfaces — know which one you're touching

This repo contains two largely separate systems. Most new work belongs to the production path; the
legacy path is retained for reference only (see `docs/legacy.md`).

1. **Production LLM/RAG workflow (supported).** Driven by `cli.py`. Artifacts are **CWD-relative**:
   `datasets/`, `runs/`, `reports/`, `governance/` under the active root, resolved by
   `storage/layout.py:project_root()` which honors the `--root` flag (defaults to `Path.cwd()`).
   Datasets are JSON prompt packs; runs/reports/comparisons are JSON artifacts.

2. **Legacy ML benchmark surfaces (reference only).** `models/` (distilbert, logistic_tfidf),
   `mitigations/`, `perturbations/`, `evaluation/`, `tracking/`, and the Streamlit `results_ui/`.
   These use a **different** layout in `utils/paths.py`: rooted at `MODEL_FAILURE_LAB_ARTIFACT_ROOT`
   (default `artifacts/`), with `baselines/`, `mitigations/`, parquet predictions, WILDS data, etc.
   The `scripts/` directory and `[legacy]`/`[ui]` extras mostly serve this path. Don't wire new
   production features through here.

Note the two env vars are different: production React UI reads `FAILURE_LAB_ARTIFACT_ROOT`; the
legacy/`utils.paths` system reads `MODEL_FAILURE_LAB_ARTIFACT_ROOT` (and `MODEL_FAILURE_LAB_CONFIG_ROOT`).

### Production module layout

- `cli.py` — single argparse surface; each subcommand has an `_handle_*` function. This is large; the
  command/handler pairs are the entry points for tracing any behavior.
- `runner/` — run execution (`execute.py`) and artifact writing (`artifacts.py`).
- `adapters/` — model invocation backends registered in `adapters/registry.py`. Supports `demo`,
  `ollama:<model>`, `anthropic:<model>`, and OpenAI model names. To add a backend, implement the
  contract in `adapters/contracts.py` and register it. (Use the latest Claude models for the
  Anthropic adapter — e.g. `claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5-20251001`.)
- `reporting/` — run reports, comparison deltas (`compare.py`), signal drivers (`signals.py`).
- `index/` — derived **SQLite** projection over local artifacts (`.failure_lab/`). Build with
  `failure-lab index rebuild`, validate contracts with `failure-lab index validate`. Query surfaces
  (`query`, `clusters`, `regressions`, `history`) read from this index.
- `governance/` — turns comparison signals into deterministic actions: policy recommendations,
  gate decisions, lifecycle/portfolio workflows, baseline registry.
- `harvest/` + `datasets/evolution.py` — harvest failing/regressing cases into draft packs, then
  promote into immutable curated dataset versions.
- `clusters.py` + `governance/intelligence.py` — recurring failure cluster / root-cause summaries.
- `storage/layout.py` — **the** source of truth for production artifact paths.

See `docs/code-map.md` for a "if you want to change X, edit file Y" table and
`docs/artifact-model.md` for concrete artifact payload contracts.

## Conventions

- Python 3.11+, `from __future__ import annotations` everywhere, `ruff` (line-length 100, E501
  ignored; rules E/F/I — import sorting is enforced).
- Output and artifacts must be **deterministic** (sorted keys, stable IDs). Tests assert on exact
  artifact payloads, so changing output shape means updating contracts intentionally.
- Tests live in `tests/unit/`. The CLI/governance smoke tests (`test_cli_production_smoke.py`,
  `test_cli_governance.py`) are the fastest signal that the production loop still works.
- Only `PyYAML` is a hard runtime dependency. Model providers, the legacy stack, and the Streamlit UI
  are all optional extras — keep production code importable without them.
