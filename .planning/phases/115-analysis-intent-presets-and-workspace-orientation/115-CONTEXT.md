# Phase 115: Analysis Intent Presets And Workspace Orientation - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Make `/analysis` read like an operator workflow instead of a raw filter wall, and make the shared
shell treat the active artifact workspace as first-class context. This phase covers URL-backed
analysis presets, lightweight signal-query enrichment needed to support them, and stronger shell
orientation around the current artifact root.

</domain>

<decisions>
## Implementation Decisions

### Intent Presets
- Add operator presets directly to the existing `/analysis` route rather than creating a parallel
  queue or dashboard.
- Keep presets URL-backed so they remain shareable and compose with the existing dataset/model/time
  filters.

### Preset Data Contract
- Reuse the signal query mode and enrich those rows with portfolio priority and saved-plan context
  from the query bridge.
- Filter preset views client-side after the raw signal query resolves so the underlying query
  contract stays simple and explainable.

### Workspace Orientation
- Strengthen the shared shell with explicit workspace status, source path, and trust cues rather
  than treating the active artifact root as passive metadata.
- Add orientation on non-detail routes and a skip link without disturbing the existing route-local
  debugger structure.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- [`AnalysisPage.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/AnalysisPage.tsx)
  already owns query search params and can introduce presets without adding new route plumbing.
- [`TraceShell.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/components/layout/TraceShell.tsx)
  already centralizes route framing and artifact-root surfacing, making it the right place for
  shared workspace orientation.
- [`query_bridge.py`](/Users/padraigobrien/model-failure-lab/scripts/query_bridge.py) already
  enriches comparison inventory rows with governance and portfolio data, so signal-query enrichment
  can follow the same pattern.

### Established Patterns
- The UI already uses URL-backed route state for detail selection and triage views.
- The debugger favors route-local artifact context over hidden browser state or server sessions.

### Integration Points
- Signal-query rows flow from [`query_bridge.py`](/Users/padraigobrien/model-failure-lab/scripts/query_bridge.py)
  through [`load.ts`](/Users/padraigobrien/model-failure-lab/frontend/src/lib/artifacts/load.ts)
  into [`AnalysisPage.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/AnalysisPage.tsx).
- Analysis route regressions live in
  [`analysis.test.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/__tests__/analysis.test.tsx).

</code_context>

<specifics>
## Specific Ideas

- Add presets for actionable regressions, critical queue, merge candidates, and plan-backed items.
- Show active preset focus and visible-row counts so users understand when the page is applying a
  workflow view on top of the raw query response.
- Surface workspace source, status, and trust cues consistently in the shell so users know which
  artifact root they are interrogating.

</specifics>

<deferred>
## Deferred Ideas

- Phase 116 will absorb router-warning cleanup, duplicate-key cleanup, and end-to-end verification.
- A future dashboard or multi-workspace switcher remains out of scope for `v5.1`.

</deferred>
