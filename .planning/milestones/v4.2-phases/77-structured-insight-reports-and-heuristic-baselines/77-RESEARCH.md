# Phase 77 Research

- The existing query layer already provides stable case rows, delta rows, aggregate counts, and
  drillthrough identifiers. Phase 77 should consume that contract instead of touching artifact JSON
  directly.
- Prior reporting code already solves deterministic ranking over failure types, verdicts, and
  notable cases. The insight layer should reuse those heuristics where possible so summaries remain
  reproducible and easy to test.
- The key new requirement is not "better prose"; it is a structured report shape that later phases
  can reuse for CLI JSON, human-readable rendering, LLM-grounded outputs, and debugger panels.
- The likely failure mode is overfitting the report contract to one query mode. The schema must
  tolerate case result sets, delta result sets, and aggregate result sets without losing evidence
  references.

