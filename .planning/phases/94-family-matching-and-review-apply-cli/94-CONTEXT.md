# Phase 94: Family Matching And Review/Apply CLI - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Expose the governance recommendation backend through review/apply CLI flows and add deterministic
family-health inspection. This phase covers recent-comparison review, explicit apply behavior, and
read-only family health. Debugger recommendation surfacing remains in Phase 95.

</domain>

<decisions>
## Implementation Decisions

### CLI Namespace Posture
- Keep governance under the existing `regressions` and `dataset` namespaces rather than adding a
  new top-level command family.
- Add:
  - `failure-lab regressions recommend --comparison ...`
  - `failure-lab regressions review ...`
  - `failure-lab regressions apply ...`
  - `failure-lab dataset families ...`
- Preserve the existing flat `failure-lab regressions` listing as the raw signal surface.

### Review And Apply Posture
- `recommend` stays single-comparison and read-only.
- `review` evaluates recent saved comparisons through the current policy and returns a stable
  action list without writing files.
- `apply` recomputes recommendations in deterministic signal order, then writes dataset actions
  only for actionable `create` or `evolve` recommendations.
- `create` and `evolve` both materialize through the existing immutable family-evolution path so
  the enforcement loop stays on one dataset contract.

### Family Matching And Health
- Phase 94 keeps family choice intentionally exact and inspectable:
  policy override or deterministic suggested family id from the saved comparison signal.
- Family-health inspection explains why that family is actionable, capped, or duplicate-heavy
  through latest version, latest size, source dataset, primary driver, and overlap/cap metrics.
- Richer cross-family ranking is still out of scope for this milestone.

</decisions>

<code_context>
## Existing Code Insights

- [`src/model_failure_lab/governance/policy.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/governance/policy.py)
  now exposes the typed single-comparison recommendation contract and family-health guard inputs.
- [`src/model_failure_lab/cli.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/cli.py)
  already has adjacent `regressions`, `dataset evolve`, and `dataset versions` surfaces, so
  review/apply should extend those namespaces instead of inventing a new CLI topology.
- [`src/model_failure_lab/datasets/evolution.py`](/Users/padraigobrien/model-failure-lab/src/model_failure_lab/datasets/evolution.py)
  already treats “missing family” as `v1` evolution, which gives Phase 94 one apply path for both
  `create` and `evolve`.

</code_context>

<deferred>
## Deferred Ideas

- Debugger recommendation badges and matched-family drillthrough belong to Phase 95.
- Milestone-wide workflow verification belongs to Phase 96.

</deferred>
