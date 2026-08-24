import { describe, expect, it } from "vitest";

import { validateComparisonInventory } from "@/lib/artifacts/load";
import { verdictTone } from "@/app/routes/ComparisonsPage";

const SOURCE = {
  label: "workspace",
  path: "/workspace",
  runsPath: "runs/",
  reportsPath: "reports/",
};

function inventoryRow(overrides: Record<string, unknown> = {}) {
  return {
    report_id: "compare_a_to_b_0001",
    baseline_run_id: "run-a",
    candidate_run_id: "run-b",
    dataset: "reasoning-failures-v1",
    created_at: "2026-08-24T00:00:00Z",
    status: "completed",
    compatible: true,
    signal_verdict: "regression",
    regression_score: 0.1,
    improvement_score: 0,
    net_score: -0.1,
    severity: 0.1,
    top_drivers: [],
    ...overrides,
  };
}

describe("comparison signal valves fail safe, not open", () => {
  it("maps a missing signal verdict to 'unknown', never a healthy 'neutral'", () => {
    const result = validateComparisonInventory({
      source: SOURCE,
      comparisons: [inventoryRow({ signal_verdict: null })],
    });

    expect(result.comparisons[0].signalVerdict).toBe("unknown");
    expect(result.comparisons[0].signalVerdict).not.toBe("neutral");
  });

  it("renders an 'unknown' verdict in the neutral tone (never green/'good')", () => {
    expect(verdictTone("unknown")).toBe("neutral");
  });

  it("fails closed on a corrupt (non-array) top_drivers block instead of dropping it", () => {
    expect(() =>
      validateComparisonInventory({
        source: SOURCE,
        comparisons: [inventoryRow({ top_drivers: "corrupt" })],
      }),
    ).toThrow(/must be an array/);
  });

  it("still tolerates an absent top_drivers list", () => {
    const result = validateComparisonInventory({
      source: SOURCE,
      comparisons: [inventoryRow({ top_drivers: null })],
    });

    expect(result.comparisons[0].topDrivers).toEqual([]);
  });
});
