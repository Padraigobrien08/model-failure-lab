# 94 Research

## Goal

Turn the Phase 93 governance contract into a usable CLI workflow without adding a second decision
path or hiding writes behind an ambiguous command.

## Findings

1. The existing CLI shape already gives a natural place for governance flows.
   - `regressions` is the raw comparison-signal surface.
   - `dataset evolve` already materializes immutable family versions.

2. A separate `create family` write path is unnecessary.
   - `evolve_dataset_family(...)` already creates `v1` when no family exists.
   - Governance apply can use that single write surface for both recommended actions.

3. Family health needs to be explicit before UI surfacing.
   - Users need a read-only way to inspect family size, latest version, source dataset, latest
     driver, and why a policy would skip or cap that family.

## Chosen Approach

- Add backend helpers for:
  - listing family health
  - reviewing recommendations over recent comparisons
  - applying actionable recommendations in deterministic order
- Add CLI surfaces for recommend/review/apply/families on top of those helpers.
