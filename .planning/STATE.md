---
gsd_state_version: 1.0
milestone: v4.4
milestone_name: Regression Detection And Signal Layer
current_phase: 88
current_phase_name: Signal Stability And Workflow Verification
current_plan: null
status: ready_to_plan
stopped_at: Phase 87 complete
last_updated: "2026-04-04T14:30:15Z"
last_activity: 2026-04-04
progress:
  total_phases: 4
  completed_phases: 3
  total_plans: 3
  completed_plans: 3
  percent: 75
---

# State: v4.4 Regression Detection And Signal Layer

## Project Reference

See: [.planning/PROJECT.md](/Users/padraigobrien/model-failure-lab/.planning/PROJECT.md) (updated 2026-04-04)

**Core value:** Make behavior changes explicit, deterministic, and actionable from local
artifacts.
**Current focus:** Prove the signal layer is stable and workflow-complete across persisted
artifacts, CLI surfaces, and debugger severity views.

## Current Focus

- next_action: plan Phase `88`
- status: Phase 87 complete; final workflow verification is next

## Current Position

Milestone: `v4.4`
Phase: `88` — ready to plan

## Workflow State

**Current Phase:** `88`
**Current Phase Name:** `Signal Stability And Workflow Verification`
**Total Phases:** 4
**Current Plan:** none
**Total Plans in Phase:** 0
**Status:** Ready to plan
**Progress:** [████████░░] 75%
**Last Activity:** 2026-04-04
**Last Activity Description:** Completed Phase 87 debugger severity surfacing and evidence handoff

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
**Stopped At:** Phase 87 complete
**Resume File:** None

## Next Suggested Commands

```bash
$gsd-plan-phase 88
$gsd-execute-phase 88
```

---
*State updated: 2026-04-04 after Phase 87 completion*
