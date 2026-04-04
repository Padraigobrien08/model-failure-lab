# Phase 85 Research

- The existing comparison builder already computes deterministic failure-rate deltas per failure
  type on shared cases only, which is the right score base for this milestone.
- The current persisted comparison payload has no first-class signal block, so later layers would
  otherwise be forced to recompute severity from raw metrics or case deltas.
- The SQLite index currently mirrors comparison summary fields and case deltas only. Persisting the
  signal now lets the index stay a mirror of artifact truth rather than a second scoring engine.
