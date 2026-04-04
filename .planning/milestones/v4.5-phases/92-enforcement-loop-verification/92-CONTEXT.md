# Phase 92: Enforcement Loop Verification - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Close `v4.5` by proving the full enforcement loop from comparison signal to generated/versioned
dataset to rerun and compare. This phase owns workflow proof, smoke stability, and regression
hardening discovered during final verification.

</domain>

<decisions>
## Implementation Decisions

### Proof Standard
- The loop must be proven with automated tests over local artifacts, not just screenshots or CLI
  examples.
- Verification needs to cover Python workflow correctness, frontend route regressions, production
  build health, and at least one real-artifact smoke run.

### Runtime Hardening
- Treat smoke failures as product bugs, not verification noise.
- Fix import and bridge issues inside the milestone so the shipped contract is stable from CLI to
  debugger.

</decisions>

<code_context>
## Existing Code Insights

- [`test_harvest_replay_loop.py`](/Users/padraigobrien/model-failure-lab/tests/unit/test_harvest_replay_loop.py)
  already proves the earlier harvested-dataset replay loop and is the right base for the evolved
  enforcement story.
- [`smoke-real-artifacts.mjs`](/Users/padraigobrien/model-failure-lab/frontend/scripts/smoke-real-artifacts.mjs)
  already validates the debugger over a temporary real-artifact workspace.

</code_context>
