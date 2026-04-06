# Phase 101: Cluster Contract And Stable Identity - Context

**Gathered:** 2026-04-04  
**Status:** Completed

## Phase Boundary

Define deterministic recurring cluster identity over saved run failures and comparison deltas,
then persist that identity inside the derived local query index so later CLI, history, governance,
and debugger surfaces can reuse one contract.

## Implementation Decisions

- Keep cluster identity fully local and artifact-derived.
- Split cluster scope into two explicit kinds: `run_case` and `comparison_delta`.
- Build cluster ids from stable prompt normalization plus dataset scope, failure or transition
  semantics, tag signature, and expectation context.
- Keep recurring-ness deterministic by counting distinct artifact scopes instead of using any
  learned similarity model.

## Existing Code Insights

- [builder.py](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/index/builder.py)
  already owned the derived SQLite index contract and schema versioning.
- [history.py](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/history.py)
  already computed deterministic temporal context and was the right place to thread recurring
  cluster payloads later.
- [insight_fixture.py](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/testing/insight_fixture.py)
  already materialized repeatable cross-run/cross-comparison patterns that could prove cluster
  stability.

## Deferred

- Human-readable cluster summaries and CLI inspection belong to Phase 102.
- Debugger surfacing belongs to Phase 103.
- Governance rationale and full workflow verification belong to Phase 104.
