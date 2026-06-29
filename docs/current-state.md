# Current State Assessment

> Baseline audit, generated 2026-06-29. Based on executed commands and source inspection.

## What's working (verified)

| Area | Evidence |
|---|---|
| Production CLI core loop | `python3 -m model_failure_lab demo` runs end-to-end; writes datasets/runs/reports |
| Bundled datasets | `datasets list` returns reasoning/rag/hallucination packs |
| Lint | `ruff check src tests` → "All checks passed!" (ruff 0.13.3) |
| Production test subset | 59 tests passed across CLI/runner/harvest/governance/dataset-evolution; `make test-fast` → 9 passed |
| Packaging | `model-failure-lab` 0.1.0 installed & importable; prebuilt wheel/sdist in `dist/` |
| Deterministic artifacts | Stable run IDs, sorted-key JSON, slugified paths (`storage/layout.py`) |

## What's incomplete / broken

| Area | State | Evidence |
|---|---|---|
| Full test suite | **Broken in audit env** | `pytest -q` → 252 passed, 1 failed, 23 errors (numpy/pandas ABI) |
| `reporting` package import | Partially broken | pandas-backed symbols fail to import in audit env |
| Legacy benchmark stack | Reference-only, env-fragile | `docs/legacy.md`; depends on the broken numpy/pandas pair |
| Live model adapters (anthropic/openai/ollama) | Not exercised | No credentials/Ollama in audit env |
| React UI | Not exercised | `npm run dev` not run |
| Screenshots referenced in README | Absent | `docs/screens/` referenced but image files not confirmed present |

## Major risks

| Risk | Severity | Notes |
|---|---|---|
| numpy/pandas ABI breakage blocks green CI/tests | **High** | Whether CI is currently green depends on pip resolving a compatible pair on a fresh `[dev,legacy]` install — not reproduced here |
| Legacy/production entanglement in `reporting/` & dual subsystems | **High** | Refactoring risk; easy to touch the wrong path (`runner/` vs `runners/`, `index/` vs `artifact_index/`) |
| `cli.py` god module | **Medium-High** | Concentrated change risk; weak isolation for testing |
| Heavy/undeclared deps (`torch`, `torchvision`, `sentence-transformers`) | **Medium** | Install fragility, slow CI, unclear necessity |
| Artifact written to CWD by default | **Low-Medium** | Can pollute working dirs; mitigated by `--root`/`make clean` |

## Missing / thin test coverage (observed)

- **Live adapters:** `anthropic`/`openai`/`ollama` adapters are tested for contract shape
  (`test_model_adapters.py`) but no live integration test exists (expected — they need credentials).
- **End-to-end full-loop test under a clean environment:** the full suite cannot currently run green,
  so the legacy-touching paths are effectively unverified in this environment.
- **Cycle/architecture tests:** no import-cycle or layering enforcement test was found.
- **Frontend:** 28 Vitest files exist under `frontend/src/**/__tests__`; not executed in this audit
  (Node run not performed).

> Test count: 60 Python test files in `tests/unit/`; production subset verified green, legacy subset
> blocked by D1 (see `docs/technical-debt.md`).

## Estimated maturity by subsystem

> Subjective audit rating (Mature / Developing / Fragile / Reference-only), based on code + tests run.

| Subsystem | Maturity | Rationale |
|---|---|---|
| `runner/`, `adapters/`, `classifiers/`, `schemas/`, `storage/` | **Mature** | Clean contracts, dataclasses, passing tests, demo works |
| `datasets/` (load/bundled/evolution) | **Mature** | Tests pass; evolution/promotion exercised |
| `governance/`, `harvest/`, `clusters`, `history` | **Developing** | Large surface, tests pass, but very large modules |
| `index/` (SQLite) | **Developing** | Works (`index validate` in CI), 1.1k-LOC builder |
| `analysis/` | **Developing** | Insight reports; fixture-tested |
| `reporting/` | **Fragile** | Mixed prod/legacy; import breaks with pandas issue |
| `cli.py` | **Fragile** | Functionally works but structurally unwieldy |
| `models/`, `mitigations/`, `perturbations/`, `evaluation/`, `data/`, `runners/`, `tracking/`, `artifact_index/`, `results_ui/`, `config/` | **Reference-only / Fragile** | Legacy; blocked by ABI issue; declared non-supported |
| `frontend/` | **Unverified** | Substantial (routes + tests) but not run in audit |

## Suggestions for modernization (not implemented)

> These are recommendations only; no application code was changed in this audit.

1. **Fix the dependency floor (P0).** Pin a compatible numpy/pandas pair in `[legacy]` (e.g.
   `numpy<2`) or split legacy deps so production imports never touch pandas. Restores a green suite.
2. **Extract the legacy benchmark stack** into a separate optional package (or archive it). Removes
   ~half the surface, the heaviest deps, and the `reporting/` entanglement.
3. **Decompose `cli.py`** into per-command modules with thin handlers that call library functions and
   return structured results; move `print()` to a presentation layer.
4. **Unify path/root handling** behind one resolver and one documented env var; deprecate the
   duplicate (`utils/paths.py` vs `storage/layout.py`).
5. **Disambiguate or merge** `runner/`↔`runners/` and `index/`↔`artifact_index/`.
6. **De-duplicate** payload-validation and slug helpers into a shared `utils`/`schemas` module.
7. **Drop undeclared/unused deps** (`torchvision`, `sentence-transformers`) after confirming.
8. **Add a layering/import-cycle test** to lock in the production/legacy boundary once established.
