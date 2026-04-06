---
phase: 69-artifact-compatibility-and-distribution-verification
plan: 01
subsystem: frontend
tags: [debugger, artifact-root, vite, react-router, vitest]
requires: []
provides:
  - honest configured artifact-source metadata across overview, inventory, and detail routes
  - active artifact-root copy on shell and detail loading states
  - regression coverage for configured external artifact roots on run and comparison detail routes
affects:
  - 69-02
  - debugger shell
  - run detail
  - comparison detail
tech-stack:
  added: []
  patterns:
    - configured artifact-root metadata flows through the same adapter-generic route payloads as repo-root artifacts
    - route and shell copy describe the active artifact root instead of assuming a source checkout
key-files:
  created: []
  modified:
    - frontend/vite.config.ts
    - frontend/src/components/layout/ArtifactStatePanel.tsx
    - frontend/src/app/routes/RunsPage.tsx
    - frontend/src/app/routes/RunDetailPage.tsx
    - frontend/src/app/routes/ComparisonDetailPage.tsx
    - frontend/src/app/__tests__/shell.test.tsx
    - frontend/src/app/__tests__/runDetail.test.tsx
    - frontend/src/app/__tests__/comparisonDetail.test.tsx
key-decisions:
  - "Keep the debugger contract strict and adapter-generic by fixing source metadata at the serving layer rather than teaching the UI to normalize mismatched payloads."
  - "Treat configured external artifact roots as first-class debugger inputs and prove them through the existing shell and detail routes."
patterns-established:
  - "Artifact source labels and paths should round-trip from the server payload into route provenance and artifact context without repo-root assumptions."
  - "Configured-root coverage belongs in the route suite so future artifact-root regressions fail before milestone-close smoke runs."
requirements-completed: []
duration: 10 min
completed: 2026-04-03
---

# Phase 69 Plan 01: Configured Artifact-Root Contract Summary

**Debugger source metadata now stays honest under configured external artifact roots**

## Performance

- **Duration:** 10 min
- **Started:** 2026-04-03T11:05:00Z
- **Completed:** 2026-04-03T11:15:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Replaced the remaining hardcoded repo-root source payloads in the Vite run-detail and comparison-detail endpoints with the resolved configured artifact source.
- Removed `default local artifact root` wording from shell and detail loading states so the UI describes the active artifact root instead of implying a source checkout.
- Added shell coverage for a configured external artifact source in the top-level debugger state.
- Added run-detail and comparison-detail regressions that prove configured external source labels and paths survive into route provenance and artifact context.

## Task Commits

Each task was committed atomically:

1. **Task 1: Remove remaining repo-root assumptions from debugger detail payloads and route source messaging** - `a7c37b0` (fix)
2. **Task 2: Add configured-root and incompatibility regressions across the detail routes** - `f70ad3e` (test)

## Files Created/Modified

- `frontend/vite.config.ts` - run-detail and comparison-detail payloads now reuse the resolved configured artifact source metadata.
- `frontend/src/components/layout/ArtifactStatePanel.tsx` - loading copy now refers to the active artifact root.
- `frontend/src/app/routes/RunsPage.tsx` - inventory loading copy now reflects the active artifact root.
- `frontend/src/app/routes/RunDetailPage.tsx` - run-detail loading copy now names the active artifact source.
- `frontend/src/app/routes/ComparisonDetailPage.tsx` - comparison-detail loading copy now names the active artifact source.
- `frontend/src/app/__tests__/shell.test.tsx` - configured external artifact-source coverage for the shell contract.
- `frontend/src/app/__tests__/runDetail.test.tsx` - configured source metadata regression for run detail.
- `frontend/src/app/__tests__/comparisonDetail.test.tsx` - configured source metadata regression for comparison detail.

## Decisions Made

- Fixed the contract where it originates: the server payload now carries the configured artifact root through detail routes instead of leaving the UI to compensate.
- Kept the route behavior adapter-generic and explicit; this pass did not add provider-specific branches or special-case UI for external roots.

## Deviations from Plan

None.

## Issues Encountered

- A stale `.git/index.lock` briefly interrupted the first commit attempt, but the lock cleared without manual cleanup and did not affect the final code state.

## User Setup Required

None.

## Next Phase Readiness

- The debugger-serving layer and route suite are now honest about configured external artifact roots, so `69-02` can focus on packaged-install and Ollama debugger proof instead of baseline contract cleanup.
- No extra frontend abstraction is needed before the smoke harness integration.

## Self-Check: PASSED

- Found `.planning/phases/69-artifact-compatibility-and-distribution-verification/69-01-SUMMARY.md`
- Found commit `a7c37b0`
- Found commit `f70ad3e`
