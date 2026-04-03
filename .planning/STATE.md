---
gsd_state_version: 1.0
milestone: v3.0
milestone_name: Packaged Engine And Ollama Adapter Reach
current_phase: null
current_phase_name: null
current_plan: null
status: milestone_complete
stopped_at: Archived v3.0 milestone
last_updated: "2026-04-03T09:30:00Z"
last_activity: 2026-04-03
progress:
  total_phases: 3
  completed_phases: 3
  total_plans: 6
  completed_plans: 6
  percent: 100
---

# State: v3.0 Packaged Engine And Ollama Adapter Reach

## Project Reference

See: [.planning/PROJECT.md](/Users/padraigobrien/model-failure-lab/.planning/PROJECT.md) (updated 2026-04-03)

**Core value:** Make structured LLM failure analysis simple, reproducible, and easy to inspect from local artifacts.
**Current focus:** Milestone archived; ready to define the next milestone

## Current Focus

- next_action: start the next milestone
- status: `v3.0` is archived locally and no active phase is in progress

## Current Position

Milestone: `v3.0` — archived
Phase: none active

## Workflow State

**Current Phase:** none
**Current Phase Name:** none
**Total Phases:** 3
**Current Plan:** none
**Total Plans in Phase:** 0
**Status:** Milestone complete
**Progress:** [██████████] 100%
**Last Activity:** 2026-04-03
**Last Activity Description:** v3.0 milestone archived locally and tagged

## Recent Decisions

- Default `failure-lab` artifact placement now follows the invocation current working directory unless `--root` is supplied explicitly.
- Phase 69 is now complete: configured external roots, installed-package artifacts, and Ollama-backed artifacts are all proven through the existing debugger workflow.
- The next milestone should start from fresh requirements rather than carrying forward the archived `v3.0` requirements file.

## Accumulated Context

- The engine backbone is now real:
  canonical schemas, local artifact storage, adapters, classifiers, runner, reporting,
  comparison, and the `failure-lab` CLI.

- The repo now ships bundled reasoning, hallucination, and RAG datasets by canonical ID.
- Bundled dataset discovery is visible at:
  `failure-lab datasets list`

- `v2.0` shipped the real artifact-backed React debugger for saved runs and comparisons.
- `v2.1` completed the debugger operability pass:
  1. run and comparison detail routes keep durable deep-linkable investigation state
  2. comparison cases drill directly into baseline and candidate run evidence
  3. route provenance is singular and active-case selection is visibly recoverable
  4. the investigation loop is explicitly proven through route regressions, build, smoke, and `66-VERIFICATION.md`
- Local JSON artifacts under `datasets/`, `runs/`, and `reports/` remain the canonical product
  contract.

- `67-01` removed source-layout assumptions from artifact placement:
  the installed CLI now writes into the current working directory by default and keeps `--root` as
  the explicit override.

- `67-01` also made bundled demo/dataset asset failures package-aware and rewrote the README around
  `python3 -m pip install .` plus the installed `failure-lab demo -> run -> report -> compare`
  flow.

- `67-02` added the missing install proof:
  a temp-environment smoke now installs the package, runs the installed `failure-lab` console
  script end-to-end, and verifies `datasets/`, `runs/`, and `reports/` from a scratch working
  directory.

- `67-02` also locked the source-level quickstart regression and README wording to that same
  package-install artifact loop, including the expected incompatible comparison artifact at the end
  of the quickstart.

- `68-01` added the built-in `ollama` adapter:
  non-streaming HTTP execution, normalized usage mapping, and saved-artifact compatibility coverage
  for run, report, and comparison paths.

- `68-02` exposed explicit Ollama CLI configuration:
  `ollama:<model>`, `--ollama-host`, `--system-prompt`, and JSON `--model-option`, plus a
  localhost stub proving the full `run -> report -> compare` loop.

- `69-01` made the debugger honest about configured external artifact roots:
  detail payloads now preserve configured source metadata and route-level regressions protect that
  contract across shell, run detail, and comparison detail.

- `69-02` closed the compatibility loop:
  installed-package smoke now verifies debugger inspection, the frontend smoke can inspect existing
  artifact roots or generate Ollama-stub artifacts, and the README documents the
  `FAILURE_LAB_ARTIFACT_ROOT` handoff.

- `v3.0` is now archived:
  roadmap and requirements snapshots are stored under `.planning/milestones/`, the repo is tagged
  locally, and the live planning files are reset for the next milestone.

- `v3.0` now targets that next gap directly:
  1. package `failure-lab` for a normal install path without editable-checkout assumptions
  2. add Ollama as the next real adapter family through the current adapter and artifact seams
  3. prove packaged and Ollama-produced artifacts still flow through the current debugger without a new UI branch
- The debugger architecture is intentionally stable during this milestone; widening distribution and
  adapter reach is the priority.

## Session

**Last Date:** 2026-04-03T09:30:00Z
**Stopped At:** Archived v3.0 milestone
**Resume File:** None

## Next Suggested Commands

```bash
$gsd-new-milestone
$gsd-progress
```

---
*State updated: 2026-04-03 after archiving v3.0*
