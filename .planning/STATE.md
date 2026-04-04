---
gsd_state_version: 1.0
milestone: v4.4
milestone_name: Regression Detection And Signal Layer
current_phase: 85
current_phase_name: Comparison Signal Contract And Artifact Persistence
current_plan: null
status: ready_to_discuss
stopped_at: Milestone defined
last_updated: "2026-04-04T13:40:54Z"
last_activity: 2026-04-04
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# State: v4.4 Regression Detection And Signal Layer

## Project Reference

See: [.planning/PROJECT.md](/Users/padraigobrien/model-failure-lab/.planning/PROJECT.md) (updated 2026-04-04)

**Core value:** Make behavior changes explicit, deterministic, and actionable from local
artifacts.
**Current focus:** Define and ship the persisted comparison signal contract before opening new UI
surfaces.

## Current Focus

- next_action: discuss Phase `85`
- status: milestone initialized; requirements and roadmap are ready

## Current Position

Milestone: `v4.4`
Phase: `85` — ready to discuss

## Workflow State

**Current Phase:** `85`
**Current Phase Name:** `Comparison Signal Contract And Artifact Persistence`
**Total Phases:** 4
**Current Plan:** none
**Total Plans in Phase:** 0
**Status:** Ready to discuss
**Progress:** [░░░░░░░░░░] 0%
**Last Activity:** 2026-04-04
**Last Activity Description:** Started milestone v4.4 and defined requirements and roadmap

## Recent Decisions

- Use `v4.4` as the next version because this milestone extends the shipped `v4.3` artifact and
  harvesting stack with a new signal layer rather than resetting product scope.
- Keep signal computation deterministic and quantitative first; LLM interpretation remains an
  optional extension through the existing insight layer.
- Persist signals directly inside comparison artifacts so they remain artifact-native, reproducible,
  and queryable.
- Reuse the current CLI, query, and debugger surfaces instead of introducing a separate alerting
  service or provider-specific UI branch.

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

**Last Date:** 2026-04-04T13:40:54Z
**Stopped At:** Milestone defined
**Resume File:** None

## Next Suggested Commands

```bash
$gsd-discuss-phase 85
$gsd-plan-phase 85
```

---
*State updated: 2026-04-04 for milestone v4.4 initialization*
