# Phase 83 Research

- The existing Vite middleware + Python bridge pattern is already used for overview, inventory,
  detail, and query routes, so adding one POST-based harvest action is lower risk than extending
  the React app with direct filesystem assumptions.
- `/analysis` already computes a stable filter payload from URL state, making export a natural
  extension of the current query contract.
- Comparison detail already keeps one active transition case in focus, which is the right place to
  anchor a single export action without cluttering the grouped cards.
