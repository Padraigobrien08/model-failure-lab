# Phase 124: Workflow Verification And Stability - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Verify the full `triage -> plan -> execute -> rerun/compare -> attest outcome -> updated context`
loop and close the milestone on stable backend and frontend proof.

</domain>

<decisions>
## Implementation Decisions

### Verification Scope
- Reuse the governance, history, and CLI backend suite plus the comparison, analysis, and
  comparison-inventory frontend routes because those surfaces now carry the full `v5.3` contract.

### Stability Standard
- Require both automated tests and a production build so payload-contract changes are validated
  across Python, the query bridge, TypeScript loaders, and rendered routes.

</decisions>

<code_context>
## Existing Code Insights

- [`test_regression_governance.py`](/Users/padraigobrien/model-failure-lab/tests/unit/test_regression_governance.py),
  [`test_history_tracking.py`](/Users/padraigobrien/model-failure-lab/tests/unit/test_history_tracking.py),
  and
  [`test_cli_governance.py`](/Users/padraigobrien/model-failure-lab/tests/unit/test_cli_governance.py)
  now jointly cover governance policy, history, execution, and attestation behavior.
- [`comparisons.test.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/__tests__/comparisons.test.tsx),
  [`comparisonDetail.test.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/__tests__/comparisonDetail.test.tsx),
  and
  [`analysis.test.tsx`](/Users/padraigobrien/model-failure-lab/frontend/src/app/__tests__/analysis.test.tsx)
  cover the debugger routes that expose the new policy-feedback state.

</code_context>

<specifics>
## Specific Ideas

- Verify the backend milestone slice with one command covering governance, history, and CLI
  workflows.
- Verify the frontend route slice with comparisons, comparison detail, and analysis together.
- Require the production build before archiving the milestone.

</specifics>
