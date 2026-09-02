/**
 * One gate decision, rendered the same way on every screen.
 *
 * `governance/gates.py:evaluate_gate_conditions` is the single place the engine decides
 * PASS/FAIL, and it blocks on four conditions: a regression verdict, runs that are not
 * comparable, a drop in execution success or classification coverage, and a candidate that
 * deleted the baseline's failing cases. Only the first is a regression.
 *
 * DESIGN.md: "Red (`bad`) means regression. Only regression." So the *fact* of a block and
 * the *tone* of a block are two different questions, and every surface has to answer both
 * the same way. They did not:
 *
 *   - `ConsoleShell` painted the nav chip `bad` on any block, so a fail-closed
 *     "runs are not comparable" rendered a red FAIL badge in the rail while the banner
 *     100px to its right rendered the same state in amber.
 *   - `ComparisonDetailPage` short-circuited an `incompatible` verdict to "not evaluated"
 *     before it ever looked at the gate row -- so a comparison that was the *sole reason*
 *     the gate failed reported, on its own page, that the gate had not been evaluated on
 *     it. That is the console-green / CI-red split the unified gate contract exists to
 *     prevent, reintroduced one layer up.
 *
 * Everything that renders a gate answer now derives it here.
 */

import type { GateDecisionRow, GateResponse } from "./extended";

/** `good` = clear, `bad` = blocked by a regression, `warn` = blocked fail-closed. */
export type GateTone = "good" | "warn" | "bad";

export type GateSummary = {
  /** `null` when no comparison has been evaluated at all. */
  label: "PASS" | "FAIL" | null;
  tone: GateTone;
  /** Rows actually responsible for the block, in payload order. */
  blockingRows: GateDecisionRow[];
  /** True when a regression verdict is among the reasons -- the only red-worthy case. */
  hasRegression: boolean;
  /** The engine's own block reasons, deduped, verbatim. */
  blockReasons: string[];
};

/**
 * Tone for one decision row. A blocked row is red only when its own verdict is a
 * regression; every other block is a degraded state the candidate did not necessarily
 * cause.
 */
export function gateRowTone(row: GateDecisionRow): GateTone {
  if (!row.blocked) {
    return "good";
  }
  return row.verdict === "regression" ? "bad" : "warn";
}

/** The whole-gate answer: what the rail chip, the gate banner and CI all report. */
export function gateSummary(gate: GateResponse): GateSummary {
  if (gate.rows.length === 0) {
    return { label: null, tone: "good", blockingRows: [], hasRegression: false, blockReasons: [] };
  }
  const blockingRows = gate.rows.filter((row) => row.blocked);
  const hasRegression = blockingRows.some((row) => row.verdict === "regression");
  const blockReasons = Array.from(
    new Set(
      blockingRows
        .map((row) => row.blockReason)
        .filter((reason): reason is string => Boolean(reason)),
    ),
  );
  return {
    label: gate.blocked ? "FAIL" : "PASS",
    tone: gate.blocked ? (hasRegression ? "bad" : "warn") : "good",
    blockingRows,
    hasRegression,
    blockReasons,
  };
}

/**
 * Remedy line for a blocked gate.
 *
 * Both halves are commands a reader can paste. The screen used to print
 * `--waivers waivers.yml`, which resolves to nothing -- and at the time there was no
 * command that wrote a waiver at all, so the console's only offered way out was to
 * hand-author YAML from a description in the docs.
 */
export function gateRemedy(hasRegression: boolean, comparisonId?: string): string {
  const target = comparisonId ?? "<comparison-id>";
  const waive = `failure-lab regressions waive ${target} --reason "..."`;
  return hasRegression
    ? `harvest it: failure-lab regressions apply · or waive it: ${waive}`
    : `rerun on comparable artifacts · or waive it: ${waive}`;
}
