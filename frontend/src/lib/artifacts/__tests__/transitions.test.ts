/**
 * The console's transition sets must be the engine's.
 *
 * `tests/fixtures/contract/transitions.json` is written from
 * `reporting/signals.py:REGRESSION_TRANSITION_TYPES` and `reporting/compare.py` by
 * `tests/unit/test_transition_vocabulary_contract.py`. This asserts the TypeScript copy
 * agrees, so the divergence that painted `error_stage_changed` red under a NEUTRAL banner
 * and a green PASS cannot come back.
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import {
  CHURN_TRANSITIONS,
  IMPROVEMENT_TRANSITIONS,
  REGRESSION_TRANSITIONS,
  TRANSITION_ORDER,
  isRegressionTransition,
  transitionTone,
} from "@/lib/artifacts/transitions";

const CONTRACT = JSON.parse(
  readFileSync(
    path.resolve(
      path.dirname(fileURLToPath(import.meta.url)),
      "../../../../../tests/fixtures/contract/transitions.json",
    ),
    "utf-8",
  ),
) as {
  all: string[];
  order: string[];
  regression: string[];
  improvement: string[];
  churn: string[];
};

const sorted = (values: ReadonlySet<string>) => [...values].sort();

describe("transition vocabulary contract", () => {
  it("classifies regressions exactly as the engine does", () => {
    expect(sorted(REGRESSION_TRANSITIONS)).toEqual(CONTRACT.regression);
  });

  it("classifies improvements exactly as the engine does", () => {
    expect(sorted(IMPROVEMENT_TRANSITIONS)).toEqual(CONTRACT.improvement);
  });

  it("classifies churn exactly as the engine does", () => {
    expect(sorted(CHURN_TRANSITIONS)).toEqual(CONTRACT.churn);
  });

  it("covers every transition the engine can emit", () => {
    const classified = [
      ...REGRESSION_TRANSITIONS,
      ...IMPROVEMENT_TRANSITIONS,
      ...CHURN_TRANSITIONS,
    ].sort();
    expect(classified).toEqual(CONTRACT.all);
    expect([...TRANSITION_ORDER].sort()).toEqual(CONTRACT.all);
  });

  it("never tints a non-regression red", () => {
    // The rule DESIGN.md states, asserted directly rather than inferred from the sets.
    for (const transition of CONTRACT.all) {
      const isRegression = CONTRACT.regression.includes(transition);
      expect(transitionTone(transition) === "bad").toBe(isRegression);
      expect(isRegressionTransition(transition)).toBe(isRegression);
    }
  });

  it("renders a changed-but-not-worse transition neutral", () => {
    expect(transitionTone("error_stage_changed")).toBe("neutral");
    expect(transitionTone("failure_type_swap")).toBe("neutral");
  });
});
