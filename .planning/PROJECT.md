# Model Failure Lab

## What This Is

Model Failure Lab is an LLM failure debugging system, not a loose collection of benchmark scripts.
It lets a user run prompts against a model, classify failures, persist local JSON artifacts, and
inspect the results through a CLI-first and artifact-backed React debugger workflow. Older
benchmark-era surfaces still exist in the repo, but the product direction is now centered on the
`failure-lab` engine and the saved artifact contract it produces.

## Current State

- Latest shipped milestone: `v3.0`
- Active milestone: none
- Primary public surface:
  - [failure-lab CLI](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/cli.py)
- Secondary surfaces:
  - [React Failure Debugger](/Users/padraigobrien/model-failure-lab/frontend)
  - [legacy benchmark/reporting workflows](/Users/padraigobrien/model-failure-lab/src/model_failure_lab)
  - [repo launch surface](/Users/padraigobrien/model-failure-lab/README.md)
- Operational status:
  - `v1.8` shipped the real engine loop: `demo`, `run`, `report`, and `compare`
  - `v1.9` added bundled reasoning, hallucination, and RAG datasets plus dataset discovery
  - `v2.0` rebuilt the React debugger on top of real run/comparison artifacts and recovered denser guided inspection
  - `v2.1` completed deep-linkable detail state, exact cross-artifact drillthrough, singular route provenance, stronger active-case clarity, and explicit workflow proof
  - `67-standard-package-install-path` is complete: the installed CLI now defaults artifacts to the invocation workspace, packaged assets fail explicitly, and the package-install quickstart is verified by a temp-venv smoke
  - `68-ollama-adapter-integration` is complete: the built-in Ollama adapter now shares the normal artifact contract, the CLI exposes explicit Ollama configuration, and the end-to-end loop is proven against a localhost API stub
  - `69-artifact-compatibility-and-distribution-verification` is complete: configured external roots are honest in the debugger, installed-package artifacts hand off into debugger inspection, and Ollama-backed artifacts are proven through the same artifact-backed routes
  - local JSON artifacts under `datasets/`, `runs/`, and `reports/` remain the stable backbone
  - adapter and classifier registration seams exist, with deterministic demo, OpenAI, and Ollama support
  - `v3.0` is now shipped and archived locally; the next milestone can focus on dependency surface and broader adapter reach

## Latest Completed Milestone: v3.0 Packaged Engine And Ollama Adapter Reach

**Goal:** Make `failure-lab` installable as a normal package, add Ollama as the next adapter
family, and prove the packaged/Ollama artifact paths remain debugger-compatible.

**Delivered:**
- A normal install-first CLI path with cwd-root artifact placement, packaged-asset guidance, and a
  temp-venv installed-console-script smoke.
- A built-in Ollama adapter plus explicit CLI configuration over the same saved-artifact contract.
- Debugger compatibility proof across configured external roots, installed-package artifacts, and
  Ollama-backed artifacts through one `FAILURE_LAB_ARTIFACT_ROOT` handoff.

## Previous Milestone: v2.1 Cross-Artifact Drillthrough And Debugger Operability

**Goal:** Make the artifact-backed debugger feel operational rather than merely readable through
deep-linkable investigation state, direct cross-artifact drillthrough, and tighter detail-route
focus.

**Delivered:**
- Deep-linkable run and comparison detail state so selected section, lens, and case survive
  refresh, sharing, and route-to-route movement.
- One-click drillthrough from comparison deltas into the matching baseline or candidate run case,
  plus direct handoff into raw-backed context.
- Leaner detail surfaces with less repeated provenance chrome and clearer active-case selection
  while scanning dense evidence.

## Next Milestone Goals

- Split optional provider extras so users do not need every adapter dependency for a standard
  package install.
- Extend adapter reach beyond Ollama through the same adapter registry and artifact contract.
- Preserve the current debugger and local-artifact posture while widening distribution breadth.

## Core Value

Make structured LLM failure analysis simple, reproducible, and easy to inspect from local
artifacts.

## Requirements

### Validated

- ✓ Reproducible CivilComments benchmark pipeline with subgroup-aware artifacts, baselines,
  evaluation, and mitigation comparison — `v1.0`
- ✓ Live benchmark validation, seeded stability work, and explicit robustness closeout over the
  original research workflow — `v1.1` to `v1.4`
- ✓ React-first and then trace-first failure debugger surfaces over saved artifacts — `v1.5`,
  `v1.7`
- ✓ CLI-first failure analysis engine with canonical schemas, storage, adapters, classifiers,
  runner, reporting, comparison, and zero-config demo flow — `v1.8`
- ✓ Bundled datasets, shared taxonomy, richer single-run/comparison reporting, and an engine-first
  install-to-report path — `v1.9`
- ✓ Artifact-backed React debugger over saved runs and comparisons, with guided detail density and
  audit-clean milestone closure — `v2.0`
