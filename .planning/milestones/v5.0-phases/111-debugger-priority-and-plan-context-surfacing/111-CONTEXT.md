# Phase 111: Debugger Priority And Plan Context Surfacing - Context

**Gathered:** 2026-04-05
**Status:** Completed

<domain>
## Phase Boundary

Surface portfolio priority and saved-plan context on existing debugger routes without adding a new
dashboard. This phase covers query-bridge payload extensions, typed frontend parsing, and compact
route-local UI in the existing dataset automation panel.

</domain>

<decisions>
## Implementation Decisions

- Reuse the existing dataset-versions bridge payload as the family-context entrypoint for priority
  and saved-plan data instead of creating a parallel artifact endpoint.
- Keep the UI route-local by extending
  [`SignalDatasetAutomationPanel`](/Users/padraigobrien/model-failure-lab/frontend/src/components/datasets/SignalDatasetAutomationPanel.tsx),
  which already concentrates lifecycle, history, and cluster context.
- Enable family-context loading on the existing analysis and comparison routes only when a matched
  family already exists, avoiding unnecessary requests for pure suggestion-only comparisons.

</decisions>

<code_context>
## Existing Code Insights

- [`scripts/query_bridge.py`](/Users/padraigobrien/model-failure-lab/scripts/query_bridge.py)
  already enriches dataset-version responses with history and lifecycle actions, making it the
  natural seam for portfolio context.
- The frontend artifact loaders already parse optional governance and lifecycle payloads, so adding
  optional portfolio types keeps the bridge backward compatible.
- The current automation panel already shows the evidence users need to drill deeper, which means
  portfolio context only needs to explain rank and saved-plan inclusion rather than recreate the
  underlying evidence surfaces.

</code_context>

<specifics>
## Phase-Specific Gaps To Close

- Add family-scoped portfolio item and saved-plan payloads to the dataset-versions bridge output.
- Add frontend types/loaders for the new optional payload shape.
- Surface compact priority and plan cards in the automation panel and enable them on the analysis
  route when an existing family is present.

</specifics>

<deferred>
## Deferred Ideas

- End-to-end workflow proof and final milestone closeout belong to Phase 112.

</deferred>
