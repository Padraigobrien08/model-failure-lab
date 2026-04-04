# Phase 102: Cluster Summaries And CLI Surfaces - Context

**Gathered:** 2026-04-04  
**Status:** Completed

## Phase Boundary

Take the persisted cluster contract and expose it as a usable inspection surface in the CLI:
list clusters, filter them, inspect one cluster in detail, and render readable history without
opening the debugger.

## Implementation Decisions

- Keep CLI semantics parallel to the existing query/history surfaces rather than inventing a
  separate mode family.
- Expose both machine-readable JSON and readable terminal summaries.
- Keep cluster summaries evidence-linked so CLI output can still hand users back into the saved
  artifact routes.

## Existing Code Insights

- [cli.py](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/cli.py) already had
  deterministic JSON/text rendering patterns for query, history, and governance.
- [query_bridge.py](/Users/padraigobrien/model-failure-lab/scripts/query_bridge.py) already
  served as the frontend-facing seam for query-backed analysis modes.
