# Phase 118: CLI Plan Execution, Checkpoints, And Rollback Receipts - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Expose the saved-plan execution contract through the CLI so operators can preflight, execute, list,
and inspect plan receipts without leaving the existing dataset command family. This phase covers
checkpoint progression, rollback guidance, and prepared rerun/compare follow-up.

</domain>

<decisions>
## Implementation Decisions

### CLI Shape
- Extend the existing `dataset` command family with `plan-preflight`, `plan-execute`,
  `executions`, and `execution-show` instead of creating a separate command tree.
- Keep `plan-promote` intact for single-family explicit promotion while adding richer saved-plan
  execution for checkpointed flows.

### Execution Modes
- `stepwise` executes one ready action by default so repeated invocations can advance one explicit
  checkpoint at a time.
- `batch` executes all ready actions unless operators bound the run with `--max-actions`.

### Outcome Guidance
- Persist rollback guidance and prepared rerun/compare next steps inside each receipt instead of
  hiding that reasoning in terminal-only text.

</decisions>

<code_context>
## Existing Code Insights

- [`cli.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/cli.py)
  already centralizes dataset lifecycle and saved-plan surfaces under one parser tree.
- Existing portfolio plan rendering helpers provide the same table and JSON conventions needed for
  the new execution surfaces.
- The governance test fixture already exercises saved-plan creation and lifecycle mutation, so the
  new commands can be verified without inventing a new fixture root.

</code_context>
