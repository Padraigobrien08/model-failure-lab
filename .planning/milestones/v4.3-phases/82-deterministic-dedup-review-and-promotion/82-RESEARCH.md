# Phase 82 Research

- The draft packs already carry enough prompt hashing metadata to keep duplicate grouping
  deterministic without rescanning the original artifact root.
- Promotion should write normal dataset JSON under the active artifact root so the existing
  `failure-lab run --dataset <id>` path keeps working unchanged.
- The least disruptive way to surface promoted packs is extending `datasets list` with a local
  section rather than replacing the bundled catalog.
