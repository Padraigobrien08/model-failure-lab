---
gsd_state_version: 1.0
milestone: v4.6
milestone_name: Regression Governance And Recommendation Layer
current_phase: 94
current_phase_name: Family Matching And Review/Apply CLI
current_plan: null
status: ready_to_discuss
stopped_at: Phase 93 complete
last_updated: "2026-04-04T18:20:00Z"
last_activity: 2026-04-04
progress:
  total_phases: 4
  completed_phases: 1
  total_plans: 2
  completed_plans: 2
  percent: 25
---

# State: v4.6 Regression Governance And Recommendation Layer

## Project Reference

See: [.planning/PROJECT.md](/Users/padraigobrien/model-failure-lab/.planning/PROJECT.md) (updated 2026-04-04)

**Core value:** Make structured LLM failure analysis simple, reproducible, queryable,
interpretable, reusable, and actionable from local artifacts.
**Current focus:** Turn regression enforcement into deterministic governance recommendations and
review/apply workflows.

## Current Focus

- next_action: discuss Phase `94`
- status: Phase `93` complete; next phase ready to discuss

## Current Position

Milestone: `v4.6`
Phase: `94` — ready to discuss

## Workflow State

**Current Phase:** `94`
**Current Phase Name:** `Family Matching And Review/Apply CLI`
**Total Phases:** 4
**Current Plan:** none
**Total Plans in Phase:** 0
**Status:** Ready to discuss
**Progress:** [██░░░░░░░░] 25%
**Last Activity:** 2026-04-04
**Last Activity Description:** Completed Phase `93` governance policy contract and recommendation rules

## Recent Decisions

- Use `v4.6` because this work extends the shipped `v4.5` enforcement loop rather than resetting
  product scope.
- Skip separate milestone research because the governance layer is a direct continuation of the
  current signal and dataset-evolution architecture.
- Keep governance recommendations deterministic, local, and inspectable rather than introducing a
  hosted policy service or opaque ranking model.
- Treat review/apply as an explicit user-facing workflow with dry-run surfaces before writes.

## Accumulated Context

- The product already supports execution, reporting, comparison, query, grounded insight, failure
  harvesting, regression signals, and versioned regression-pack enforcement over local artifacts.
- `v4.5` closed the enforcement loop:
  saved regressions can become future evaluation datasets automatically and reproducibly.
- The next user bottleneck is governance:
  deciding which regressions deserve action, which family should absorb them, and how to keep
  evolving packs high-signal over time.
- Phase `93` now provides the deterministic backend contract for governance recommendations,
  including policy, matched-family context, and no-write evidence preview.

## Session

**Last Date:** 2026-04-04T17:00:00Z
**Stopped At:** Phase 93 complete
**Resume File:** None

## Next Suggested Commands

```bash
$gsd-discuss-phase 94
$gsd-plan-phase 94
```

---
*State updated: 2026-04-04 after Phase 93 completion*
