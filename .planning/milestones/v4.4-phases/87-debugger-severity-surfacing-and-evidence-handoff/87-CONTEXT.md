# Phase 87: Debugger Severity Surfacing And Evidence Handoff - Context

**Gathered:** 2026-04-04
**Status:** Completed

<domain>
## Phase Boundary

Surface persisted comparison signals inside the existing debugger so users can identify direction,
severity, and likely drivers before opening dense evidence views. This phase only covers debugger
and query-backed UI surfaces; milestone-wide workflow proof stays in Phase 88.

</domain>

<decisions>
## Implementation Decisions

### Comparison Surfaces
- Show persisted signal verdict, severity, and top drivers directly in the comparisons inventory
  and comparison detail framing section.
- Keep the comparison detail signal readout quantitative first, with signal buttons handing off
  into existing transition evidence selection rather than inventing a new drillthrough surface.

### Analysis Surface
- Extend `/analysis` with a dedicated `signals` mode backed by the existing query bridge.
- Keep signal mode intentionally different from case/delta/aggregate analysis:
  no insight panel and no draft export, because the user is ranking comparisons rather than
  summarizing row sets or harvesting cases.

### Compatibility Handling
- Preserve neutral defaults when older fixtures or artifacts lack signal blocks.
- Normalize raw signal payloads from the bridge and dev server at the type boundary so the React
  routes only deal with one client-side signal shape.

</decisions>

<code_context>
## Existing Code Insights

- [`frontend/src/app/routes/ComparisonsPage.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/ComparisonsPage.tsx)
  already centralizes comparison inventory ordering, so severity-first sorting belonged there.
- [`frontend/src/app/routes/ComparisonDetailPage.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/ComparisonDetailPage.tsx)
  already owned deep-link state for transition evidence, which made top-driver handoff a route-state
  update rather than a new routing concept.
- [`frontend/src/app/routes/AnalysisPage.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/routes/AnalysisPage.tsx)
  already owned query-backed modes and filters, so adding `signals` could reuse the same URL-backed
  filter contract and return-state handling.

</code_context>

<deferred>
## Deferred Ideas

- Threshold automation and milestone-level “what changed?” proof stay in Phase 88.
- Any future alert dashboard or dataset seeding from signals stays outside `v4.4`.

</deferred>
