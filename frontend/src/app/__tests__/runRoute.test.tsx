import { describe, expect, it } from "vitest";

import { buildRunRouteModel, buildRunRoutePath } from "@/lib/runRoute";

describe("runRoute", () => {
  it("builds a compact run model with scoped breadcrumb context", () => {
    const runRoute = buildRunRouteModel("distilbert_reweighting_seed_13", "all", {
      laneId: "calibration",
      methodId: "reweighting",
    });

    expect(runRoute.question).toBe("What happened in this run?");
    expect(runRoute.runId).toBe("distilbert_reweighting_seed_13");
    expect(runRoute.laneLabel).toBe("Calibration");
    expect(runRoute.methodLabel).toBe("Reweighting");
    expect(runRoute.metricStrip).toHaveLength(2);
    expect(runRoute.interpretationNote).toContain("Calibration improves");
    expect(runRoute.breadcrumbs.methodPath).toBe("/lane/calibration/reweighting?scope=all");
    expect(runRoute.inspector.rawPath).toBe("/debug/raw/run_distilbert_reweighting_seed_13?scope=all");
  });

  it("builds scope-visible run links that preserve lane and method context", () => {
    expect(
      buildRunRoutePath("distilbert_reweighting_seed_13", "all", {
        laneId: "robustness",
        methodId: "reweighting",
      }),
    ).toBe("/run/distilbert_reweighting_seed_13?scope=all&lane=robustness&method=reweighting");
  });
});
