# Roadmap: Model Failure Lab

## Archived Milestones

- [x] [v1.0 MVP](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.0-ROADMAP.md) - shipped 2026-03-20; 10 phases, 29 plans, 23/23 requirements complete.
- [x] [v1.1 Live Benchmark Validation And Research Packaging](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.1-ROADMAP.md) - shipped 2026-03-20; 6 phases, 15 plans, 10/10 requirements complete.
- [x] [v1.2 Seed Stability And Reweighting Validation](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.2-ROADMAP.md) - shipped 2026-03-22; 4 phases, 9 plans, 7/7 requirements complete.
- [x] [v1.3 Artifact-Driven Results UI And Robustness Consolidation](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.3-ROADMAP.md) - shipped 2026-03-24; 4 phases, 9 plans, 8/8 requirements complete.
- [x] [v1.4 Final Robustness Attempt Before Expansion](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.4-ROADMAP.md) - shipped 2026-03-25; 3 phases, 6 plans, 6/6 requirements complete.
- [x] [v1.5 React Failure Debugger UI](/Users/padraigobrien/model-failure-lab/.planning/milestones/v1.5-ROADMAP.md) - shipped 2026-03-25; 4 phases, 8 plans, 8/8 requirements complete.

## Current Milestone: v1.7 Trace-First Failure Debugger Rebuild

**Goal:** Rebuild the Failure Debugger frontend as a route-driven, trace-first interface where
each screen answers one question in the chain `Verdict -> Lane -> Method -> Run -> Artifact`
without dashboard patterns, visual fluff, or scope ambiguity.

## Phases

- [x] **Phase 36: Trace Shell And Route Scaffold** - Create the React app shell, sticky header, route skeleton, scope context, and placeholder trace routes. (completed 2026-03-26)
- [ ] **Phase 37: Summary Entry Route** - Build `/` as the compact answer to “Where should I look?” using final verdict plus robustness and calibration entry panels.
- [ ] **Phase 38: Lane Table Workspace** - Build `/lane/:laneId` as a table-first lane view with method comparison, grouped runs, and a reactive inspector.
- [ ] **Phase 39: Method Drilldown Route** - Build `/lane/:laneId/:methodId` as the focused answer to “Why is this method judged this way?”
- [ ] **Phase 40: Run Detail Route** - Build `/run/:runId` as the focused answer to “What happened in this run?”
- [ ] **Phase 41: Raw Debug And Shared Inspector** - Build `/debug/raw/:entityId` and harden the shared inspector so provenance and evidence never disappear.
- [ ] **Phase 42: Scope Filtering And URL State** - Integrate official/exploratory scope into filtering, labels, and `?scope=` URL persistence across the app.
- [ ] **Phase 43: Interaction Audit And Tightening** - Audit the rebuilt UI for dashboard drift, inspector failures, noisy spacing, broken drill-downs, and inconsistent readability.

## Phase Details

### Phase 36: Trace Shell And Route Scaffold
**Goal**: Create the minimal React shell and route structure for the trace-first debugger.
**Depends on**: `v1.5` shipped React surface and existing repo frontend tooling
**Requirements**: SHELL-01
**Success Criteria** (what must be TRUE):
1. User can navigate to `/`, `/lane/:laneId`, `/lane/:laneId/:methodId`, `/run/:runId`, and `/debug/raw/:entityId`.
2. The shell has a sticky header and a main content area only; no visible inspector column or dashboard chrome is present yet.
3. Scope mode is available through one shared React context from the start.
**Plans**: 2 plans
Plans:
- [x] `36-01-PLAN.md` - Reset the route contract, shared scope context, and minimal sticky-header shell. (completed 2026-03-26)
- [x] `36-02-PLAN.md` - Add placeholder route pages, scope-preserving route links, and scaffold regression coverage. (completed 2026-03-26)