- ✓ Deep-linkable detail state, exact comparison-to-run drillthrough, singular provenance, shared
  active-case cues, and explicit investigation-loop proof inside the artifact-backed debugger —
  `v2.1`
- ✓ Standard package install path, install-first quickstart, explicit packaged-asset guidance, and
  installed-console-script proof for `failure-lab demo -> run -> report -> compare` — `v3.0`
- ✓ Built-in Ollama adapter, explicit CLI configuration, and debugger compatibility proof across
  packaged and Ollama-backed artifacts — `v3.0`

### Active

- User can install only the provider extras they need instead of pulling every adapter dependency.
- User can run additional local or hosted adapter families through the same adapter registry and
  artifact contract.

### Out of Scope

- Databases, remote services, queues, or heavy experiment infrastructure — local artifacts remain
  the right complexity level.
- Learned scoring or classifier models — heuristic classification is still the right starting
  point.
- Deployment, multi-user platform features, or hosted serving — this repo is still a local tool.
- Reopening benchmark-first architecture — future work should stay driven by the engine and its
  saved artifacts.

## Context

- `v1.0` to `v1.4` established and then closed a benchmark-first research loop around
  CivilComments.
- `v1.5` and `v1.7` proved there is value in a debugger-style evidence surface, but those UIs sat
  partly on older benchmark assumptions.
- `v1.8` created the real reusable engine:
  canonical schemas, local artifact layout, adapters, classifiers, runner, reporting, comparison,
  and the `failure-lab` CLI loop.
- `v1.9` made that engine useful out of the box with bundled datasets, one shared taxonomy, richer
  reporting, and an engine-first quickstart.
- `v2.0` is now complete:
  the React debugger reads real artifacts, exposes run/comparison drilldown, restores denser guided
  inspection, and passes milestone audit cleanly.
- `v2.1` is now complete:
  the debugger keeps durable detail state, drills precisely from comparisons into run evidence,
  carries one route-level provenance model, and proves the full investigative loop through route
  regressions, build, and smoke validation.
- The next product pressure is no longer debugger continuity; it is making the engine easier to
  install and broader to run while preserving the same saved-artifact contract.
- `v3.0` should solve that directly:
  package the CLI and bundled assets for a normal install path, add one new adapter family through
  Ollama, and prove that the existing artifact-backed debugger continues to work unchanged on the
  resulting runs and reports.
- `68-ollama-adapter-integration` is now complete:
  built-in Ollama execution works through the same saved-artifact contract, CLI configuration is
  explicit, and the automated suite proves the end-to-end loop through a localhost API stub.
- `69-artifact-compatibility-and-distribution-verification` is now complete:
  configured external roots are honest throughout the debugger, packaged-install artifacts hand
  off into debugger inspection, and the same debugger workflow is proven over saved Ollama
  artifacts through a localhost stub.
- `v3.0` is now archived:
  the milestone snapshots are stored under `.planning/milestones/`, the live roadmap is collapsed,
  and the next milestone should start from fresh requirements rather than reusing `v3.0` scope.
- The debugger architecture should stay stable during this milestone; widening reach matters more
  than another UI pass right now.

## Constraints

- **Product posture**: CLI and artifacts first — the engine contract must keep driving
  architecture.
- **Complexity**: Keep it simple, fast, and obvious — no new heavy infra or framework
  abstractions.
- **Storage**: Filesystem-only JSON artifacts remain canonical — no database introduction.
- **Classifier quality bar**: Heuristic and inspectable over opaque or learned scoring.
- **Distribution**: The repo should move toward a 30-second install-to-report path, so bundled
  assets and outputs must be easy to inspect by hand.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Shift the repo from benchmark-first to engine-first | A reusable failure analysis system is more valuable than extending one benchmark workflow forever | ✓ Validated in `v1.8` |
| Keep local JSON artifacts as the canonical contract | Local inspectability and reproducibility matter more than infra breadth at this stage | ✓ Validated in `v1.8` |
| Keep the CLI as the primary product surface for now | The engine needed to become real before another major UI pass | ✓ Validated in `v1.8` |
| Build dataset value and report usefulness before another major UI rebuild | The bottleneck was usefulness and shareability, not plumbing | ✓ Validated in `v1.9` |
| Rebuild future UI work on the real engine artifact contract | The CLI, datasets, and reports now define the stable product truth | ✓ Validated in `v2.0` |
| Tighten the artifact-backed investigation loop before expanding packaging or adapter breadth | The current friction is navigation and drillthrough, not missing surface area | ✓ Validated in `v2.1` |
| Default installed CLI artifacts to the caller's workspace and prove the package path with a real console-script smoke | Standard install needs predictable artifact placement and direct install evidence, not source-checkout assumptions | ✓ Validated in Phase `67` |
| Add Ollama through the existing adapter, runner, and artifact seams instead of creating a provider-specific pipeline | The value is breadth without contract churn, so provider integration should remain contained | ✓ Validated in Phase `68` |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-03 after archiving v3.0*
