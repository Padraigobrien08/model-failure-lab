# Technical Debt Report

> Baseline audit, generated 2026-06-29. Findings are evidence-based with file references. Severity:
> **P0** (blocks work / broken), **P1** (high — impedes modernization), **P2** (medium), **P3** (low).

## Severity summary

| ID | Severity | Issue | Evidence |
|---|---|---|---|
| D1 | **P0** | numpy/pandas ABI mismatch breaks full test suite & `reporting` import | `pytest -q` → 1 failed + 23 collection errors, all `numpy.dtype size changed` |
| D2 | **P1** | Production and legacy code interleaved in shared packages (`reporting/`) | `reporting/__init__.py` lazy `__getattr__` workaround; `bundle.py` imports pandas |
| D3 | **P1** | `cli.py` is a 4,157-line god module (44 handlers, 88 `print()` calls, 126 defs) | `src/model_failure_lab/cli.py` |
| D4 | **P1** | Two parallel path/root systems + confusingly similar env vars | `utils/paths.py` vs `storage/layout.py`; `MODEL_FAILURE_LAB_ARTIFACT_ROOT` vs `FAILURE_LAB_ARTIFACT_ROOT` |
| D5 | **P1** | Duplicate run-execution & index subsystems with near-identical names | `runner/` vs `runners/`; `index/` vs `artifact_index/` |
| D6 | **P2** | Payload-validation helpers duplicated across ≥6 modules | `def _require_mapping` in 6 contract files; `_normalize_segment` in 4 files |
| D7 | **P2** | Undeclared/unused heavy dependencies installed | `torchvision`, `sentence-transformers` installed, **no imports** in `src/` |
| D8 | **P2** | Several very large modules (>800 LOC) concentrate logic | `governance/portfolio.py` (1,340), `index/builder.py` (1,116), `governance/execution.py` (1,029) |
| D9 | **P3** | Legacy benchmark scaffolding dominates the tree but is "reference only" | `models/`, `mitigations/`, `perturbations/`, `evaluation/`, `data/`, `configs/`, ~half of `scripts/` |
| D10 | **P3** | Output coupling: business logic prints directly in CLI | 88 `print(` calls in `cli.py` |

## Details

### D1 — numpy/pandas ABI mismatch (P0)

`python3 -m pytest -q` cannot collect 23 test files and fails 1 test, **all** with
`ValueError: numpy.dtype size changed`. Root cause: numpy 2.2.6 with pandas 2.1.1 (compiled against
numpy 1.x). Every affected file is legacy/ML or imports the pandas-backed `reporting` chain
(`test_reporting_imports.py` fails because `reporting.bundle` does `import pandas`). The production
test subset (CLI/runner/harvest/governance) passes cleanly (59 tests verified).

- **Impact:** No green full-suite run in the audited environment; `import model_failure_lab.reporting`
  of pandas-backed symbols fails.
- **Fix direction:** pin a compatible numpy/pandas pair in the `[legacy]` extra (e.g. `numpy<2` or
  pandas ≥2.2), or fully isolate legacy deps from the production import path. **Not changed in this
  audit (analysis-only task).**

### D2 — production/legacy entanglement in `reporting/` (P1)

`reporting/` contains production modules (`core.py`, `compare.py`, `signals.py`) **and** legacy
modules importing pandas/matplotlib (`bundle.py`, `mitigation.py`, `stability.py`, `robustness.py`,
`figures.py`, `perturbation.py`, `calibration.py`, `tables.py`, `summary.py`, `discovery.py`). The
package masks this with a hand-maintained lazy `__getattr__` export map in `reporting/__init__.py`
(also in `index/__init__.py`) so importing the package does not eagerly pull pandas. This is a code
smell that papers over a missing module boundary.

### D3 — `cli.py` god module (P1)

4,157 lines, 44 `_handle_*` functions, 126 `def`s, 88 `print()` calls in one file. Hard to navigate,
test in isolation, or refactor. All command parsing, orchestration, and presentation live together.

### D4 — dual path/root systems (P1)

`storage/layout.py` (production, CWD/`--root`) and `utils/paths.py` (legacy,
`MODEL_FAILURE_LAB_ARTIFACT_ROOT`) implement parallel, independently-normalized path schemes. The
React UI uses yet another variable name, `FAILURE_LAB_ARTIFACT_ROOT`. Easy to wire a feature through
the wrong one.

### D5 — duplicated subsystems (P1)

- `runner/` (production execution) vs `runners/dispatch.py` (943-line legacy benchmark dispatch).
- `index/` (SQLite query index, production) vs `artifact_index/` (JSON manifest index, legacy/UI).

Near-identical names invite mistakes and make the "one real path" non-obvious.

### D6 — duplicated helpers (P2)

`def _require_mapping`/`_optional_string`/`_validate_json_value` appear in 6 `*contracts.py`/builder
files; `_normalize_segment` (slug helper) is reimplemented in `runner/identity.py`, `utils/paths.py`,
`storage/layout.py`, `tracking/run_id.py`. Candidates for a shared validation/util module.

### D7 — undeclared/unused dependencies (P2)

`torchvision` 0.23.0 and `sentence-transformers` 5.6.0 are installed but **not** declared in
`pyproject.toml` and **not imported** anywhere in `src/` (grep returned nothing). Likely leftover.

### D8 — oversized modules (P2)

| File | LOC |
|---|---|
| `cli.py` | 4,157 |
| `governance/portfolio.py` | 1,340 |
| `index/builder.py` | 1,116 |
| `governance/execution.py` | 1,029 |
| `runners/dispatch.py` (legacy) | 943 |
| `governance/outcomes.py` | 836 |
| `datasets/evolution.py` | 823 |
| `history.py` | 812 |

### D9 / D10 — legacy dominance & output coupling (P3)

Roughly half the package (by module count) and nearly all of `configs/` and `scripts/` serve the
"reference-only" benchmark. It inflates the surface, dependency weight, and CI time. CLI handlers
print directly rather than returning structured results, coupling logic to presentation.

## Dead code candidates

| Candidate | Evidence | Confidence |
|---|---|---|
| `torchvision`, `sentence-transformers` deps | no imports in `src/` | High |
| Legacy benchmark stack (`models/`, `mitigations/`, `perturbations/`, `evaluation/`, `data/`, `results_ui/`, `runners/`) | `docs/legacy.md` declares reference-only | Medium (still imported by tests/scripts, not dead per se) |
| `_FamilyPortfolioEvidence` and other private dataclasses | private, scope unverified | Low — not investigated per-symbol |

> No `TODO`/`FIXME`/`HACK`/`XXX` comments exist anywhere in `src/`, `scripts/`, or `tests/` (grep
> count: 0). Absence of inline debt markers does **not** imply absence of debt — the items above are
> structural.

## Circular dependencies

No circular-import failures were observed at runtime (the package imports and the CLI runs). Only 3
modules use `TYPE_CHECKING` guards. The lazy `__getattr__` in `reporting`/`index` is used to defer
heavy imports, not to break cycles. **Assumption:** no hard import cycles, but a formal cycle scan
(e.g. `pydeps`/`grimp`) was not run.

## Areas that will make future upgrades difficult (ranked)

1. **D1/D2** — until legacy deps are isolated, you cannot get a clean green test suite or safely
   import `reporting`. This blocks confident refactoring.
2. **D3** — `cli.py` must be decomposed before command behavior can be changed safely.
3. **D4/D5** — the dual path/runner/index systems must be disambiguated (ideally legacy extracted).
4. **D6/D7** — cheap cleanups that reduce surface before bigger moves.
