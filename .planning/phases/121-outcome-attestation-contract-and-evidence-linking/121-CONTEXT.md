# Phase 121: Outcome Attestation Contract And Evidence Linking - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Define the persisted outcome-attestation contract over saved plan execution receipts without
rewriting the execution artifact model. This phase covers open-follow-up discovery, evidence-link
validation, explicit closure state, and stable storage seams for outcome attestation records.

</domain>

<decisions>
## Implementation Decisions

### Storage Boundary
- Store outcome attestation artifacts under a dedicated governance root instead of mutating saved
  execution receipt files in place.
- Treat execution receipts as immutable source artifacts and synthesize an `open` outcome state
  from them when no attestation record exists yet.

### Evidence Linking Rules
- Validate linked run ids against saved run artifacts and linked comparison ids against saved
  comparison report artifacts before persisting any attestation update.
- Key outcome attestation records to one execution checkpoint so every follow-up maps back to one
  explicit family action and one saved receipt.

### Closure State
- Use explicit outcome states (`open`, `evidence_linked`, `attested`) instead of treating prepared
  follow-up prose as the only source of progress.
- Preserve operator notes and linked evidence on the attestation artifact without mutating family
  policy implicitly.

</decisions>

<code_context>
## Existing Code Insights

- [`execution.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/execution.py)
  already persists receipts, before/after snapshots, and prepared follow-up scope for saved plan
  actions.
- [`layout.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/storage/layout.py)
  already separates governance artifact roots, so outcome attestations can follow the same storage
  pattern as saved plans and executions.
- [`cli.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/cli.py) already exposes
  dataset plan and execution commands, giving outcome follow-up commands a natural home.
- [`query.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/index/query.py) and
  saved report artifacts already provide stable comparison signal lookups for later verdict
  computation.

</code_context>

<specifics>
## Specific Ideas

- Add a dedicated outcome-attestation module with typed attestation records, open-follow-up
  listing, evidence linking, and explicit attestation finalization helpers.
- Expose linked run ids, comparison ids, notes, and closure state through JSON payloads so later
  CLI and debugger surfaces can reuse one contract.
- Keep verdict computation optional at the contract level so Phase 122 can layer deterministic
  outcome scoring on top of the same attestation artifact.

</specifics>

