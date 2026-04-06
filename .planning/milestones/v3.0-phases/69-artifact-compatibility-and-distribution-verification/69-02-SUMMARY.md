---
phase: 69-artifact-compatibility-and-distribution-verification
plan: 02
subsystem: integration
tags: [debugger, packaged-install, ollama, smoke, README]
requires:
  - phase: 69-01
    provides: honest configured artifact-root metadata across debugger routes
provides:
  - installed-package smoke that verifies debugger inspection through the supported artifact-root seam
  - frontend smoke modes for existing artifact roots and stubbed Ollama artifact generation
  - documented `FAILURE_LAB_ARTIFACT_ROOT` handoff for the React debugger
affects:
  - milestone closeout
  - debugger smoke
  - package smoke
  - README
tech-stack:
  added: [node http stub, Vite middleware inspection]
  patterns:
    - packaged and Ollama artifacts are proven through the same configured-root debugger contract
    - debugger smoke can inspect an existing artifact root instead of always generating fresh demo artifacts
key-files:
  created: []
  modified:
    - scripts/smoke_package_install.py
    - frontend/scripts/smoke-real-artifacts.mjs
    - README.md
    - frontend/src/app/__tests__/shell.test.tsx
    - tests/unit/test_cli_demo_compare.py
key-decisions:
  - "Keep the debugger handoff server-configured and external-root based instead of adding an in-app artifact picker."
  - "Close the milestone on automated artifact compatibility proof, not only CLI-level success."
patterns-established:
  - "Packaged-install proof can hand a saved workspace directly into debugger inspection through `FAILURE_LAB_ARTIFACT_ROOT`."
  - "Ollama debugger proof should verify both endpoint compatibility and the saved artifact metadata that proves the adapter path was real."
requirements-completed: [ADAPT-03]
duration: 29 min
completed: 2026-04-03
---

# Phase 69 Plan 02: Distribution Compatibility Proof Summary

**Packaged-install and Ollama artifact paths now reach the debugger through one proven contract**

## Performance

- **Duration:** 29 min
- **Started:** 2026-04-03T08:46:00Z
- **Completed:** 2026-04-03T09:15:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Extended `scripts/smoke_package_install.py` with `--verify-debugger`, so the installed-package smoke now hands its temp workspace into the debugger instead of stopping at raw artifact existence.
- Reworked `frontend/scripts/smoke-real-artifacts.mjs` into a reusable verifier with `demo`, `existing`, and `ollama-stub` modes.
- Added an Ollama-stub debugger proof that generates same-dataset saved artifacts through the real `ollama:<model>` CLI path, then verifies overview, inventory, and detail endpoints against those artifacts.
- Documented the supported debugger handoff in `README.md` through `FAILURE_LAB_ARTIFACT_ROOT`.
- Closed the phase with the full compatibility matrix: frontend route regressions, frontend build, installed-package debugger smoke, fast Ollama CLI regression, and the Ollama debugger smoke.

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend the installed-package smoke through debugger inspection and document the handoff** - `580819e` (feat)
2. **Task 2: Add an Ollama-backed debugger smoke and close the phase with the full compatibility matrix** - `a1bfa28` (test)

## Files Created/Modified

- `scripts/smoke_package_install.py` - `--verify-debugger` support and debugger handoff into the frontend smoke harness.
- `frontend/scripts/smoke-real-artifacts.mjs` - reusable `existing` and `ollama-stub` modes plus adapter-specific Ollama artifact assertions.
- `README.md` - explicit React debugger handoff through `FAILURE_LAB_ARTIFACT_ROOT`.
- `frontend/src/app/__tests__/shell.test.tsx` - explicit `ArtifactOverview` fixture typing so the configured-root shell regression also survives TypeScript build verification.
- `tests/unit/test_cli_demo_compare.py` - shared Ollama prompt settings in the localhost stub regression.

## Decisions Made

- Reused the existing external artifact-root seam all the way through packaged-install and Ollama proof, rather than adding a second inspection flow.
- Kept the debugger contract strict: the new smoke asserts honest source paths and real Ollama adapter metadata instead of normalizing drift in the frontend.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] TypeScript build exposed a fixture typing hole in the configured-root shell regression**
- **Found during:** final frontend build verification
- **Issue:** `shell.test.tsx` spread a union-typed `overview` fixture, which allowed `status` to become optional at the type level and broke the production TypeScript build.
- **Fix:** pinned the configured shell fixture to `ArtifactOverview` explicitly.
- **Files modified:** `frontend/src/app/__tests__/shell.test.tsx`
- **Verification:** `npm --prefix frontend run test -- --run src/app/__tests__/shell.test.tsx src/app/__tests__/runs.test.tsx src/app/__tests__/runDetail.test.tsx src/app/__tests__/comparisons.test.tsx src/app/__tests__/comparisonDetail.test.tsx`; `npm --prefix frontend run build`
- **Committed in:** `580819e`

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Improved verification integrity without changing the product contract.

## Issues Encountered

- The Ollama localhost stub verifiers cannot bind sockets inside this sandbox, so `python3 -m pytest tests/unit/test_cli_demo_compare.py -q` and `node frontend/scripts/smoke-real-artifacts.mjs --mode ollama-stub` were rerun with local socket permission.

## User Setup Required

None. Manual real-daemon Ollama verification is still optional follow-up, not a blocker for this phase.

## Next Phase Readiness

- Phase 69 is complete and `v3.0` is ready for milestone closeout.
- The debugger contract now has automated proof across configured external roots, installed-package artifacts, and Ollama-backed artifacts.

## Self-Check: PASSED

- Found `.planning/phases/69-artifact-compatibility-and-distribution-verification/69-02-SUMMARY.md`
- Found commit `580819e`
- Found commit `a1bfa28`
