# 95 Validation

## Must Pass

1. `/analysis?mode=signals` shows recommendation action and rationale on signal cards.
2. Comparison detail shows recommendation status and matched-family context without requiring a new
   route.
3. Recommendation surfaces expose links back to relevant source comparison evidence or family
   provenance.
4. React loaders normalize governance payloads once and do not recompute policy client-side.
5. Existing signal-mode and comparison-detail tests still pass with the new recommendation payloads.

## Automated Proof

- frontend route tests covering analysis signals and comparison detail
- build verification after bridge/type changes
