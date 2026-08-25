/**
 * Case-transition vocabulary, mirrored from the engine.
 *
 * DESIGN.md: "Red (`bad`) means regression. Only regression." The engine decides what a
 * regression is, in `reporting/signals.py`:
 *
 *     REGRESSION_TRANSITION_TYPES = frozenset({"no_failure_to_failure", "new_error"})
 *
 * with `error_stage_changed` deliberately excluded -- a case that was already erroring and
 * now errors at a different stage is not a net-new failure, so it does not move the verdict.
 * The console used to include it anyway, which put a red regression-tinted group directly
 * beneath a NEUTRAL banner and a green PASS on the same screen: two definitions of
 * "regression" for one artifact.
 *
 * These sets are pinned to the engine's by `tests/fixtures/contract/transitions.json`,
 * written by `tests/unit/test_transition_vocabulary_contract.py` and read by
 * `__tests__/transitions.test.ts`. Changing either side alone fails one of them.
 */

/** Net-new failures. The engine's `REGRESSION_TRANSITION_TYPES`. */
export const REGRESSION_TRANSITIONS: ReadonlySet<string> = new Set([
  "no_failure_to_failure",
  "new_error",
]);

/** Cases the candidate fixed. */
export const IMPROVEMENT_TRANSITIONS: ReadonlySet<string> = new Set([
  "failure_to_no_failure",
  "error_cleared",
]);

/**
 * Changed but neither better nor worse: still failing (different type), or still erroring
 * (different stage). These render neutral -- never red, never green.
 */
export const CHURN_TRANSITIONS: ReadonlySet<string> = new Set([
  "failure_type_swap",
  "error_stage_changed",
]);

/** Display order: what got worse first, then churn, then what got better. */
export const TRANSITION_ORDER: readonly string[] = [
  "no_failure_to_failure",
  "new_error",
  "failure_type_swap",
  "error_stage_changed",
  "error_cleared",
  "failure_to_no_failure",
];

export type TransitionTone = "bad" | "good" | "neutral";

export function transitionTone(transitionType: string): TransitionTone {
  if (REGRESSION_TRANSITIONS.has(transitionType)) return "bad";
  if (IMPROVEMENT_TRANSITIONS.has(transitionType)) return "good";
  return "neutral";
}

/**
 * True for a transition the candidate made worse. Use this for "regressions only" filters
 * and for red tinting -- not for "did anything change", which is any transition at all.
 */
export function isRegressionTransition(transitionType: string): boolean {
  return REGRESSION_TRANSITIONS.has(transitionType);
}
