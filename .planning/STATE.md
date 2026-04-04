---
gsd_state_version: 1.0
milestone: v4.4
milestone_name: Regression Detection And Signal Layer
current_phase: null
current_phase_name: null
current_plan: null
status: milestone_completed
stopped_at: Milestone archived
last_updated: "2026-04-04T14:34:26Z"
last_activity: 2026-04-04
progress:
  total_phases: 4
  completed_phases: 4
  total_plans: 4
  completed_plans: 4
  percent: 100
---

# State: v4.4 Regression Detection And Signal Layer

## Project Reference

See: [.planning/PROJECT.md](/Users/padraigobrien/model-failure-lab/.planning/PROJECT.md) (updated 2026-04-04)

**Core value:** Make behavior changes explicit, deterministic, and actionable from local
artifacts.
**Current focus:** Await the next milestone definition.

## Current Focus

- next_action: define the next milestone
- status: `v4.4` archived locally

## Current Position

Milestone: `v4.4`
Phase: none

## Workflow State

**Current Phase:** none
**Current Phase Name:** none
**Total Phases:** 4
**Current Plan:** none
**Total Plans in Phase:** 0
**Status:** Milestone completed
**Progress:** [██████████] 100%
**Last Activity:** 2026-04-04
**Last Activity Description:** Archived milestone `v4.4`

## Recent Decisions

- Use `v4.4` as the next version because this milestone extends the shipped `v4.3` artifact and
  harvesting stack with a new signal layer rather than resetting product scope.
- Keep signal computation deterministic and quantitative first; LLM interpretation remains an
  optional extension through the existing insight layer.
- Persist signals directly inside comparison artifacts so they remain artifact-native, reproducible,
  and queryable.
- Reuse the current CLI, query, and debugger surfaces instead of introducing a separate alerting
  service or provider-specific UI branch.
- Mirror persisted signal fields into the SQLite query index, with a compatibility fallback that
  derives signals from older comparison artifacts when the signal block is absent.
- Keep the CLI alert surface directional-only so neutral comparisons remain queryable without
  producing noisy automated alerts.
- Keep debugger signal views quantitative first:
  verdict, severity, top drivers, then drillthrough into existing evidence routes.
- Treat `/analysis?mode=signals` as a ranking view rather than an insight or harvesting surface,
  so it does not show heuristic summaries or draft-export actions.
- Treat repeated comparison generation over the same saved runs as deterministic:
  persisted signal payloads must remain stable and index rebuilds must not drift the listing layer.

## Accumulated Context

- The product already supports execution, reporting, comparison, cross-run query, grounded
  insight, failure harvesting, dataset curation, and replayable evaluation loops.
- `v4.3` closed the reuse loop:
  users can now turn saved failures into curated datasets and rerun them through the standard
  engine.
- The next user bottleneck is not “can I inspect or reuse failures?” It is “can the system tell me
  what materially changed between runs and how severe it is without manual digging?”
- `v4.4` addresses that directly through deterministic comparison scoring, persisted signal blocks,
  CLI surfacing, and debugger severity views.

## Session

**Last Date:** 2026-04-04T14:04:56Z
**Stopped At:** Milestone archived
**Resume File:** None

## Next Suggested Commands

```bash
$gsd-new-milestone
```

---
*State updated: 2026-04-04 after v4.4 archive*
