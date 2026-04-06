# Phase 85: Comparison Signal Contract And Artifact Persistence - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a deterministic comparison signal block at artifact-build time and persist it through the
existing comparison report contract. This phase only covers signal computation and persistence.
CLI surfaces, query/index listing behavior, and debugger severity affordances stay in later phases.

</domain>

<decisions>
## Implementation Decisions

### Signal Source Of Truth
- Compute signals directly from the deterministic comparison artifact inputs already produced by
  `build_comparison_report`: failure-rate deltas over shared cases plus the saved case-delta rows.
- Persist the same signal payload in both the compact report summary and the comparison detail
  payload so later surfaces do not need to recompute or reinterpret it.

### Verdict Contract
- Keep the existing comparison `status.overall` string for backward compatibility.
- Add an explicit signal verdict with the stricter closed set `regression`, `improvement`,
  `neutral`, or `incompatible`.

### Driver Contract
- Top drivers are failure-type deltas ordered deterministically by absolute magnitude, then failure
  type label.
- Persist signed deltas and supporting case ids so later CLI/debugger layers can explain the score
  without ad hoc regrouping.

</decisions>

<code_context>
## Existing Code Insights

- [`src/model_failure_lab/reporting/compare.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/reporting/compare.py)
  already owns the directional baseline-to-candidate report builder and has the exact failure-rate
  delta inputs needed for deterministic signal scoring.
- [`src/model_failure_lab/schemas/contracts.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/schemas/contracts.py)
  keeps the compact report schema intentionally open through JSON mappings for `comparison`,
  `metrics`, and `status`, so nested signal payloads can land without a separate report version.
- [`src/model_failure_lab/index/builder.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/index/builder.py)
  mirrors comparison artifact fields into the SQLite query index and will need the new signal
  fields immediately after persistence lands.

</code_context>

<deferred>
## Deferred Ideas

- Thresholded alert formatting belongs to Phase 86.
- `/analysis` recent-regression surfacing belongs to Phase 87.

</deferred>