### Phase 37: Summary Entry Route
**Goal**: Make the default route answer “Where should I look?” in one compact screen.
**Depends on**: Phase 36
**Requirements**: SUM-01
**Success Criteria** (what must be TRUE):
1. User lands on `/` and sees the final verdict immediately.
2. User can scan compact `Robustness` and `Calibration` panels with short summaries, status, method previews, and key metrics.
3. User can drill from a lane panel or method row into the next route without wading through overview/dashboard filler.

### Phase 38: Lane Table Workspace
**Goal**: Make one lane readable as a comparison workspace instead of a summary page.
**Depends on**: Phase 37
**Requirements**: LANE-01
**Success Criteria** (what must be TRUE):
1. User can open `/lane/:laneId` and read a table-first method comparison with the correct lane-specific columns.
2. User can expand a method to see grouped runs without leaving the lane route.
3. Selecting a row updates an inspector with evidence links and provenance preview in the same workspace.

### Phase 39: Method Drilldown Route
**Goal**: Make one method explainable without duplicating the whole lane workspace.
**Depends on**: Phase 38
**Requirements**: METHOD-01
**Success Criteria** (what must be TRUE):
1. User can open `/lane/:laneId/:methodId` and see method status, metrics, and run rows clearly.
2. User can read a structured explanation of what improved, what regressed, and why the method has its current status.
3. User can inspect lineage and choose a run without losing method-level context.

### Phase 40: Run Detail Route
**Goal**: Make a run readable as a single trace artifact rather than a comparison surface.
**Depends on**: Phase 39
**Requirements**: RUN-01
**Success Criteria** (what must be TRUE):
1. User can open `/run/:runId` and understand the run status, seed, method, lane, and key metrics quickly.
2. User can inspect lineage and artifact summaries without unrelated runs appearing on the page.
3. User can navigate back to the parent method or deeper into evidence from the run route.

### Phase 41: Raw Debug And Shared Inspector
**Goal**: Make the raw evidence/debug path explicit and ensure the shared inspector is always useful.
**Depends on**: Phase 40
**Requirements**: RAW-01, INSPECT-01
**Success Criteria** (what must be TRUE):
1. User can open `/debug/raw/:entityId` and inspect raw JSON, manifest entity, and metadata in monospaced tabs.
2. The shared inspector updates from selections across pages and never collapses into an empty decorative region.
3. The inspector exposes evidence links, provenance fields, scope, and an `Open raw` action consistently.

### Phase 42: Scope Filtering And URL State
**Goal**: Make official-versus-exploratory mode explicit, filterable, and persistent.
**Depends on**: Phase 41
**Requirements**: SCOPE-01
**Success Criteria** (what must be TRUE):
1. User can toggle between `official only` and `include exploratory`.
2. The active scope persists in both global state and `?scope=` query state.
3. Methods and runs filter correctly and exploratory entries remain clearly marked everywhere they appear.

### Phase 43: Interaction Audit And Tightening
**Goal**: Remove dashboard drift and tighten the rebuilt UI into a readable debugger surface.
**Depends on**: Phase 42
**Requirements**: FLOW-01
**Success Criteria** (what must be TRUE):
1. The UI no longer exhibits accidental dashboard/card-grid patterns.
2. Table readability, spacing, and drill-down flows are consistent across all rebuilt routes.
3. The inspector, navigation, and route hierarchy feel like a trace-first debugger rather than an analytics summary page.

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 36. Trace Shell And Route Scaffold | 2/2 | Complete   | 2026-03-26 |
| 37. Summary Entry Route | 0/0 | Not started | - |
| 38. Lane Table Workspace | 0/0 | Not started | - |
| 39. Method Drilldown Route | 0/0 | Not started | - |
| 40. Run Detail Route | 0/0 | Not started | - |
| 41. Raw Debug And Shared Inspector | 0/0 | Not started | - |
| 42. Scope Filtering And URL State | 0/0 | Not started | - |
| 43. Interaction Audit And Tightening | 0/0 | Not started | - |

---
*Last updated: 2026-03-26 after completing 36-02*
