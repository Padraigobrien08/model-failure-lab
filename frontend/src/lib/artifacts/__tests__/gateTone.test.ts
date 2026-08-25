import { describe, expect, it } from "vitest";

import type { GateDecisionRow, GateResponse } from "@/lib/artifacts/extended";
import { gateRemedy, gateRowTone, gateSummary } from "@/lib/artifacts/gateTone";

const SOURCE = {
  label: "Configured artifact store",
  path: "/w",
  runsPath: "/w/runs",
  reportsPath: "/w/reports",
};

function row(overrides: Partial<GateDecisionRow> = {}): GateDecisionRow {
  return {
    comparisonId: "cmp_1",
    verdict: "neutral",
    action: "ignore",
    severity: 0,
    policyRule: "rule",
    blocked: false,
    waived: false,
    waiver: null,
    blockReason: null,
    ...overrides,
  };
}

function gate(rows: GateDecisionRow[]): GateResponse {
  return {
    source: SOURCE,
    blocked: rows.some((r) => r.blocked),
    policy: {
      minimumSeverity: 0.05,
      topN: 10,
      failureType: null,
      familyId: null,
      familyCaseCap: 200,
      maxDuplicateRatio: 0.6,
      recurrenceWindow: 5,
      recurrenceThreshold: 2,
      strategy: "top_regressions",
    },
    policySource: "default",
    waiverSource: null,
    rows,
  };
}

describe("gateRowTone", () => {
  it("is good when the row does not block", () => {
    expect(gateRowTone(row({ blocked: false, verdict: "regression" }))).toBe("good");
  });

  it("is bad only when a blocking row's own verdict is a regression", () => {
    expect(gateRowTone(row({ blocked: true, verdict: "regression" }))).toBe("bad");
  });

  it.each(["incompatible", "neutral", "improvement", "unknown"])(
    "is warn for a fail-closed block with verdict %s",
    (verdict) => {
      expect(gateRowTone(row({ blocked: true, verdict }))).toBe("warn");
    },
  );
});

describe("gateSummary", () => {
  it("reports no label at all when nothing has been evaluated", () => {
    const summary = gateSummary(gate([]));
    expect(summary.label).toBeNull();
    expect(summary.blockingRows).toEqual([]);
  });

  it("passes green when no row blocks", () => {
    const summary = gateSummary(gate([row(), row({ comparisonId: "cmp_2" })]));
    expect(summary).toMatchObject({ label: "PASS", tone: "good", hasRegression: false });
  });

  it("fails amber when every blocking reason is fail-closed", () => {
    const summary = gateSummary(
      gate([row({ blocked: true, verdict: "incompatible", blockReason: "runs are not comparable" })]),
    );
    expect(summary).toMatchObject({ label: "FAIL", tone: "warn", hasRegression: false });
    expect(summary.blockReasons).toEqual(["runs are not comparable"]);
  });

  it("fails red as soon as one blocking row is a regression", () => {
    const summary = gateSummary(
      gate([
        row({ blocked: true, verdict: "incompatible", blockReason: "runs are not comparable" }),
        row({
          comparisonId: "cmp_2",
          blocked: true,
          verdict: "regression",
          blockReason: "signal verdict: regression",
        }),
      ]),
    );
    expect(summary).toMatchObject({ label: "FAIL", tone: "bad", hasRegression: true });
    expect(summary.blockReasons).toEqual([
      "runs are not comparable",
      "signal verdict: regression",
    ]);
  });

  it("ignores a waived regression when choosing the tone", () => {
    // A waived row is not blocked, so it cannot make the gate red -- the gate is only as
    // red as the reasons that are actually stopping CI.
    const summary = gateSummary(
      gate([
        row({ blocked: false, waived: true, verdict: "regression" }),
        row({ comparisonId: "cmp_2", blocked: true, verdict: "incompatible" }),
      ]),
    );
    expect(summary.tone).toBe("warn");
    expect(summary.hasRegression).toBe(false);
  });

  it("dedupes identical block reasons", () => {
    const summary = gateSummary(
      gate([
        row({ blocked: true, verdict: "incompatible", blockReason: "runs are not comparable" }),
        row({
          comparisonId: "cmp_2",
          blocked: true,
          verdict: "incompatible",
          blockReason: "runs are not comparable",
        }),
      ]),
    );
    expect(summary.blockReasons).toEqual(["runs are not comparable"]);
  });
});

describe("gateRemedy", () => {
  it("names the waiver path the engine discovers, in both branches", () => {
    for (const hasRegression of [true, false]) {
      expect(gateRemedy(hasRegression)).toContain("governance/waivers.yml");
    }
  });
});
