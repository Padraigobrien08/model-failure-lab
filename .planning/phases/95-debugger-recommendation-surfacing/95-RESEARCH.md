# 95 Research

## Goal

Expose governance recommendations in the debugger without creating a second frontend-only policy
system or a new route family.

## Findings

1. The current signal surfaces already have the right insertion points.
   - `/analysis` signal cards rank comparisons.
   - comparison detail already has a top-of-page enforcement panel.

2. The current automation panel is structurally close to the desired end state.
   - it already shows generation/evolution controls
   - it already loads version history
   - it already links back to source comparison evidence

3. Bridge-side enrichment is the right path.
   - recommendation output is deterministic backend state
   - duplicating the policy logic in React would violate the governance contract

## Chosen Approach

- Enrich signal query rows and comparison detail payloads with governance recommendation data.
- Add frontend types/loaders for that payload.
- Upgrade the existing signal cards and automation panel so users can see action, rationale, and
  family context before drilling deeper.
