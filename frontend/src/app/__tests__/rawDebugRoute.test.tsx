import { describe, expect, it } from "vitest";

import { buildRawDebugRouteModel, getRawDebugTabSlugs } from "@/lib/rawDebugRoute";

describe("rawDebugRoute", () => {
  it("defaults to raw JSON and keeps related entities outside the tab payload", () => {
    const route = buildRawDebugRouteModel("run_distilbert_reweighting_seed_13", "all");

    expect(route.state).toBe("ready");
    if (route.state !== "ready") {
      return;
    }

    expect(getRawDebugTabSlugs()).toEqual(["raw JSON", "manifest entity", "metadata"]);
    expect(route.defaultTab).toBe("raw_json");
    expect(route.tabs.map((tab) => tab.label)).toEqual(["Raw JSON", "Manifest entity", "Metadata"]);
    expect(route.relatedEntities[0]?.relation).toBe("Parent method");
  });

  it("distinguishes scope-hidden exploratory entities from missing ones", () => {
    const hiddenRoute = buildRawDebugRouteModel("method_group_dro_robustness", "official");
    const missingRoute = buildRawDebugRouteModel("entity_does_not_exist", "all");

    expect(hiddenRoute.state).toBe("scope-hidden");
    if (hiddenRoute.state === "scope-hidden") {
      expect(hiddenRoute.recoveryPath).toBe("/debug/raw/method_group_dro_robustness?scope=all");
    }

    expect(missingRoute.state).toBe("missing");
  });
});
