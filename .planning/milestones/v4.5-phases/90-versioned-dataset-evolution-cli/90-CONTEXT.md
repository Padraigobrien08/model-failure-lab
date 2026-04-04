# Phase 90: Versioned Dataset Evolution CLI - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Add immutable dataset-family history and deterministic evolution commands on top of the draft
signal-pack layer. This phase owns dataset version records, lineage inspection, and CLI evolution
surfaces. It does not yet expose those actions in the debugger.

</domain>

<decisions>
## Implementation Decisions

### Immutable Family Model
- Treat dataset families as append-only version histories: `family_id -> v1, v2, ...`.
- Keep every version as a standalone dataset artifact so reruns remain reproducible and older
  versions are never rewritten.

### Deterministic Evolution Rules
- Evolution must compose new regression cases with the latest family version under stable duplicate
  collapse rules.
- Duplicate detection should use normalized prompt hashing plus stable case identity derivation so
  repeated evolution over the same comparison does not inflate the family.

### CLI Posture
- Add `failure-lab dataset versions` for family lineage inspection.
- Add `failure-lab dataset evolve ... --from-comparison ...` for immutable version creation.
- Keep the existing dataset discovery contract intact so versioned packs look like normal datasets to
  the rest of the system.

</decisions>

<code_context>
## Existing Code Insights

- [`src/model_failure_lab/datasets/load.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/datasets/load.py)
  already resolves canonical dataset files from the local artifact workspace.
- [`src/model_failure_lab/storage/__init__.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/storage/__init__.py)
  already exposes deterministic JSON writes and dataset-path helpers.
- The draft regression-pack output from Phase 89 already contains enough source signal metadata to
  seed version lineage without inventing a second provenance contract.

</code_context>
