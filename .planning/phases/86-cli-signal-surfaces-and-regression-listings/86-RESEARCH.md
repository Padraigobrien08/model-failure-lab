# Phase 86 Research

- The compare command already rebuilds comparison artifacts on demand, so signal score and summary
  output can read directly from the newly persisted signal block without adding another persistence
  step.
- The query index now stores comparison-level signal rows and ranked signal drivers, which makes a
  severity-ordered listing command straightforward and deterministic.
- Neutral comparisons can carry meaningful severity but still be poor alert candidates, so the
  alert surface should remain directional-only.
