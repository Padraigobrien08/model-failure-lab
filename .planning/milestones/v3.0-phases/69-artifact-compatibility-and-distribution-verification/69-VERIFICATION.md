---
phase: 69-artifact-compatibility-and-distribution-verification
verified: 2026-04-03T09:15:00Z
status: passed
score: 5/5 must-haves verified
---

# Phase 69: Artifact Compatibility And Distribution Verification Report

**Phase Goal:** Prove that packaged-install artifacts and Ollama-backed artifacts survive into the existing debugger through the configured external artifact-root contract.
**Verified:** 2026-04-03T09:15:00Z
**Status:** passed
**Re-verification:** No - initial verification

## Automated Checks

- `npm --prefix frontend run test -- --run src/app/__tests__/shell.test.tsx src/app/__tests__/runs.test.tsx src/app/__tests__/runDetail.test.tsx src/app/__tests__/comparisons.test.tsx src/app/__tests__/comparisonDetail.test.tsx`
- `npm --prefix frontend run build`
- `python3 scripts/smoke_package_install.py --verify-debugger`
- `python3 -m pytest tests/unit/test_cli_demo_compare.py -q`
- `node frontend/scripts/smoke-real-artifacts.mjs --mode ollama-stub`

## Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Configured external artifact roots stay honest across overview, inventory, and detail routes. | ✓ VERIFIED | `69-01` fixed Vite detail payloads to reuse the configured source and added configured-root regressions in the shell, run detail, and comparison detail route tests. The frontend route suite passed with `33/33` tests. |
| 2 | Installed-package artifacts can be inspected through the debugger without a repo-root sync step. | ✓ VERIFIED | `python3 scripts/smoke_package_install.py --verify-debugger` exited `0`, installed the package into a temp venv, ran the installed `failure-lab` console script, and then invoked the debugger smoke in `existing` mode against that workspace. |
| 3 | Ollama-backed artifacts can be inspected through the same debugger endpoints with no adapter-specific UI branch. | ✓ VERIFIED | `node frontend/scripts/smoke-real-artifacts.mjs --mode ollama-stub` exited `0` and verified overview, runs inventory, run detail, comparisons inventory, and comparison detail against artifacts generated through the real `ollama:<model>` CLI path. |
| 4 | Incompatible or partial artifacts remain explicit rather than silently hidden or normalized away. | ✓ VERIFIED | The installed-package smoke intentionally ends on an `incompatible_dataset` comparison and still proves debugger inspection through the same route family. Route-level incompatible states remain covered by the shell and detail regressions from `69-01`. |
| 5 | Phase 69 closes on a full compatibility matrix, not a single happy-path script. | ✓ VERIFIED | The final matrix includes configured-root frontend regressions, frontend build, installed-package debugger smoke, fast Ollama CLI regression, and the Ollama debugger smoke. All passed. |

**Score:** 5/5 truths verified

## Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `frontend/vite.config.ts` | Detail payloads reuse the configured artifact source instead of hardcoding repo-root metadata. | ✓ VERIFIED | Run-detail and comparison-detail endpoints now emit the configured source, matching overview and inventory. |
| `scripts/smoke_package_install.py` | Installed-package smoke can verify debugger inspection through the supported handoff. | ✓ VERIFIED | `--verify-debugger` invokes the frontend smoke against the generated workspace and passed. |
| `frontend/scripts/smoke-real-artifacts.mjs` | Reusable debugger smoke over both existing artifact roots and Ollama-generated artifacts. | ✓ VERIFIED | `existing` and `ollama-stub` modes both passed; the Ollama mode also asserts saved `adapter_id: ollama` metadata and a compatible comparison report. |
| `README.md` | Documents the supported debugger handoff through `FAILURE_LAB_ARTIFACT_ROOT`. | ✓ VERIFIED | The README now explains the external artifact-root seam and shows the debugger launch command. |
| `tests/unit/test_cli_demo_compare.py` | Fast Ollama regression remains green under the same localhost stub pattern. | ✓ VERIFIED | `8 passed` with the localhost stub once local socket binding was allowed. |

## Investigation Stories

1. `installed package -> saved artifacts -> configured debugger root -> route inspection`
The package smoke installs `failure-lab`, writes a fresh workspace, and hands that workspace directly into the debugger. Overview, inventory, and detail endpoints all resolve against the temp artifact root instead of a repo-root assumption.

2. `ollama:<model> -> saved runs -> compare -> debugger inspection`
The Ollama stub smoke writes baseline and candidate runs through the real CLI path, reports them, compares them, and then verifies the same debugger endpoints over those artifacts without a provider-specific route family.

3. `configured-root route contract`
The frontend route suite proves that the active source label and path survive shell, run detail, and comparison detail rendering under a configured external artifact root, and that explicit incompatible states remain visible.

## Requirements Coverage

| Requirement | Description | Status | Evidence |
| --- | --- | --- | --- |
| ADAPT-03 | Packaged-install and Ollama-produced artifacts remain debugger-compatible through the existing artifact-backed React routes. | ✓ SATISFIED | Verified by the configured-root route suite, `python3 scripts/smoke_package_install.py --verify-debugger`, `python3 -m pytest tests/unit/test_cli_demo_compare.py -q`, `node frontend/scripts/smoke-real-artifacts.mjs --mode ollama-stub`, and `npm --prefix frontend run build`. |

## Residual Risk

- The automated Ollama proof uses a localhost stub rather than a real daemon with a pulled model. That is the intended contract for automated verification in this phase and does not block milestone closeout.
- The localhost verifiers require socket permission in this environment. The successful reruns prove application behavior rather than a product defect.

## Result

Phase 69 closes `v3.0` with explicit debugger compatibility proof across configured external roots, installed-package artifacts, and Ollama-backed artifacts. The debugger contract stayed strict, the route suite stayed green, the production build succeeded, and the two new smoke paths prove distribution and adapter reach without introducing a new UI branch.

Phase 69 verification passed
